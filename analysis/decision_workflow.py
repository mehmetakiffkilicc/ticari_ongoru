"""Unified, auditable signal review and action outcome workflow."""
from __future__ import annotations

import hashlib
import json
from contextlib import closing
from datetime import date, datetime, timedelta
from typing import Any

from analysis import engine
from analysis.commercial_analytics import pricing_analytics, seller_analytics
from analysis.customer_analytics import customer_analytics


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _ensure_schema(con) -> None:
    con.executescript('''
    CREATE TABLE IF NOT EXISTS signal_metadata(
      signal_id TEXT PRIMARY KEY, module TEXT NOT NULL, entity_name TEXT NOT NULL,
      lifecycle TEXT NOT NULL DEFAULT 'new', occurrence_count INTEGER NOT NULL DEFAULT 1,
      disposition TEXT NOT NULL DEFAULT 'pending', review_note TEXT, reviewer TEXT,
      reviewed_at TEXT, previous_score REAL, score_delta REAL NOT NULL DEFAULT 0);
    CREATE INDEX IF NOT EXISTS signal_metadata_module ON signal_metadata(module,lifecycle,disposition);
    CREATE TABLE IF NOT EXISTS signal_occurrences(
      id TEXT PRIMARY KEY, signal_id TEXT NOT NULL, run_key TEXT NOT NULL, observed_at TEXT NOT NULL,
      severity TEXT NOT NULL, score REAL NOT NULL, impact_value REAL NOT NULL, evidence TEXT NOT NULL,
      UNIQUE(signal_id,run_key));
    CREATE INDEX IF NOT EXISTS signal_occurrence_signal ON signal_occurrences(signal_id,observed_at);
    CREATE TABLE IF NOT EXISTS action_closures(
      action_id TEXT PRIMARY KEY, closure_note TEXT, closed_at TEXT, cycle_hours REAL,
      outcome TEXT, realized_impact REAL, updated_at TEXT NOT NULL);
    ''')


def _score(severity: str, evidence: dict[str, Any], confidence: str = 'Orta') -> int:
    base = {'info': 28, 'attention': 50, 'high': 72, 'critical': 90}.get(severity, 50)
    observed, threshold = evidence.get('observed'), evidence.get('threshold', evidence.get('reference'))
    ratio = 0
    try:
        ratio = min(100, abs(float(observed) - float(threshold)) / max(abs(float(threshold)), 1) * 100)
    except (TypeError, ValueError):
        ratio = min(100, abs(float(evidence.get('impact') or 0)) ** .5)
    confidence_value = {'Düşük': 45, 'Orta': 70, 'Yüksek': 92}.get(confidence, 70)
    return round(base * .55 + ratio * .25 + confidence_value * .2)


def _recommend(code: str, title: str) -> str:
    if 'PRICE' in code or 'MARGIN' in code:
        return 'Fiyat, maliyet ve yerine koyma marjını doğrulayarak fiyat aksiyonu belirleyin.'
    if 'RETURN' in code:
        return 'İade hareketlerini müşteri ve ürün bazında inceleyip kök neden aksiyonu oluşturun.'
    if 'SELLER' in code:
        return 'Satıcı portföyünü kanıtla birlikte gözden geçirip sorumlu ve termin atayın.'
    if 'CUSTOMER' in code:
        return 'Müşteri geçmişini inceleyip temas veya geri kazanım aksiyonu planlayın.'
    return f'{title} sinyalinin kanıtını doğrulayıp sorumlu bir aksiyon oluşturun.'


