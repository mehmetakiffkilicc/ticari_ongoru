"""Versioned decision dossiers. Reads never evaluate signals or advance time.

Documents, immutable proposal revisions, approvals, tasks and audit events are
committed together under a SQLite write lock. Demo and uploaded-data scopes are
explicit and cannot be crossed by reset or mutation operations.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import uuid
from contextlib import closing
from datetime import date, datetime, timedelta

from analysis import engine

DEMO_DATE = '2024-12-30'
DEFAULTS = {
    'stock': ('Stok ve tedarik', 7, 'Kapsama gününü en az 21 güne çıkar; fiziksel stoğu doğrula.'),
    'pricing': ('Fiyat ve marj', 30, 'Marjı en az %22 yap; satış hacmindeki değişimi birlikte değerlendir.'),
    'customer': ('Müşteri geri kazanımı', 14, 'Müşteriyle temas kur; yeniden sipariş ve tutarını kontrol et.'),
    'commercial': ('Ticari inceleme', 14, 'Kanıtı doğrula; bu bulgu için ölçülebilir bir hedef belirle.'),
}
OUTCOMES = {'met', 'partial', 'not_met', 'unmeasurable'}


def now():
    return datetime.now().astimezone().isoformat()


def _schema(con):
    con.execute('''CREATE TABLE IF NOT EXISTS decision_cases (
        id TEXT PRIMARY KEY, scope TEXT NOT NULL CHECK(scope IN ('demo','live')),
        origin TEXT, document TEXT NOT NULL, UNIQUE(scope,origin))''')


def _scope(data):
    scope = data.get('scope', 'live')
    if scope not in ('demo', 'live'):
        raise ValueError('Geçersiz çalışma alanı.')
    return scope


def _text(value, label, minimum=1):
    value = str(value or '').strip()
    if len(value) < minimum or len(value) > 2000:
        raise ValueError(f'{label}: {minimum}–2000 karakter girin.')
    return value


def _date(value):
    try:
        return date.fromisoformat(str(value)).isoformat()
    except (ValueError, TypeError):
        raise ValueError('Geçerli bir tarih girin.') from None


def _event(doc, label, actor='Demo kullanıcı', business_date=None):
    doc['events'].append({'id': uuid.uuid4().hex, 'label': label, 'actor': actor,
                          'at': now(), 'businessDate': business_date or (doc['clockDate'] if doc['scope'] == 'demo' else date.today().isoformat())})


def _base(identifier, scope, category, entity, title, snapshot, origin=None):
    clock = DEMO_DATE if scope == 'demo' else date.today().isoformat()
    proposal = {'description': snapshot.get('recommendedAction') or title,
                'owner': {'stock': 'Satın alma sorumlusu', 'pricing': 'Satış yöneticisi', 'customer': 'Müşteri temsilcisi', 'commercial': 'Ticari yönetici'}[category],
                'dueDate': (date.fromisoformat(clock) + timedelta(days=3)).isoformat(),
                'followupDays': DEFAULTS[category][1], 'successMetric': DEFAULTS[category][2]}
    doc = {'id': identifier, 'scope': scope, 'origin': origin, 'category': category,
           'entity': entity, 'title': title, 'snapshot': snapshot, 'clockDate': clock,
           'state': 'pending', 'version': 1, 'revision': 1, 'proposal': proposal,
           'revisions': [], 'approvals': [], 'tasks': [], 'feedback': None,
           'events': [], 'parentId': None, 'childId': None, 'createdAt': now()}
    doc['revisions'].append({'revision': 1, 'proposal': copy.deepcopy(proposal), 'at': now()})
    _event(doc, 'Kanıt ve içgörü kaydedildi; kullanıcı onayı bekleniyor.')
    return doc


def _insert(con, doc):
    con.execute('INSERT INTO decision_cases VALUES(?,?,?,?)',
                (doc['id'], doc['scope'], doc['origin'], json.dumps(doc, ensure_ascii=False)))


def _save(con, doc):
    doc['version'] += 1
    con.execute('UPDATE decision_cases SET document=? WHERE id=? AND scope=?',
                (json.dumps(doc, ensure_ascii=False), doc['id'], doc['scope']))


def _read(con, identifier, scope):
    row = con.execute('SELECT document FROM decision_cases WHERE id=? AND scope=?', (identifier, scope)).fetchone()
    if not row:
        raise ValueError('Karar dosyası bu çalışma alanında bulunamadı.')
    return json.loads(row[0])


def _view(doc):
    result = copy.deepcopy(doc)
    today = doc['clockDate'] if doc['scope'] == 'demo' else date.today().isoformat()
    result['effectiveDate'] = today
    task = next((t for t in reversed(doc['tasks']) if t['revision'] == doc['revision'] and t['status'] != 'superseded'), None)
    result['task'] = task
    result['overdue'] = bool(task and task['status'] in ('ready', 'in_progress') and task['dueDate'] < today)
    result['followupReady'] = bool(task and task.get('followupDate') and task['followupDate'] <= today)
    return result


def listing(data):
    scope = _scope(data)
    with closing(engine.db()) as con:
        _schema(con)
        docs = [json.loads(r[0]) for r in con.execute('SELECT document FROM decision_cases WHERE scope=? ORDER BY id', (scope,))]
        legacy = [dict(r) for r in con.execute('SELECT id,title,status,owner,due_date,outcome,realized_impact FROM actions ORDER BY created DESC')] if scope == 'live' else []
    docs.sort(key=lambda d: (-d['snapshot'].get('score', 0), d['id']))
    return {'cases': [_view(d) for d in docs], 'legacy': legacy, 'scope': scope, 'demoDate': DEMO_DATE}


def detail(data):
    with closing(engine.db()) as con:
        _schema(con)
        return _view(_read(con, data.get('id'), _scope(data)))


def seed(data):
    if _scope(data) != 'demo':
        raise ValueError('Yalnız demo alanı hazırlanabilir veya sıfırlanabilir.')
    # Entirely fictional examples: no customer, product or metric from source data.
    cases = []
    for category, label, unit, before, target, after in [
        ('stock', 'Örnek Ürün A', 'gün', 5, 20, 24),
        ('pricing', 'Örnek Ürün B', '%', 10, 25, 18),
        ('customer', 'Örnek Müşteri A', 'sipariş', 0, 2, 0),
    ]:
        for index, phase in enumerate(('pending', 'monitoring', 'reviewed')):
            entity = label if index == 0 else f'{label} · Örnek {index + 1}'
            outcome = {'stock': 'met', 'pricing': 'partial', 'customer': 'not_met'}[category]
            cases.append({
                'id': f'demo-{category}-{phase}', 'category': category,
                'entity': entity, 'title': f'{DEFAULTS[category][0]} — kurgusal senaryo',
                'phase': phase,
                'snapshot': {
                    'tags': [{'name': DEFAULTS[category][0], 'rule': f'Hedef: {target} {unit}',
                              'reason': f'Kurgusal başlangıç değeri: {before} {unit}'}],
                    'observed': before, 'threshold': target, 'unit': unit,
                    'score': 80 - index * 5, 'impact': None,
                    'confidence': 'Örnek senaryo; gerçek veriden hesaplanmadı.',
                    'insight': f'{entity} için {before} {unit} başlangıç değeriyle karar akışını deneyin.',
                    'uncertainty': 'Tüm adlar ve ölçümler kurgusaldır; ticari karar için kullanılamaz.',
                    'recommendedAction': DEFAULTS[category][2],
                    'sourceExplanation': 'Yalnız uygulamanın karar akışını göstermek için hazırlanmış örnek.',
                    'signalBasis': [
                        {'metric': 'Başlangıç', 'value': f'{before} {unit}', 'source': 'Kurgusal örnek'},
                        {'metric': 'Hedef', 'value': f'{target} {unit}', 'source': 'Kurgusal örnek'}],
                    'targetCustomers': [] if category == 'customer' else [
                        {'customerCode': 'DEMO-C001', 'customerName': 'Örnek Müşteri A',
                         'city': 'Örnek şehir', 'seller': 'Örnek Temsilci A',
                         'propensityScore': 75, 'tier': 'Örnek', 'expectedOrderQty': 10,
                         'reason': 'Kurgusal müşteri önerisi.', 'type': 'due_reorder'}],
                    'predictiveBasket': [] if category != 'customer' else [
                        {'code': 'DEMO-P001', 'name': 'Örnek Ürün A', 'category': 'Örnek kategori',
                         'probability': 75, 'badge': 'Örnek', 'expectedQty': 10,
                         'expectedPrice': 12, 'expectedValue': 120,
                         'reason': 'Kurgusal sepet önerisi.', 'type': 'regular',
                         'orderCount': 4, 'orderFrequency': 50}],
                },
                'feedback': {'outcome': outcome, 'before': before, 'after': after, 'unit': unit,
                             'note': 'Kurgusal takip sonucu; gerçek işlem yapılmadı.',
                             'evidence': 'Hazır örnek senaryo'} if phase == 'reviewed' else None,
                'monitoring_elapsed': None if phase == 'pending' else (
                    DEFAULTS[category][1] + 2 if phase == 'reviewed' or category == 'stock' else 2),
            })
    with closing(engine.db()) as con:
        _schema(con)
        con.execute('BEGIN IMMEDIATE')
        if data.get('reset'):
            con.execute("DELETE FROM decision_cases WHERE scope='demo'")
        for case in cases:
            if con.execute('SELECT 1 FROM decision_cases WHERE id=?', (case['id'],)).fetchone():
                continue
            snapshot = case['snapshot']
            snapshot['analysisDate'] = DEMO_DATE
            snapshot['period'] = ['2024-10-01', DEMO_DATE]
            snapshot['quality'] = 'Hazır sunum örneği; yüklenmiş veri değildir.'
            snapshot['provenance'] = 'demo'
            snapshot['sources'] = []
            snapshot['filters'] = {'analysisDate': DEMO_DATE}
            
            doc = _base(case['id'], 'demo', case['category'], case['entity'], case['title'], snapshot, case['id'])
            
            if case['monitoring_elapsed'] is not None:
                elapsed = case['monitoring_elapsed']
                applied = date.fromisoformat(DEMO_DATE) - timedelta(days=elapsed)
                doc['snapshot']['analysisDate'] = (applied - timedelta(days=4)).isoformat()
                doc['snapshot']['period'] = [(applied - timedelta(days=93)).isoformat(), doc['snapshot']['analysisDate']]
                doc['snapshot']['filters']['analysisDate'] = doc['snapshot']['analysisDate']
                doc['events'][0]['businessDate'] = doc['snapshot']['analysisDate']
                doc['proposal']['dueDate'] = applied.isoformat()
                doc['revisions'][0]['proposal'] = copy.deepcopy(doc['proposal'])
                doc['approvals'].append({'revision': 1, 'decision': 'approved', 'actor': 'Demo yönetici', 'at': now(), 'businessDate': (applied-timedelta(days=1)).isoformat(), 'note': 'Hazır demo onayı'})
                doc['tasks'].append({'id': f"{case['id']}-task-1", 'revision': 1, 'status': 'applied', 'owner': doc['proposal']['owner'], 'dueDate': applied.isoformat(),
                                     'appliedDate': applied.isoformat(), 'followupDate': (applied+timedelta(days=DEFAULTS[case['category']][1])).isoformat(), 'note': 'Hazır demo uygulama kaydı'})
                _event(doc, 'Öneri onaylandı; görev oluşturuldu.', 'Demo yönetici', (applied-timedelta(days=1)).isoformat())
                _event(doc, 'Aksiyon başlatıldı.', business_date=applied.isoformat())
                _event(doc, 'Aksiyon uygulandı; takip tarihi belirlendi.', business_date=applied.isoformat())
                doc['state'] = 'monitoring'
                
            if case['phase'] == 'reviewed':
                doc['state'] = 'reviewed'
                doc['feedback'] = case['feedback']
                doc['feedback']['at'] = now()
                doc['feedback']['businessDate'] = DEMO_DATE
                doc['feedback']['source'] = 'demo'
                _event(doc, 'Takip değerlendirildi; kullanıcı geri bildirimi kaydedildi.', business_date=DEMO_DATE)
                
            _insert(con, doc)
        con.commit()
    return listing(data)


def evaluate(data):
    if _scope(data) != 'live':
        raise ValueError('Veri değerlendirmesi yalnız yüklenmiş veri alanında çalışır.')
    from analysis.decision_workflow import _collect
    chosen, signals = _collect(data.get('analysisDate'))
    stocks = engine.stock_analysis({'analysisDate': chosen}).get('products', [])
    for p in stocks:
        if p.get('status') != 'Kritik':
            continue
        signals.append({'id': f"stock-{p['code']}", 'module': 'stock', 'entityId': p['code'], 'entityName': p['name'],
                        'title': 'Kritik stok kapsaması', 'code': 'LOW_COVERAGE', 'score': 85, 'confidence': 'Demo stok modeli',
                        'evidence': {'observed': p['coverageDays'], 'threshold': p.get('targetCoverageDays'), 'unit': 'gün'},
                        'recommendedAction': 'Fiziksel stoğu doğrulayın; hedef kapsama için alım ihtiyacını belirleyin.'})
    with closing(engine.db()) as con:
        _schema(con)
        batches = [dict(r) for r in con.execute('SELECT id,name,kind,created FROM batches ORDER BY created DESC')]
        latest = list({kind: next((b for b in batches if b['kind'] == kind), None) for kind in ('stock', 'movement')}.values())
        latest = [b for b in latest if b]
        batch_key = '|'.join(b['id'] for b in latest)
        con.execute('BEGIN IMMEDIATE')
        for s in signals:
            category = ('stock' if s['module'] == 'stock' else 'customer' if s['module'] == 'customers' else
                        'pricing' if s['module'] == 'pricing' or any(word in s['code'] for word in ('MARGIN', 'PRICE', 'COST')) else 'commercial')
            ev = s.get('evidence') or {}
            origin = hashlib.sha256(f"{s['id']}|{chosen}|{batch_key}".encode()).hexdigest()
            if con.execute("SELECT 1 FROM decision_cases WHERE scope='live' AND origin=?", (origin,)).fetchone():
                continue
            from analysis.predictive_engine import predict_customer_next_basket, predict_product_target_customers
            movement_rows = [json.loads(r[0]) for r in con.execute("SELECT converted FROM records WHERE kind='movement' ORDER BY source_line")]
            p_basket = predict_customer_next_basket(s['entityId'], chosen, movement_rows, max_items=4) if category == 'customer' and s.get('entityId') and movement_rows else []
            t_customers = predict_product_target_customers(s['entityId'], chosen, movement_rows, max_results=6) if category in ('stock', 'pricing') and s.get('entityId') and movement_rows else []

            snapshot = {'analysisDate': chosen, 'period': [(date.fromisoformat(chosen)-timedelta(days=89)).isoformat(), chosen],
                        'quality': 'Kabul edilmiş kaynak kayıtları; kanıt kapsamını kontrol edin.',
                        'provenance': 'modeled' if category == 'stock' else 'records', 'sources': latest,
                        'tags': [{'name': s['title'], 'rule': s['code'], 'reason': f"Gözlem: {ev.get('observed', 'Belirtilmedi')}; referans: {ev.get('threshold', ev.get('reference', 'Portföy dağılımı'))}"}],
                        'observed': ev.get('observed'), 'threshold': ev.get('threshold', ev.get('reference')), 'unit': ev.get('unit', ''),
                        'score': s.get('score', 0), 'confidence': s.get('confidence', 'Belirtilmedi'), 'impact': ev.get('impact'),
                        'insight': f"{s['entityName']}: {s['title']}. {s['recommendedAction']}",
                        'uncertainty': 'Nedensellik doğrulanmadı. Stok miktarları tahmini modeldir.' if category == 'stock' else 'Gözlenen ilişki nedensellik veya kesin ticari kazanç göstermez.',
                        'recommendedAction': s['recommendedAction'], 'filters': {'analysisDate': chosen, 'scope': 'Tüm ambarlar ve satıcılar'},
                        'evidence': ev, 'entityId': s['entityId'], 'sourceModule': s['module'],
                        'predictiveBasket': p_basket, 'targetCustomers': t_customers}
            doc = _base(uuid.uuid4().hex, 'live', category, s['entityName'], s['title'], snapshot, origin)
            _insert(con, doc)
        con.commit()
    return listing(data)


def mutate(data):
    scope = _scope(data)
    operation = data.get('operation')
    actor = _text(data.get('actor') or ('Demo kullanıcı' if scope == 'demo' else 'Yerel kullanıcı'), 'Kullanıcı')
    with closing(engine.db()) as con:
        _schema(con)
        con.execute('BEGIN IMMEDIATE')
        doc = _read(con, data.get('id'), scope)
        if data.get('version') != doc['version']:
            raise ValueError('Dosya değişti. Yenileyip güncel sürümle tekrar deneyin.')
        today = doc['clockDate'] if scope == 'demo' else date.today().isoformat()
        task = _view(doc)['task']
        if operation == 'edit':
            if doc['state'] in ('monitoring', 'reviewed'):
                raise ValueError('Uygulanmış karar değiştirilemez; yeni inceleme başlatın.')
            p = data.get('proposal') or {}
            try:
                days = int(p.get('followupDays', 0))
            except (TypeError, ValueError):
                raise ValueError('Takip süresi 1–365 gün olmalı.') from None
            if str(p.get('followupDays')) != str(days) or not 1 <= days <= 365:
                raise ValueError('Takip süresi 1–365 gün olmalı.')
            proposal = {'description': _text(p.get('description'), 'İşlem kapsamı', 5),
                        'owner': _text(p.get('owner'), 'Sorumlu'), 'dueDate': _date(p.get('dueDate')),
                        'successMetric': _text(p.get('successMetric'), 'Başarı ölçütü', 5), 'followupDays': days}
            if proposal['dueDate'] < today:
                raise ValueError('Termin değerlendirme tarihinden önce olamaz.')
            if proposal == doc['proposal']:
                return _view(doc)
            if task:
                next(t for t in doc['tasks'] if t['id'] == task['id'])['status'] = 'superseded'
            doc['revision'] += 1
            doc['proposal'] = proposal
            doc['revisions'].append({'revision': doc['revision'], 'proposal': copy.deepcopy(proposal), 'at': now()})
            doc['state'] = 'pending'
            _event(doc, 'Öneri değişti; yeni sürüm için yeniden onay gerekiyor.', actor)
        elif operation in ('approve', 'reject'):
            if doc['state'] != 'pending':
                raise ValueError('Bu sürüm onay beklemiyor.')
            note = _text(data.get('note'), 'Ret gerekçesi', 5) if operation == 'reject' else str(data.get('note') or '')[:2000]
            if operation == 'approve' and doc['proposal']['dueDate'] < today:
                raise ValueError('Onaydan önce geçmiş termini güncelleyin.')
            doc['approvals'].append({'revision': doc['revision'], 'decision': 'approved' if operation == 'approve' else 'rejected',
                                     'actor': actor, 'at': now(), 'businessDate': today, 'note': note})
            doc['state'] = 'approved' if operation == 'approve' else 'rejected'
            if operation == 'approve':
                doc['tasks'].append({'id': f"{doc['id']}-task-{doc['revision']}", 'revision': doc['revision'], 'status': 'ready',
                                     'owner': doc['proposal']['owner'], 'dueDate': doc['proposal']['dueDate']})
            _event(doc, 'Öneri onaylandı; görev oluşturuldu.' if operation == 'approve' else f'Öneri reddedildi: {note}', actor)
        elif operation in ('start', 'apply'):
            expected = 'approved' if operation == 'start' else 'in_progress'
            if doc['state'] != expected or not task:
                raise ValueError('Aksiyon bu aşamada ilerletilemez; geçerli onay ve önceki adım gerekir.')
            stored_task = next(t for t in doc['tasks'] if t['id'] == task['id'])
            stored_task['status'] = 'in_progress' if operation == 'start' else 'applied'
            doc['state'] = 'in_progress' if operation == 'start' else 'monitoring'
            if operation == 'apply':
                stored_task['note'] = _text(data.get('note'), 'Uygulama notu', 5)
                stored_task['appliedDate'] = today
                stored_task['followupDate'] = (date.fromisoformat(today)+timedelta(days=doc['proposal']['followupDays'])).isoformat()
            _event(doc, 'Aksiyon başlatıldı.' if operation == 'start' else 'Aksiyon uygulandı; takip tarihi belirlendi.', actor)
        elif operation == 'feedback':
            if doc['state'] != 'monitoring' or not _view(doc)['followupReady']:
                raise ValueError('Takip tarihi henüz gelmedi veya değerlendirme tamamlandı.')
            outcome = data.get('outcome')
            if outcome not in OUTCOMES:
                raise ValueError('Geçerli bir takip sonucu seçin.')
            measured = outcome != 'unmeasurable'
            values = {}
            for key in ('before', 'after'):
                try:
                    value = float(data.get(key)) if measured else None
                except (TypeError, ValueError):
                    raise ValueError('Ölçülebilir sonuç için önce ve sonra değerleri gerekir.') from None
                if value is not None and not math.isfinite(value):
                    raise ValueError('Ölçüm sonlu bir sayı olmalı.')
                values[key] = value
            doc['feedback'] = {'outcome': outcome, **values, 'unit': _text(data.get('unit'), 'Birim') if measured else '',
                               'note': _text(data.get('note'), 'Değerlendirme notu', 5),
                               'evidence': _text(data.get('evidence'), 'Ölçüm kaynağı', 5) if measured else 'Veri yetersiz',
                               'at': now(), 'businessDate': today, 'source': 'user_reported'}
            doc['state'] = 'reviewed'
            _event(doc, 'Takip değerlendirildi; kullanıcı geri bildirimi kaydedildi.', actor)
        elif operation == 'reopen':
            if doc['state'] not in ('reviewed', 'rejected'):
                raise ValueError('Yalnız sonuçlanmış veya reddedilmiş karar yeniden incelenebilir.')
            if doc['childId']:
                return _view(_read(con, doc['childId'], scope))
            child = _base(uuid.uuid4().hex, scope, doc['category'], doc['entity'], doc['title'], copy.deepcopy(doc['snapshot']))
            child['parentId'] = doc['id']
            child['snapshot']['uncertainty'] += ' Önceki kararın kanıtı korunmuştur; yeni karar öncesi güncelliğini doğrulayın.'
            doc['childId'] = child['id']
            _event(doc, 'Sonuçtan yeni inceleme başlatıldı.', actor)
            _insert(con, child)
            _save(con, doc)
            con.commit()
            return _view(child)
        else:
            raise ValueError('Geçersiz karar işlemi.')
        _save(con, doc)
        con.commit()
    return _view(doc)


def from_entity(data):
    """Create an unapproved user proposal from a server-verified profile."""
    if _scope(data) != 'live':
        raise ValueError('Profil kararları yalnız yüklenmiş kaynak veriden hazırlanır.')
    entity_type = data.get('entityType')
    code = _text(data.get('code'), 'Varlık kodu')
    description = _text(data.get('description'), 'Önerilen işlem', 5)
    metric = _text(data.get('successMetric'), 'Başarı ölçütü', 5)
    chosen = _date(data.get('analysisDate'))
    if entity_type == 'customer':
        from analysis.customer_analytics import customer_analytics
        dataset = customer_analytics({'analysisDate': chosen})
        entity = next((c for c in dataset.get('customers', []) if c['code'] == code), None)
        category, module = 'customer', 'customers'
    elif entity_type == 'product':
        dataset = engine.signals({'analysisDate': chosen, 'persist': False})
        entity = next((p for p in dataset.get('products', []) if p['code'] == code), None)
        category, module = 'commercial', 'products'
    else:
        raise ValueError('Yalnız ürün veya müşteri profilinden karar hazırlanabilir.')
    if not entity:
        raise ValueError('Seçili tarihte kaynak veride bu profil bulunamadı.')
    chosen = dataset['analysisDate']
    tags = entity.get('tags', [])
    snapshot = {'analysisDate': chosen, 'entityType': entity_type, 'entityId': code, 'sourceModule': module,
                'period': dataset['periods']['current'], 'filters': {'analysisDate': chosen, 'entityType': entity_type, 'code': code},
                'provenance': 'records', 'quality': 'Kabul edilmiş kayıtların profil özeti; kullanıcı tarafından önerilen karar.',
                'tags': [{'name': t['name'], 'rule': t['code'], 'reason': t.get('explanation') or f"Gözlem: {t['evidence'].get('observed')}; referans: {t['evidence'].get('reference')}"} for t in tags],
                'observed': entity['sales'], 'threshold': None, 'unit': 'EUR net satış',
                'score': max((t.get('score', 0) for t in tags), default=0), 'confidence': 'Kaynak profil; kullanıcı önerisi',
                'impact': None, 'insight': f"{entity['name']}: güncel 90 günde net satış €{entity['sales']:,.2f}, kâr €{entity['profit']:,.2f}. Kullanıcı önerisi: {description}",
                'uncertainty': 'Bu öneri kullanıcı tarafından hazırlanmıştır; otomatik olarak tespit edilmiş yeni bir sinyal veya kanıtlanmış etki değildir.',
                'recommendedAction': description}
    from analysis.decision_workflow import _attach_source_references
    reference = {'entityType': entity_type, 'entityId': code, 'evidence': {}}
    _attach_source_references([reference], chosen)
    snapshot['evidence'] = reference['evidence']
    with closing(engine.db()) as con:
        _schema(con)
        con.execute('BEGIN IMMEDIATE')
        snapshot['sources'] = [dict(row) for row in con.execute("SELECT id,name,kind FROM batches WHERE id IN (SELECT id FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1) OR id IN (SELECT id FROM batches WHERE kind='stock' ORDER BY created DESC LIMIT 1) ORDER BY kind")]
        key = json.dumps([entity_type, code, chosen, description, metric, snapshot['sources']], sort_keys=True)
        origin = 'profile:' + hashlib.sha256(key.encode()).hexdigest()
        existing = con.execute("SELECT document FROM decision_cases WHERE scope='live' AND origin=?", (origin,)).fetchone()
        if existing:
            return _view(json.loads(existing[0]))
        doc = _base(uuid.uuid4().hex, 'live', category, entity['name'], 'Profil incelemesinden karar önerisi', snapshot, origin)
        doc['proposal']['successMetric'] = metric
        doc['revisions'][0]['proposal'] = copy.deepcopy(doc['proposal'])
        _event(doc, 'Kullanıcı profil incelemesinden bir öneri hazırladı; uygulama onayı verilmedi.', 'Yerel kullanıcı')
        _insert(con, doc)
        con.commit()
    return _view(doc)


def dispatch(data):
    handlers = {'case_list': listing, 'case_detail': detail, 'case_demo_prepare': seed,
                'case_evaluate': evaluate, 'case_mutate': mutate, 'case_from_entity': from_entity}
    return handlers[data['action']](data)