def _attach_source_references(signals: list[dict[str, Any]], analysis_date: str | None = None) -> None:
    """Attach verifiable record pointers without exposing raw rows or inventing IDs."""
    with closing(engine.db()) as con:
        batch = con.execute("SELECT id FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1").fetchone()
        records = [(row['source_line'], json.loads(row['converted'])) for row in con.execute(
            "SELECT source_line,converted FROM records WHERE kind='movement' AND batch_id=?", (batch['id'],)
        )] if batch else []
    by_entity: dict[tuple[str, str], list[tuple[int, dict[str, Any]]]] = {}
    for source_line, row in records:
        if engine.invoice_kind(row) not in ('sale', 'return'):
            continue
        # Historic decisions must never cite a transaction from the future.
        if analysis_date and str(row.get('Fatura Tarihi') or '')[:10] > analysis_date:
            continue
        keys = (
            ('product', str(row.get('Malzeme Kodu') or '').strip()),
            ('customer', str(row.get('Müsteri Kodu') or 'Bilinmiyor').strip() or 'Bilinmiyor'),
            ('seller', str(row.get('Satici') or 'Bilinmiyor').strip() or 'Bilinmiyor'),
        )
        for entity_type, entity_id in keys:
            if entity_id:
                by_entity.setdefault((entity_type, entity_id), []).append((source_line, row))
    for signal in signals:
        candidates = by_entity.get((signal['entityType'], signal['entityId']), [])
        candidates.sort(key=lambda item: (str(item[1].get('Fatura Tarihi') or ''), item[0]), reverse=True)
        refs, seen = [], set()
        for source_line, row in candidates:
            identity = (source_line, str(row.get('Fatura No') or ''))
            if identity in seen:
                continue
            seen.add(identity)
            refs.append({'batchId': batch['id'], 'sourceLine': int(source_line), 'invoice': str(row.get('Fatura No') or '') or None,
              'date': str(row.get('Fatura Tarihi') or '') or None,
              'invoiceType': 'Satış iadesi' if engine.invoice_kind(row) == 'return' else 'Satış',
              'amount': round(abs(engine._float(row.get('Net Satir Tutari'))), 2)})
            if len(refs) == 8:
                break
        evidence = dict(signal.get('evidence') or {})
        evidence['source'] = {'kind': 'records', 'references': refs, 'totalMatchingRows': len(candidates)} if refs else {
          'kind': 'aggregate', 'references': [],
          'reason': 'Bu sinyal toplu metriklerden hesaplandı; güvenle eşleştirilebilen tekil kaynak satırı yok.'}
        signal['evidence'] = evidence


def _collect(analysis_date: str | None) -> tuple[str, list[dict[str, Any]]]:
    product_data = engine.signals({'analysisDate': analysis_date, 'persist': False})
    if product_data.get('status') != 'ready':
        return date.today().isoformat(), []
    chosen = product_data['analysisDate']
    output: list[dict[str, Any]] = []
    for product in product_data['products']:
        for tag in product.get('tags', []):
            if tag.get('score', 0) < 40:
                continue
            output.append({'id': tag['signalId'], 'module': 'products', 'entityType': 'product', 'entityId': product['code'],
              'entityName': product['name'], 'code': tag['code'], 'title': tag['name'], 'severity': tag['severity'],
              'score': tag['score'], 'confidence': tag['confidence'], 'impact': tag['evidence'].get('impact', 0),
              'evidence': tag['evidence'], 'recommendedAction': tag.get('recommendedAction') or _recommend(tag['code'], tag['name'])})

    customers = customer_analytics({'analysisDate': chosen})
    if customers.get('status') == 'ready':
        for customer in customers['customers']:
            for tag in customer.get('tags', []):
                if tag.get('score', 0) < 40:
                    continue
                signal_id = engine.stable_signal_id('customer', customer['code'], tag['code'])
                output.append({'id': signal_id, 'module': 'customers', 'entityType': 'customer', 'entityId': customer['code'],
                  'entityName': customer['name'], 'code': tag['code'], 'title': tag['name'], 'severity': tag['severity'],
                  'score': tag['score'], 'confidence': tag['confidence'], 'impact': tag['evidence'].get('impact', 0),
                  'evidence': tag['evidence'], 'recommendedAction': tag['recommendedAction']})

    analysis_scope = {'analysisDate': chosen, 'start': (date.fromisoformat(chosen)-timedelta(days=89)).isoformat(), 'end': chosen}
    for module, entity_type, dataset in (
        ('pricing', 'product', pricing_analytics(analysis_scope)),
        ('salespeople', 'seller', seller_analytics(analysis_scope)),
    ):
        for signal in dataset.get('signals', []):
            code = signal['code']; entity_id = str(signal.get('entityId') or signal.get('seller') or 'Bilinmiyor')
            entity_name = str(signal.get('entityName') or signal.get('seller') or entity_id)
            evidence = signal.get('evidence') or {}; confidence = 'Yüksek' if evidence.get('observed') is not None else 'Orta'
            score = _score(signal['severity'], evidence, confidence)
            if score < 40:
                continue
            signal_id = engine.stable_signal_id(entity_type, entity_id, code)
            output.append({'id': signal_id, 'module': module, 'entityType': entity_type, 'entityId': entity_id,
              'entityName': entity_name, 'code': code, 'title': signal['title'], 'severity': signal['severity'],
              'score': score, 'confidence': confidence, 'impact': evidence.get('impact') or 0,
              'evidence': evidence, 'recommendedAction': _recommend(code, signal['title'])})
    _attach_source_references(output, chosen)
    return chosen, output


def synchronize(data: dict[str, Any] | None = None) -> dict[str, Any]:
    data = data or {}; chosen, signals = _collect(data.get('analysisDate')); now = _now(); run_key = f'unified:{chosen}'
    active_ids = {signal['id'] for signal in signals}
    with closing(engine.db()) as con:
        _ensure_schema(con)
        for signal in signals:
            old = con.execute('SELECT first_seen,score,status FROM signal_instances WHERE id=?', (signal['id'],)).fetchone()
            metadata = con.execute('SELECT occurrence_count,lifecycle,disposition FROM signal_metadata WHERE signal_id=?', (signal['id'],)).fetchone()
            previous_score = float(old['score']) if old else None
            score_delta = signal['score'] - previous_score if previous_score is not None else 0
            first_seen = old['first_seen'] if old else now
            con.execute('''INSERT OR REPLACE INTO signal_instances
              (id,run_id,entity_type,entity_id,tag_code,title,severity,score,confidence,impact_value,status,first_seen,last_seen,evidence,recommended_action)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (signal['id'], run_key, signal['entityType'], signal['entityId'], signal['code'], signal['title'], signal['severity'], signal['score'], signal['confidence'], signal['impact'], 'active', first_seen, now, json.dumps(signal['evidence'], ensure_ascii=False), signal['recommendedAction']))
            occurrence_id = hashlib.sha256(f"{signal['id']}|{run_key}".encode()).hexdigest()[:32]
            inserted = con.execute('INSERT OR IGNORE INTO signal_occurrences VALUES(?,?,?,?,?,?,?,?)',
              (occurrence_id, signal['id'], run_key, now, signal['severity'], signal['score'], signal['impact'], json.dumps(signal['evidence'], ensure_ascii=False))).rowcount
            count = (metadata['occurrence_count'] if metadata else 0) + (1 if inserted else 0)
            lifecycle = 'recurring' if old and inserted else (metadata['lifecycle'] if metadata else 'new')
            con.execute('''INSERT INTO signal_metadata(signal_id,module,entity_name,lifecycle,occurrence_count,disposition,previous_score,score_delta)
              VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(signal_id) DO UPDATE SET module=excluded.module,entity_name=excluded.entity_name,
              lifecycle=excluded.lifecycle,occurrence_count=excluded.occurrence_count,previous_score=excluded.previous_score,score_delta=excluded.score_delta''',
              (signal['id'], signal['module'], signal['entityName'], lifecycle, count, metadata['disposition'] if metadata else 'pending', previous_score, score_delta))
            if signal['score'] >= 60 and (not metadata or metadata['disposition'] != 'false_positive'):
                alert_id = hashlib.sha256(f"alert|{signal['id']}".encode()).hexdigest()[:32]
                alert = con.execute('SELECT first_seen,status,acknowledged_at FROM alerts WHERE id=?', (alert_id,)).fetchone()
                status = alert['status'] if alert and alert['status'] == 'acknowledged' else 'open'
                con.execute('''INSERT OR REPLACE INTO alerts(id,signal_id,title,severity,status,first_seen,last_seen,acknowledged_at,resolved_at)
                  VALUES(?,?,?,?,?,?,?,?,?)''', (alert_id, signal['id'], f"{signal['entityName']}: {signal['title']}", signal['severity'], status, alert['first_seen'] if alert else now, now, alert['acknowledged_at'] if alert else None, None))
            elif metadata and metadata['disposition'] == 'false_positive':
                con.execute("UPDATE alerts SET status='resolved',resolved_at=? WHERE signal_id=?", (now, signal['id']))
        # Only unified-owned signals are retired here; product engine manages its own runs.
        unified = [row['id'] for row in con.execute("SELECT id FROM signal_instances WHERE run_id LIKE 'unified:%'")]
        retired = [signal_id for signal_id in unified if signal_id not in active_ids]
        for signal_id in retired:
            con.execute("UPDATE signal_instances SET status='inactive',last_seen=? WHERE id=?", (now, signal_id))
            con.execute("UPDATE signal_metadata SET lifecycle='resolved' WHERE signal_id=?", (signal_id,))
            con.execute("UPDATE alerts SET status='resolved',resolved_at=? WHERE signal_id=? AND status!='resolved'", (now, signal_id))
        con.commit()
    return {'status': 'ready', 'analysisDate': chosen, 'signals': len(signals)}


def review_signal(data: dict[str, Any]) -> dict[str, Any]:
    signal_id = str(data.get('signalId') or ''); disposition = str(data.get('disposition') or '')
    if disposition not in ('pending', 'confirmed', 'false_positive'):
        raise ValueError('Geçersiz inceleme sonucu.')
    note = str(data.get('note') or '').strip()[:1200]; reviewer = str(data.get('reviewer') or 'Demo kullanıcı').strip()[:120]
    if disposition == 'false_positive' and len(note) < 5:
        raise ValueError('Yanlış pozitif işaretlerken kısa bir gerekçe yazın.')
    with closing(engine.db()) as con:
        _ensure_schema(con)
        signal = con.execute('SELECT id FROM signal_instances WHERE id=?', (signal_id,)).fetchone()
        if not signal: raise ValueError('Sinyal bulunamadı.')
        con.execute('UPDATE signal_metadata SET disposition=?,review_note=?,reviewer=?,reviewed_at=? WHERE signal_id=?',
                    (disposition, note or None, reviewer, _now(), signal_id))
        if disposition == 'false_positive':
            con.execute("UPDATE alerts SET status='resolved',resolved_at=? WHERE signal_id=?", (_now(), signal_id))
        con.commit()
    return {'signalId': signal_id, 'disposition': disposition}


def update_action(data: dict[str, Any]) -> dict[str, Any]:
    result = engine.action_update(data)
    status = result['status']
    with closing(engine.db()) as con:
        _ensure_schema(con)
        action = con.execute('SELECT created,outcome,realized_impact FROM actions WHERE id=?', (result['id'],)).fetchone()
        if action and status in ('completed', 'rejected'):
            now = _now(); created = datetime.fromisoformat(action['created']); cycle = (datetime.fromisoformat(now) - created).total_seconds() / 3600
            note = str(data.get('note') or '').strip()[:1200]
            con.execute('''INSERT OR REPLACE INTO action_closures(action_id,closure_note,closed_at,cycle_hours,outcome,realized_impact,updated_at)
              VALUES(?,?,?,?,?,?,?)''', (result['id'], note or None, now, round(cycle, 2), action['outcome'], action['realized_impact'], now))
        elif status in ('open', 'in_progress'):
            con.execute('DELETE FROM action_closures WHERE action_id=?', (result['id'],))
        con.commit()
    return result


def unified_center(data: dict[str, Any] | None = None) -> dict[str, Any]:
    data = data or {}; sync = {'analysisDate': data.get('analysisDate') or '2024-12-30'}; today = date.today().isoformat()
    with closing(engine.db()) as con:
        _ensure_schema(con)
        signals = [dict(row) for row in con.execute('''SELECT s.*,m.module,m.entity_name,m.lifecycle,m.occurrence_count,m.disposition,m.review_note,m.reviewer,m.reviewed_at,m.score_delta,
          a.id alert_id,a.status alert_status FROM signal_instances s JOIN signal_metadata m ON m.signal_id=s.id
          LEFT JOIN alerts a ON a.signal_id=s.id ORDER BY CASE s.severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'attention' THEN 2 ELSE 3 END,s.score DESC''')]
        actions = [dict(row) for row in con.execute('''SELECT a.*,c.closure_note,c.closed_at,c.cycle_hours FROM actions a
          LEFT JOIN action_closures c ON c.action_id=a.id ORDER BY CASE a.status WHEN 'open' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END,a.updated DESC''')]
        event_counts = {row[0]: row[1] for row in con.execute('SELECT action_id,COUNT(*) FROM action_events GROUP BY action_id')}
    for signal in signals:
        signal['evidence'] = json.loads(signal['evidence']); signal['eventCount'] = signal['occurrence_count']
    for action in actions:
        action['overdue'] = bool(action['due_date'] and action['due_date'] < today and action['status'] not in ('completed','rejected'))
        action['eventCount'] = event_counts.get(action['id'], 0)
    closed = [a for a in actions if a['status'] in ('completed','rejected')]
    measured = [a for a in closed if a['realized_impact'] is not None]
    converted = [a for a in closed if a['outcome'] == 'converted']
    cycles = [float(a['cycle_hours']) for a in closed if a.get('cycle_hours') is not None]
    reviewed = [s for s in signals if s['disposition'] != 'pending']
    false_positives = [s for s in signals if s['disposition'] == 'false_positive']
    return {'status': 'ready', 'analysisDate': sync['analysisDate'], 'signals': signals, 'actions': actions,
      'summary': {'activeSignals': sum(s['status']=='active' and s['disposition']!='false_positive' for s in signals),
        'unreviewed': sum(s['disposition']=='pending' for s in signals), 'falsePositives': len(false_positives),
        'open': sum(a['status']=='open' and not a['overdue'] for a in actions), 'inProgress': sum(a['status']=='in_progress' and not a['overdue'] for a in actions),
        'completed': sum(a['status']=='completed' for a in actions), 'rejected': sum(a['status']=='rejected' for a in actions),
        'overdue': sum(a['overdue'] for a in actions), 'conversionRate': round(len(converted)/len(closed)*100,1) if closed else None,
        'measuredImpact': round(sum(float(a['realized_impact']) for a in measured),2),
        'averageCycleHours': round(sum(cycles)/len(cycles),1) if cycles else None,
        'falsePositiveRate': round(len(false_positives)/len(reviewed)*100,1) if reviewed else None}}
