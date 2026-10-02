"""Local CSV ingestion and quality engine. Standard library only; no spreadsheet coercion."""
import base64
import csv
import hashlib
import io
import json
import os
import re
import sqlite3
import sys
import unicodedata
import uuid
from collections import Counter, defaultdict
from contextlib import closing
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median

STOCK = ['Ambar', 'Malzeme Grubu', 'Kodu', 'Aciklamasi', 'Stok Miktari', 'Icerik', 'Maliyet Fiyati', 'Stok Degeri', 'Bestand nach letzter EK RE', 'Stok Degeri (KDV Dahil)']
MOVEMENT = ['Ambar', 'Satici', 'Fatura Türü', 'Fatura Tarihi', 'Fatura No', 'Malzeme Grubu', 'Malzeme Kodu', 'Malzeme Aciklamasi', 'Birim', 'Miktar', 'Birim Fiyati', 'Indirim Tutari', 'Net Satir Tutari', 'Icerik', 'Maliyet Fiyati', 'Satis Fiyati', 'Satir Maliyeti', 'Satir Marji', 'Satir Kari', 'Maliyet nach letzter EK RE', 'Kar nach letzter EK RE', 'Marj nach letzter EK RE', 'Müsteri Kodu', 'Müsteri Ünvani', 'Posta Kodu', 'Sehir', 'Ülke', 'Sevkiyat Adresi', 'Ay', 'Yil', 'Cari Tipi', 'PrimVar']
NUMERIC = set(['Stok Miktari', 'Icerik', 'Maliyet Fiyati', 'Stok Degeri', 'Bestand nach letzter EK RE', 'Stok Degeri (KDV Dahil)', 'Miktar', 'Birim Fiyati', 'Indirim Tutari', 'Net Satir Tutari', 'Satis Fiyati', 'Satir Maliyeti', 'Satir Marji', 'Satir Kari', 'Maliyet nach letzter EK RE', 'Kar nach letzter EK RE', 'Marj nach letzter EK RE', 'Ay', 'Yil'])
MARGINS = {'Satir Marji', 'Marj nach letzter EK RE'}
REQUIRED = {'stock': {'Ambar', 'Kodu', 'Stok Miktari'}, 'movement': {'Ambar', 'Fatura Türü', 'Fatura Tarihi', 'Fatura No', 'Malzeme Kodu', 'Birim', 'Miktar', 'Net Satir Tutari'}}
KINDS = {'stock': STOCK, 'movement': MOVEMENT}
ROOT = Path(os.environ.get('DATA_DIR', Path(__file__).resolve().parents[1] / 'data'))

QUALITY_RULES = [
    {'code': 'column_count', 'dimension': 'schema', 'name': 'Satır kolon sayısı', 'severity': 'error', 'modules': ['Tüm analizler']},
    {'code': 'empty_row', 'dimension': 'schema', 'name': 'Boş kaynak satırı', 'severity': 'error', 'modules': ['Tüm analizler']},
    {'code': 'extra_columns', 'dimension': 'schema', 'name': 'Eşleştirilmemiş kolon', 'severity': 'warning', 'modules': ['İlgili kolon']},
    {'code': 'missing', 'dimension': 'completeness', 'name': 'Boş alan', 'severity': 'mixed', 'modules': ['Alan bağımlı analizler']},
    {'code': 'conversion', 'dimension': 'validity', 'name': 'Tarih ve sayı dönüşümü', 'severity': 'error', 'modules': ['Tüm analizler']},
    {'code': 'zero_cost', 'dimension': 'validity', 'name': 'Sıfır maliyet', 'severity': 'error', 'modules': ['Kârlılık']},
    {'code': 'invalid_content', 'dimension': 'validity', 'name': 'Paket içeriği', 'severity': 'warning', 'modules': ['Miktar dönüşümü', 'Stok']},
    {'code': 'negative_stock', 'dimension': 'validity', 'name': 'Negatif stok', 'severity': 'warning', 'modules': ['Stok']},
    {'code': 'invoice_type', 'dimension': 'validity', 'name': 'Fatura türü', 'severity': 'warning', 'modules': ['Satış', 'Satın alma']},
    {'code': 'unit', 'dimension': 'validity', 'name': 'Birim sözlüğü', 'severity': 'warning', 'modules': ['Miktar', 'Stok']},
    {'code': 'sign', 'dimension': 'consistency', 'name': 'Fatura türü ve miktar işareti', 'severity': 'warning', 'modules': ['Satış', 'Satın alma']},
    {'code': 'date_mismatch', 'dimension': 'consistency', 'name': 'Fatura tarihi ve Ay/Yıl', 'severity': 'warning', 'modules': ['Zaman analizleri']},
    {'code': 'duplicate_candidate', 'dimension': 'consistency', 'name': 'Dosya içi tekrar adayı', 'severity': 'warning', 'modules': ['Tüm analizler']},
    {'code': 'overlap', 'dimension': 'consistency', 'name': 'Önceki aktarımla çakışma', 'severity': 'warning', 'modules': ['Tüm analizler']},
]

FIELD_MODULES = {
    'Satici': ['Satıcı'], 'Müsteri Kodu': ['Müşteri'], 'Müsteri Ünvani': ['Müşteri'],
    'Malzeme Grubu': ['Kategori'], 'Maliyet Fiyati': ['Kârlılık'], 'Satir Maliyeti': ['Kârlılık'],
    'Satir Kari': ['Kârlılık'], 'Satir Marji': ['Kârlılık'], 'Maliyet nach letzter EK RE': ['Yerine koyma'],
    'Kar nach letzter EK RE': ['Yerine koyma'], 'Marj nach letzter EK RE': ['Yerine koyma'],
    'Sehir': ['Coğrafya'], 'Ülke': ['Coğrafya'], 'Posta Kodu': ['Coğrafya'],
    'Sevkiyat Adresi': ['Sevkiyat'], 'Icerik': ['Miktar dönüşümü'], 'PrimVar': ['Prim analizi'],
}

SEVERITY_CATALOG = {
    'info': {'label': 'Bilgi', 'weight': 25}, 'attention': {'label': 'Dikkat', 'weight': 50},
    'high': {'label': 'Yüksek', 'weight': 70}, 'critical': {'label': 'Kritik', 'weight': 88},
}
METRIC_CATALOG = {
    'net_sales': {'label': 'Net satış', 'unit': 'EUR', 'formula': 'satış - satış iadesi', 'scope': 'sales'},
    'gross_profit': {'label': 'Brüt kâr', 'unit': 'EUR', 'formula': 'net satış - satış maliyeti', 'scope': 'sales'},
    'margin': {'label': 'Brüt marj', 'unit': '%', 'formula': 'brüt kâr / net satış', 'scope': 'sales'},
    'replacement_margin': {'label': 'Yerine koyma marjı', 'unit': '%', 'formula': '(net satış - yerine koyma maliyeti) / net satış', 'scope': 'sales'},
    'return_rate': {'label': 'İade oranı', 'unit': '%', 'formula': 'satış iadesi / brüt satış', 'scope': 'sales'},
    'coverage_days': {'label': 'Stok kapsama günü', 'unit': 'gün', 'formula': 'birim stok / günlük normalize tüketim', 'scope': 'inventory'},
}


def invoice_kind(row):
    """Canonical invoice semantics shared by every analysis module."""
    value = normalize(str(row.get('Fatura Türü') or ''))
    return {'satis':'sale','satis faturasi':'sale','satis iadesi':'return','satis iade faturasi':'return',
      'satin alma':'purchase','satin alma faturasi':'purchase','satinalma faturasi':'purchase','alis faturasi':'purchase',
      'satin alma iadesi':'purchase_return','satin alma iade faturasi':'purchase_return','satinalma iade faturasi':'purchase_return','alis iade faturasi':'purchase_return'}.get(value)


def stable_signal_id(entity_type, entity_id, tag_code):
    return hashlib.sha256(f'{entity_type}|{entity_id}|{tag_code}'.encode()).hexdigest()[:32]


def recommended_action(tag_code):
    if tag_code in ('PRODUCT_NEGATIVE_MARGIN','PRODUCT_LOW_MARGIN','PRODUCT_MARGIN_EROSION','PRODUCT_REPLACEMENT_MARGIN_RISK','PRODUCT_PRICE_BEHIND_COST'):
        return 'Fiyat, maliyet ve yerine koyma marjını inceleyerek fiyat aksiyonu belirleyin.'
    if tag_code in ('PRODUCT_STOPPED','PRODUCT_REVENUE_SLOWING','PRODUCT_CUSTOMER_SHRINKING'):
        return 'Kaybedilen müşteri ve siparişleri inceleyerek geri kazanım planı oluşturun.'
    if tag_code in ('PRODUCT_HIGH_RETURN','PRODUCT_RETURN_RISING','PRODUCT_RETURN_WIDESPREAD'):
        return 'İade yapan müşterileri ve fiyatları inceleyerek kök nedeni doğrulayın.'
    if tag_code == 'PRODUCT_ZERO_COST':
        return 'Maliyet kaynağını doğrulayın; kayıt düzelene kadar kârlılık kararını erteleyin.'
    return 'Ürün kanıtını inceleyerek ticari fırsatı sorumlu kişiye atayın.'


def normalize(value):
    value = value.strip().replace('ı', 'i').replace('İ', 'i').casefold()
    return ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c)).strip()


def db():
    ROOT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ROOT / 'center.sqlite', timeout=30)
    con.row_factory = sqlite3.Row
    con.executescript('''
    CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY, kind TEXT NOT NULL, digest TEXT NOT NULL,
      name TEXT NOT NULL, created TEXT NOT NULL, rows INTEGER, accepted INTEGER, rejected INTEGER,
      snapshot TEXT, report TEXT NOT NULL, UNIQUE(kind,digest));
    CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY, batch_id TEXT NOT NULL, source_line INTEGER,
      kind TEXT NOT NULL, fingerprint TEXT NOT NULL, raw TEXT NOT NULL, converted TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS record_fingerprint ON records(kind,fingerprint);
    CREATE INDEX IF NOT EXISTS record_batch ON records(batch_id);
    CREATE TABLE IF NOT EXISTS tag_rules(code TEXT NOT NULL, version INTEGER NOT NULL, name TEXT NOT NULL,
      category TEXT NOT NULL, definition TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
      PRIMARY KEY(code,version));
    CREATE TABLE IF NOT EXISTS tag_runs(id TEXT PRIMARY KEY, analysis_date TEXT NOT NULL, movement_batch TEXT NOT NULL,
      official INTEGER NOT NULL, created TEXT NOT NULL, rule_version INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS tag_instances(id TEXT PRIMARY KEY, run_id TEXT NOT NULL, entity_type TEXT NOT NULL,
      entity_id TEXT NOT NULL, tag_code TEXT NOT NULL, severity TEXT NOT NULL, score REAL NOT NULL,
      confidence TEXT NOT NULL, impact_value REAL NOT NULL, evidence TEXT NOT NULL,
      UNIQUE(run_id,entity_type,entity_id,tag_code));
    CREATE INDEX IF NOT EXISTS tag_entity ON tag_instances(entity_type,entity_id);
    CREATE TABLE IF NOT EXISTS signal_instances(id TEXT PRIMARY KEY, run_id TEXT NOT NULL, entity_type TEXT NOT NULL,
      entity_id TEXT NOT NULL, tag_code TEXT NOT NULL, title TEXT NOT NULL, severity TEXT NOT NULL,
      score REAL NOT NULL, confidence TEXT NOT NULL, impact_value REAL NOT NULL, status TEXT NOT NULL,
      first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, evidence TEXT NOT NULL, recommended_action TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS signal_status ON signal_instances(status,severity,score);
    CREATE TABLE IF NOT EXISTS alerts(id TEXT PRIMARY KEY, signal_id TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
      severity TEXT NOT NULL, status TEXT NOT NULL, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
      acknowledged_at TEXT, resolved_at TEXT);
    CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY, alert_id TEXT, signal_id TEXT, entity_type TEXT NOT NULL,
      entity_id TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL, priority TEXT NOT NULL,
      status TEXT NOT NULL, owner TEXT NOT NULL, due_date TEXT, outcome TEXT, realized_impact REAL,
      created TEXT NOT NULL, updated TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS action_status ON actions(status,priority,due_date);
    CREATE TABLE IF NOT EXISTS action_events(id INTEGER PRIMARY KEY AUTOINCREMENT, action_id TEXT NOT NULL,
      event_type TEXT NOT NULL, from_status TEXT, to_status TEXT, note TEXT, created TEXT NOT NULL);
    ''')
    return con


def stage_path(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r'[a-f0-9]{32}', identifier):
        raise ValueError('Geçersiz aktarım kimliği.')
    folder = ROOT / 'staging' / identifier
    if not folder.is_dir():
        raise ValueError('Aktarım önizlemesi bulunamadı. Dosyayı yeniden seçin.')
    return folder


def read_csv(raw, encoding, delimiter=None):
    if encoding not in ('utf-8-sig', 'cp1254', 'utf-16'):
        raise ValueError('Desteklenmeyen karakter kodlaması.')
    try:
        text = raw.decode(encoding)
    except UnicodeError:
        raise ValueError('Dosya seçilen kodlamayla okunamadı. UTF-8, Windows-1254 veya UTF-16 seçimini kontrol edin.')
    if '\x00' in text:
        raise ValueError('Dosyada geçersiz karakterler var. CSV ve karakter kodlamasını kontrol edin.')

    chosen_delimiter = delimiter
    if not chosen_delimiter or chosen_delimiter == 'auto':
        first_line = io.StringIO(text, newline='').readline()
        semicolons = first_line.count(';')
        commas = first_line.count(',')
        if semicolons > commas and semicolons > 0:
            chosen_delimiter = ';'
        else:
            chosen_delimiter = ','

    reader = csv.reader(io.StringIO(text, newline=''), delimiter=chosen_delimiter, strict=True)
    try:
        headers = next(reader)
        rows = []
        for values in reader:
            rows.append({'line': reader.line_num, 'values': values})
            if len(rows) > 100000:
                raise ValueError('Bir dosyada en fazla 100.000 veri satırı destekleniyor. Dosyayı bölün.')
    except StopIteration:
        raise ValueError('Dosya boş. Başlık satırı içeren bir CSV seçin.')
    except csv.Error as exc:
        raise ValueError(f'CSV yapısı bozuk (satır {reader.line_num}): {exc}. Ayraç içeren hücreleri çift tırnak içine alın.')
    if len(headers) < 2:
        raise ValueError('Kolonlar ayrıştırılamadı. CSV dosya ayracını (noktalı virgül veya virgül) ve formatını kontrol edin.')
    return headers, rows, chosen_delimiter


def inspect(data):
    kind = data.get('kind')
    if kind not in KINDS:
        raise ValueError('Stok veya hareket dosyası seçin.')
    raw = base64.b64decode(data.get('file', ''), validate=True)
    if not raw or len(raw) > 20 * 1024 * 1024:
        raise ValueError('Dosya boş veya 20 MB sınırını aşıyor.')
    encoding = data.get('encoding', 'utf-8-sig')
    user_delimiter = data.get('delimiter')
    headers, rows, chosen_delimiter = read_csv(raw, encoding, delimiter=user_delimiter)
    expected = KINDS[kind]
    norm = [normalize(h) for h in headers]
    mapping = [norm.index(normalize(h)) if norm.count(normalize(h)) == 1 else -1 for h in expected]
    digest = hashlib.sha256(raw).hexdigest()
    with closing(db()) as con:
        previous = con.execute('SELECT name,created FROM batches WHERE kind=? AND digest=?', (kind, digest)).fetchone()
    identifier = uuid.uuid4().hex
    folder = ROOT / 'staging' / identifier
    folder.mkdir(parents=True)
    (folder / 'raw.csv').write_bytes(raw)
    meta = {'id': identifier, 'kind': kind, 'name': Path(data.get('name', 'veri.csv')).name[:240], 'encoding': encoding, 'delimiter': chosen_delimiter, 'digest': digest, 'headers': headers}
    (folder / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False), encoding='utf-8')
    duplicates = [h for h, n in Counter(norm).items() if n > 1]
    return {**meta, 'expected': expected, 'mapping': mapping, 'preview': rows[:8], 'total': len(rows), 'exactOrder': headers == expected,
            'duplicateHeaders': duplicates, 'previous': dict(previous) if previous else None,
            'fields': [{'name': h, 'type': 'number' if h in NUMERIC else 'date' if h == 'Fatura Tarihi' else 'text', 'required': h in REQUIRED[kind]} for h in expected]}


def number(value, decimal):
    """Explicit locale; reject malformed grouping, never silently guess separators."""
    value = value.strip()
    group = '.' if decimal == ',' else ','
    dp, gp = re.escape(decimal), re.escape(group)
    pattern = rf'[+-]?(?:[0-9]+|[0-9]{{1,3}}(?:{gp}[0-9]{{3}})+)(?:{dp}[0-9]+)?'
    if not re.fullmatch(pattern, value):
        raise ValueError('Sayı biçimi seçilen ondalık ayracıyla uyuşmuyor.')
    return Decimal(value.replace(group, '').replace(decimal, '.'))


def date_value(value, fmt='iso'):
    formats = {'dmy': '%d.%m.%Y', 'iso': '%Y-%m-%d', 'slash': '%d/%m/%Y'}
    value = value.strip()
    clean_date = re.split(r'[ T]', value)[0] if (' ' in value or 'T' in value) else value

    if re.match(r'^\d{4}-\d{2}-\d{2}$', clean_date):
        try:
            return datetime.strptime(clean_date, '%Y-%m-%d').date().isoformat()
        except ValueError:
            raise ValueError('Tarih takvimde geçersiz.')

    if re.match(r'^\d{2}\.\d{2}\.\d{4}$', clean_date):
        try:
            return datetime.strptime(clean_date, '%d.%m.%Y').date().isoformat()
        except ValueError:
            raise ValueError('Tarih takvimde geçersiz.')

    if re.match(r'^\d{2}/\d{2}/\d{4}$', clean_date):
        try:
            return datetime.strptime(clean_date, '%d/%m/%Y').date().isoformat()
        except ValueError:
            raise ValueError('Tarih takvimde geçersiz.')

    try:
        return datetime.strptime(clean_date, formats[fmt]).date().isoformat()
    except (ValueError, KeyError):
        raise ValueError('Tarih seçilen biçimde değil veya takvimde geçersiz.')


def analyze(data):
    folder = stage_path(data.get('id'))
    meta = json.loads((folder / 'meta.json').read_text(encoding='utf-8'))
    with closing(db()) as con:
        if con.execute('SELECT id FROM batches WHERE id=?', (meta['id'],)).fetchone():
            raise ValueError('Onaylanan aktarımın kontrol kaydı değiştirilemez. Yeni dosya ekleyin.')
    kind = meta['kind']
    headers, rows, _ = read_csv((folder / 'raw.csv').read_bytes(), meta['encoding'], delimiter=meta.get('delimiter', ','))
    expected = KINDS[kind]
    mapping = data.get('mapping', [])
    if len(mapping) != len(expected) or any(type(i) is not int or i < 0 or i >= len(headers) for i in mapping) or len(set(mapping)) != len(mapping):
        raise ValueError('Her sistem kolonunu farklı bir kaynak kolonuna eşleştirin. Eksik kolon varsa kaynak dosyayı düzeltin.')
    decimal, fmt = data.get('decimal', ','), data.get('dateFormat', 'iso')
    if decimal not in (',', '.') or fmt not in ('auto', 'dmy', 'iso', 'slash'):
        raise ValueError('Sayı veya tarih biçimi geçersiz.')
    snapshot = data.get('snapshot', '')
    if kind == 'stock':
        if snapshot:
            try:
                datetime.fromisoformat(snapshot)
            except ValueError:
                raise ValueError('Stok görüntüsünün geçerli tarih ve saatini girin.')
        else:
            snapshot = datetime.now().astimezone().isoformat()
    issues, converted_rows, counts, affected = [], [], Counter(), set()

    def issue(row, field, code, severity, message, raw=''):
        entry = {'line': row, 'field': field, 'code': code, 'severity': severity, 'message': message, 'raw': raw}
        issues.append(entry)
        counts[(code, severity, field, message)] += 1
        if row:
            affected.add(row)

    unused = [h for i, h in enumerate(headers) if i not in mapping]
    if unused:
        issue(0, 'Başlık', 'extra_columns', 'warning', 'Eşleştirilmemiş kolonlar ham dosyada korunur, analize alınmaz.', ', '.join(unused))
    seen = {}
    with closing(db()) as con:
        old_fingerprints = {r[0] for r in con.execute('SELECT DISTINCT fingerprint FROM records WHERE kind=?', (kind,))}
    invoice_types = {
        'satis': 1, 'satis faturasi': 1, 'satis iadesi': -1, 'satis iade faturasi': -1,
        'satin alma': -1, 'satin alma faturasi': -1, 'satinalma': -1, 'satinalma faturasi': -1,
        'satin alma iadesi': 1, 'satin alma iade faturasi': 1, 'satinalma iadesi': 1, 'satinalma iade faturasi': 1
    }
    dates, warehouses, missing = [], set(), Counter()
    for row in rows:
        line, values = row['line'], row['values']
        row_start = len(issues)
        if not values or all(not v.strip() for v in values):
            issue(line, 'Satır', 'empty_row', 'error', 'Boş satır. Aktarıma dahil edilmez.')
            continue
        if len(values) != len(headers):
            issue(line, 'Satır', 'column_count', 'error', f'{len(headers)} kolon bekleniyor, {len(values)} bulundu. Tırnaksız virgül veya eksik hücre olabilir.', ' | '.join(values)[:1000])
            continue
        raw = dict(zip(expected, [values[i] for i in mapping]))
        result = {}
        for h, v in raw.items():
            clean = v.strip()
            if not clean:
                result[h] = None
                missing[h] += 1
                issue(line, h, 'missing', 'error' if h in REQUIRED[kind] else 'warning', 'Zorunlu alan boş.' if h in REQUIRED[kind] else 'Alan boş; ilgili analiz için kapsam eksik.', v)
                continue
            try:
                if h in NUMERIC:
                    source_number = clean
                    if h in MARGINS and clean.endswith('%'):
                        source_number = clean[:-1].strip()
                    n = number(source_number, decimal)
                    if h in ('Ay', 'Yil') and (n != n.to_integral_value() or (h == 'Ay' and not 1 <= n <= 12) or (h == 'Yil' and not 1900 <= n <= 2200)):
                        raise ValueError('Ay 1–12, yıl 1900–2200 aralığında tam sayı olmalı.')
                    result[h] = str(n / 100 if h in MARGINS else n)
                elif h == 'Fatura Tarihi':
                    result[h] = date_value(clean, fmt)
                    dates.append(result[h])
                else:
                    result[h] = clean
            except (ValueError, InvalidOperation) as exc:
                result[h] = None
                issue(line, h, 'conversion', 'error', str(exc) or 'Değer dönüştürülemedi.', v)
        if result.get('Ambar'):
            warehouses.add(result['Ambar'])
        for h in ('Maliyet Fiyati', 'Maliyet nach letzter EK RE'):
            if result.get(h) is not None and Decimal(result[h]) == 0:
                issue(line, h, 'zero_cost', 'error', 'Maliyet sıfır. Kârlılık analizini bozmaması için analize dahil edilmedi; karantinaya alındı.', raw[h])
        if result.get('Icerik') is not None and Decimal(result['Icerik']) <= 0:
            issue(line, 'Icerik', 'invalid_content', 'warning', 'İçerik sıfır veya negatif; birim dönüşümünü doğrulayın.', raw['Icerik'])
        if kind == 'stock' and result.get('Stok Miktari') is not None and Decimal(result['Stok Miktari']) < 0:
            issue(line, 'Stok Miktari', 'negative_stock', 'warning', 'Negatif stok kaydı; kaynak incelemesi gerekli.', raw['Stok Miktari'])
        if kind == 'movement':
            inv = normalize(result.get('Fatura Türü') or '')
            if inv and inv not in invoice_types:
                issue(line, 'Fatura Türü', 'invoice_type', 'warning', 'Fatura türü tanınmadı; işaret kuralı uygulanmadı.', raw['Fatura Türü'])
            elif inv and result.get('Miktar') is not None and Decimal(result['Miktar']) * invoice_types[inv] < 0:
                issue(line, 'Miktar', 'sign', 'warning', 'Miktar işareti rapordaki fatura türü kuralıyla uyuşmuyor.', raw['Miktar'])
            if result.get('Birim') and result['Birim'].upper() not in {'G', 'KG', 'PK', 'KL', 'ST'}:
                issue(line, 'Birim', 'unit', 'warning', 'Birim tanımlı listede yok; otomatik miktar dönüşümü yapılmadı.', raw['Birim'])
            if result.get('Fatura Tarihi'):
                d = datetime.fromisoformat(result['Fatura Tarihi'])
                for h, actual in [('Ay', d.month), ('Yil', d.year)]:
                    if result.get(h) is not None and Decimal(result[h]) != actual:
                        issue(line, h, 'date_mismatch', 'warning', 'Alan fatura tarihiyle uyuşmuyor; kaynak değer korunuyor.', raw[h])
        fingerprint = hashlib.sha256(json.dumps(result, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if fingerprint in seen:
            issue(line, 'Satır', 'duplicate_candidate', 'warning', f'Aynı içerik {seen[fingerprint]}. satırda da var. Tekrar adayı; otomatik silinmez.')
        elif fingerprint in old_fingerprints:
            issue(line, 'Satır', 'overlap', 'warning', 'Bu içerik önceki aktarımda da var. Kapsam çakışması adayı; otomatik silinmez.')
        seen[fingerprint] = line
        ok = not any(i['severity'] == 'error' for i in issues[row_start:])
        converted_rows.append({'line': line, 'raw': raw, 'converted': result, 'fingerprint': fingerprint, 'valid': ok})
    good = sum(r['valid'] for r in converted_rows)
    report = {'id': meta['id'], 'kind': kind, 'name': meta['name'], 'total': len(rows), 'accepted': good, 'rejected': len(rows) - good,
              'affected': len(affected), 'errors': sum(i['severity'] == 'error' for i in issues), 'warnings': sum(i['severity'] == 'warning' for i in issues),
              'groups': [{'code': k[0], 'severity': k[1], 'field': k[2], 'message': k[3], 'count': n} for k, n in counts.items()],
              'issues': issues, 'preview': converted_rows[:10], 'warehouses': sorted(warehouses), 'range': [min(dates), max(dates)] if dates else [],
              'snapshot': snapshot, 'missing': dict(missing), 'settings': {'decimal': decimal, 'dateFormat': fmt, 'mapping': mapping, 'marginScale': 'percent-points'},
              'created': datetime.now().astimezone().isoformat()}
    (folder / 'result.json').write_text(json.dumps({'report': report, 'records': converted_rows}, ensure_ascii=False), encoding='utf-8')
    return public_report(report)


def public_report(report, offset=0, code=None):
    issues = report['issues']
    selected = [i for i in issues if not code or i['code'] == code]
    return {**report, 'issues': selected[offset:offset+100], 'issueTotal': len(selected), 'issueOffset': offset}


def commit(data):
    folder = stage_path(data.get('id'))
    result_path = folder / 'result.json'
    if not result_path.exists():
        raise ValueError('Önce kalite kontrollerini çalıştırın.')
    result = json.loads(result_path.read_text(encoding='utf-8'))
    meta = json.loads((folder / 'meta.json').read_text(encoding='utf-8'))
    r = result['report']
    if not r['accepted']:
        raise ValueError('Aktarılabilir satır yok. Kaynak dosyayı düzeltin.')
    if (r['warnings'] or r['rejected']) and data.get('acknowledge') is not True:
        raise ValueError('Uyarıları ve karantinada kalacak satırları onaylayın.')
    con = db()
    try:
        con.execute('BEGIN IMMEDIATE')
        previous = con.execute('SELECT id FROM batches WHERE kind=? AND digest=?', (meta['kind'], meta['digest'])).fetchone()
        if previous:
            raise ValueError('Bu dosya daha önce aktarıldı. İkinci kez kayıt oluşturulmadı.')
        r['created'] = datetime.now().astimezone().isoformat()
        con.execute('INSERT INTO batches VALUES(?,?,?,?,?,?,?,?,?,?)', (r['id'], meta['kind'], meta['digest'], meta['name'], r['created'], r['total'], r['accepted'], r['rejected'], r['snapshot'], json.dumps(r, ensure_ascii=False)))
        for record in result['records']:
            if record['valid']:
                con.execute('INSERT INTO records(batch_id,source_line,kind,fingerprint,raw,converted) VALUES(?,?,?,?,?,?)', (r['id'], record['line'], r['kind'], record['fingerprint'], json.dumps(record['raw'], ensure_ascii=False), json.dumps(record['converted'], ensure_ascii=False)))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return {'id': r['id'], 'accepted': r['accepted'], 'rejected': r['rejected']}


def _score(total, affected):
    return 100 if not total else max(0, round((1 - min(affected, total) / total) * 100, 2))


def quality_summary(reports):
    """Build transparent quality dimensions from the latest report of each source type."""
    latest = {}
    for report in reports:
        latest.setdefault(report['kind'], report)
    selected = list(latest.values())
    if not selected:
        return {'status': 'no_data', 'label': 'Veri bekleniyor', 'dimensions': [], 'rules': [], 'modules': [], 'freshness': {}, 'coverage': {}}

    total = sum(r['total'] for r in selected)
    rule_index = {r['code']: r for r in QUALITY_RULES}
    affected = {'schema': set(), 'validity': set(), 'consistency': set()}
    rule_counts = Counter()
    for report in selected:
        prefix = report['kind'] + ':'
        for item in report.get('issues', []):
            rule_counts[item['code']] += 1
            rule = rule_index.get(item['code'])
            if rule and rule['dimension'] in affected and item.get('line'):
                affected[rule['dimension']].add(prefix + str(item['line']))

    possible = 0
    missing_weight = 0
    missing_fields = []
    for kind, report in latest.items():
        for field in KINDS[kind]:
            weight = 3 if field in REQUIRED[kind] else 1
            count = int(report.get('missing', {}).get(field, 0))
            possible += report['total'] * weight
            missing_weight += count * weight
            if count:
                missing_fields.append({'kind': kind, 'field': field, 'count': count,
                                       'rate': round(count / report['total'] * 100, 1) if report['total'] else 0,
                                       'required': field in REQUIRED[kind], 'modules': FIELD_MODULES.get(field, ['İlgili analiz'])})
    completeness = 100 if not possible else max(0, round((1 - missing_weight / possible) * 100, 1))
    dimensions = [
        {'key': 'schema', 'label': 'Şema uygunluğu', 'score': _score(total, len(affected['schema'])), 'affected': len(affected['schema']), 'affectedLabel': f"{len(affected['schema']):,} etkilenen satır", 'description': 'Kolon ve satır yapısının beklenen CSV şemasına uyumu'},
        {'key': 'completeness', 'label': 'Tamlık', 'score': completeness, 'affected': sum(f['count'] for f in missing_fields), 'affectedLabel': f"{sum(f['count'] for f in missing_fields):,} eksik hücre", 'description': 'Zorunlu alanlara üç kat ağırlık veren doluluk ölçümü'},
        {'key': 'validity', 'label': 'Geçerlilik', 'score': _score(total, len(affected['validity'])), 'affected': len(affected['validity']), 'affectedLabel': f"{len(affected['validity']):,} etkilenen satır", 'description': 'Tarih, sayı, maliyet, birim ve değer geçerliliği'},
        {'key': 'consistency', 'label': 'Tutarlılık', 'score': _score(total, len(affected['consistency'])), 'affected': len(affected['consistency']), 'affectedLabel': f"{len(affected['consistency']):,} etkilenen satır", 'description': 'İşaret, tarih ve tekrar kurallarının kendi içindeki uyumu'},
    ]

    movement = latest.get('movement')
    stock = latest.get('stock')
    movement_warehouses = set(movement.get('warehouses', [])) if movement else set()
    stock_warehouses = set(stock.get('warehouses', [])) if stock else set()
    unknown_warehouses = sorted(movement_warehouses - stock_warehouses)
    today = datetime.now().astimezone().date()
    last_movement = datetime.fromisoformat(movement['range'][-1]).date() if movement and movement.get('range') else None
    movement_age = (today - last_movement).days if last_movement else None
    stock_date = datetime.fromisoformat(stock['snapshot']).date() if stock and stock.get('snapshot') else None
    stock_age = (today - stock_date).days if stock_date else None

    def module(name, kind, fields, note):
        report = latest.get(kind)
        if not report:
            return {'name': name, 'status': 'missing', 'label': 'Veri bekleniyor', 'coverage': 0, 'note': note}
        missing = sum(min(report['total'], int(report.get('missing', {}).get(field, 0))) for field in fields)
        denominator = report['total'] * len(fields) if fields else report['total']
        coverage = round((1 - missing / denominator) * 100, 1) if denominator else 0
        status = 'ready' if coverage == 100 else 'partial'
        return {'name': name, 'status': status, 'label': 'Hazır' if status == 'ready' else 'Kısmen hazır', 'coverage': coverage, 'note': note}

    modules = [
        module('Satış', 'movement', ['Fatura Türü', 'Fatura Tarihi', 'Fatura No', 'Malzeme Kodu', 'Birim', 'Miktar', 'Net Satir Tutari'], 'İndirim ve işaret tanımları iş kabulünde ayrıca doğrulanır.'),
        module('Müşteri', 'movement', ['Müsteri Kodu'], 'Müşteri kodu olmayan satırlar müşteri kırılımına girmez.'),
        module('Kârlılık', 'movement', ['Maliyet Fiyati', 'Satir Maliyeti', 'Satir Kari', 'Satir Marji'], 'Maliyet ve marj formülleri kaynak faturayla uzlaştırılmalıdır.'),
        module('Satıcı', 'movement', ['Satici'], 'Boş satıcılar atanmamış olarak ayrı izlenir.'),
        module('Coğrafya', 'movement', ['Sehir', 'Ülke', 'Posta Kodu'], 'Eksik konumlar coğrafi analiz kapsamını azaltır.'),
        module('Stok', 'stock', ['Ambar', 'Kodu', 'Stok Miktari'], 'Hareket ambarlarının stok kapsamı ayrıca kontrol edilir.'),
    ]
    for item in modules:
        if item['name'] == 'Stok' and item['status'] == 'ready' and unknown_warehouses:
            item.update(status='partial', label='Kısmen hazır', note=f"Stoku bilinmeyen {len(unknown_warehouses)} hareket ambarı var.")
    module_rule_codes = {
        'Satış': {'invoice_type', 'sign', 'date_mismatch', 'conversion'},
        'Müşteri': {'conversion'},
        'Kârlılık': {'zero_cost', 'conversion'},
        'Satıcı': {'conversion'},
        'Coğrafya': {'conversion'},
        'Stok': {'negative_stock', 'invalid_content', 'unit', 'conversion'},
    }
    for item in modules:
        finding_count = sum(rule_counts[code] for code in module_rule_codes[item['name']])
        item['findingCount'] = finding_count
        if item['status'] == 'ready' and finding_count:
            item.update(status='partial', label='Kısmen hazır',
                        note=f"Bu modülü etkileyen {finding_count:,} kalite bulgusu incelenmeli.")

    rejected = sum(r.get('rejected', 0) for r in selected)
    lowest = min(d['score'] for d in dimensions)
    if rejected or any(d['score'] < 95 for d in dimensions if d['key'] in ('schema', 'validity')):
        status, label = 'correction', 'Düzeltme gerekli'
    elif lowest < 100 or unknown_warehouses or (movement_age is not None and movement_age > 3):
        status, label = 'partial', 'Kısmen hazır'
    else:
        status, label = 'ready', 'Hazır'

    rules = [{**rule, 'count': rule_counts[rule['code']], 'active': rule_counts[rule['code']] > 0} for rule in QUALITY_RULES]
    return {
        'status': status, 'label': label, 'dimensions': dimensions, 'rules': rules,
        'missingFields': sorted(missing_fields, key=lambda x: (-x['count'], x['field'])), 'modules': modules,
        'freshness': {'movementAgeDays': movement_age, 'stockAgeDays': stock_age,
                      'movementStatus': 'critical' if movement_age is not None and movement_age > 3 else 'current' if movement_age is not None else 'missing',
                      'stockStatus': 'critical' if stock_age is not None and stock_age > 3 else 'current' if stock_age is not None else 'missing'},
        'coverage': {'movementWarehouses': sorted(movement_warehouses), 'stockWarehouses': sorted(stock_warehouses), 'unknownWarehouses': unknown_warehouses},
        'scope': {'rows': total, 'files': len(selected), 'latestOnly': True},
    }


def listing():
    with closing(db()) as con:
        batches = []
        reports = []
        for row in con.execute('SELECT * FROM batches ORDER BY created DESC'):
            r = json.loads(row['report'])
            reports.append(r)
            batches.append({k: r[k] for k in ['id','kind','name','created','total','accepted','rejected','warnings','errors','affected','warehouses','snapshot','range','missing']})
        totals = {r['kind']: r['n'] for r in con.execute('SELECT kind,COUNT(*) n FROM records GROUP BY kind')}
    return {'batches': batches, 'totals': totals, 'quality': quality_summary(reports)}


def get_report(data):
    identifier = data.get('id')
    folder = stage_path(identifier)
    with closing(db()) as con:
        saved = con.execute('SELECT report FROM batches WHERE id=?', (identifier,)).fetchone()
    report = json.loads(saved['report']) if saved else json.loads((folder / 'result.json').read_text(encoding='utf-8'))['report']
    return public_report(report, max(0, int(data.get('offset', 0))), data.get('code'))


def export_issues(data):
    folder = stage_path(data.get('id'))
    report = json.loads((folder / 'result.json').read_text(encoding='utf-8'))['report']
    out = io.StringIO(newline='')
    writer = csv.writer(out)
    writer.writerow(['Kaynak satır', 'Alan', 'Seviye', 'Kontrol', 'Ham değer', 'Açıklama'])
    def safe(value):
        value = str(value)
        return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r')) else value
    for issue in report['issues']:
        writer.writerow([issue['line'], issue['field'], issue['severity'], issue['code'], safe(issue['raw']), issue['message']])
    return {'csv': '\ufeff' + out.getvalue()}


def _float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def cockpit(data):
    """Management cockpit computed only from the latest accepted movement batch."""
    filters = data.get('filters') or {}
    with closing(db()) as con:
        batch = con.execute("SELECT id,report FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1").fetchone()
        if not batch:
            return {'status': 'no_data', 'options': {'warehouses': [], 'sellers': [], 'groups': [], 'cities': []}}
        records = [json.loads(r['converted']) for r in con.execute(
            "SELECT converted FROM records WHERE kind='movement' AND batch_id=?", (batch['id'],))]
    report = json.loads(batch['report'])

    def invoice_kind(row):
        kind = normalize(str(row.get('Fatura Türü') or ''))
        if kind in ('satis', 'satis faturasi'):
            return 'sale'
        if kind in ('satis iadesi', 'satis iade faturasi'):
            return 'return'
        return None

    sales = [r for r in records if invoice_kind(r)]
    dates = sorted(r.get('Fatura Tarihi') for r in sales if r.get('Fatura Tarihi'))
    options = {
        'warehouses': sorted({r.get('Ambar') for r in sales if r.get('Ambar')}),
        'sellers': sorted({r.get('Satici') for r in sales if r.get('Satici')}),
        'groups': sorted({r.get('Malzeme Grubu') for r in sales if r.get('Malzeme Grubu')}),
        'cities': sorted({r.get('Sehir') for r in sales if r.get('Sehir')}),
        'minDate': dates[0] if dates else None, 'maxDate': dates[-1] if dates else None,
    }

    mode = filters.get('dateMode', 'all')
    start, end = filters.get('start'), filters.get('end')
    month = str(filters.get('month') or '')
    year = str(filters.get('year') or '')
    warehouses = set(filters.get('warehouses') or [])
    sellers = set(filters.get('sellers') or [])
    groups = set(filters.get('groups') or [])
    cities = set(filters.get('cities') or [])
    margin = filters.get('margin', 'all')

    def selected(r):
        d = str(r.get('Fatura Tarihi') or '')
        if mode == 'range' and ((start and d < start) or (end and d > end)): return False
        if mode == 'month' and month and d[5:7] != month.zfill(2): return False
        if mode == 'month-year' and (month and d[5:7] != month.zfill(2) or year and d[:4] != year): return False
        if mode == 'year' and year and d[:4] != year: return False
        if warehouses and r.get('Ambar') not in warehouses: return False
        if sellers and r.get('Satici') not in sellers: return False
        if groups and r.get('Malzeme Grubu') not in groups: return False
        if cities and r.get('Sehir') not in cities: return False
        m = _float(r.get('Satir Marji'))
        if margin == 'loss' and m >= 0: return False
        if margin == 'low' and not 0 <= m < .15: return False
        if margin == 'high' and m < .30: return False
        return True

    rows = [r for r in sales if selected(r)]
    return_policy = filters.get('returnPolicy', 'net')

    def signed(r, field):
        value = abs(_float(r.get(field)))
        return -value if invoice_kind(r) == 'return' else value

    gross_sales = sum(abs(_float(r.get('Net Satir Tutari'))) + abs(_float(r.get('Indirim Tutari'))) for r in rows if invoice_kind(r) == 'sale')
    returns = sum(abs(_float(r.get('Net Satir Tutari'))) for r in rows if invoice_kind(r) == 'return')
    discounts = sum(abs(_float(r.get('Indirim Tutari'))) for r in rows if invoice_kind(r) == 'sale')
    net_sales = sum(signed(r, 'Net Satir Tutari') for r in rows) if return_policy == 'net' else sum(abs(_float(r.get('Net Satir Tutari'))) for r in rows)
    cogs = sum(signed(r, 'Satir Maliyeti') for r in rows)
    profit = net_sales - cogs
    invoices = {r.get('Fatura No') for r in rows if r.get('Fatura No')}
    customers = {r.get('Müsteri Kodu') for r in rows if r.get('Müsteri Kodu')}
    products = {r.get('Malzeme Kodu') for r in rows if r.get('Malzeme Kodu')}

    selected_dates = [datetime.fromisoformat(r['Fatura Tarihi']).date() for r in rows if r.get('Fatura Tarihi')]
    period_start, period_end = (min(selected_dates), max(selected_dates)) if selected_dates else (None, None)
    daily = bool(period_start and period_end and (period_end - period_start).days <= 90 and mode != 'all')
    trend = defaultdict(lambda: {'sales': 0.0, 'profit': 0.0})
    for r in rows:
        d = str(r.get('Fatura Tarihi') or '')
        key = d if daily else d[:7]
        trend[key]['sales'] += signed(r, 'Net Satir Tutari') if return_policy == 'net' else abs(_float(r.get('Net Satir Tutari')))
        trend[key]['profit'] += signed(r, 'Satir Kari')
    trend_data = [{'key': k, 'sales': round(v['sales'], 2), 'profit': round(v['profit'], 2),
                   'margin': round(v['profit'] / v['sales'] * 100, 2) if v['sales'] else 0} for k, v in sorted(trend.items())]

    def breakdown(field):
        grouped = defaultdict(lambda: {'sales': 0.0, 'profit': 0.0, 'invoices': set()})
        for r in rows:
            key = r.get(field) or 'Atanmamış'
            grouped[key]['sales'] += signed(r, 'Net Satir Tutari')
            grouped[key]['profit'] += signed(r, 'Satir Kari')
            if r.get('Fatura No'): grouped[key]['invoices'].add(r['Fatura No'])
        return sorted([{'name': k, 'sales': round(v['sales'], 2), 'profit': round(v['profit'], 2),
                        'margin': round(v['profit']/v['sales']*100, 2) if v['sales'] else 0,
                        'invoices': len(v['invoices'])} for k, v in grouped.items()], key=lambda x: x['sales'], reverse=True)

    zero_issue_map = {}
    for issue in report.get('issues', []):
        if issue.get('code') == 'zero_cost' and issue.get('line') not in zero_issue_map:
            zero_issue_map[issue.get('line')] = issue
    zero_issues = list(zero_issue_map.values())
    loss_rows = sum(1 for r in rows if _float(r.get('Satir Kari')) < 0)
    low_rows = sum(1 for r in rows if 0 <= _float(r.get('Satir Marji')) < .15)
    high_returns = round(returns / gross_sales * 100, 2) if gross_sales else 0
    return {
        'status': 'ready', 'options': options,
        'scope': {'rows': len(rows), 'start': period_start.isoformat() if period_start else None,
                  'end': period_end.isoformat() if period_end else None, 'granularity': 'daily' if daily else 'monthly'},
        'kpis': {'grossSales': round(gross_sales,2), 'netSales': round(net_sales,2), 'returns': round(returns,2),
                 'discounts': round(discounts,2), 'cogs': round(cogs,2), 'profit': round(profit,2),
                 'margin': round(profit/net_sales*100,2) if net_sales else 0, 'quantity': round(sum(signed(r,'Miktar') for r in rows),2),
                 'invoices': len(invoices), 'customers': len(customers), 'products': len(products),
                 'averageInvoice': round(net_sales/len(invoices),2) if invoices else 0},
        'trend': trend_data,
        'waterfall': [
            {'label':'Brüt satış','value':round(gross_sales,2),'kind':'total'},
            {'label':'İndirimler','value':round(-discounts,2),'kind':'decrease'},
            {'label':'İadeler','value':round(-returns,2),'kind':'decrease'},
            {'label':'Net satış','value':round(net_sales,2),'kind':'total'},
            {'label':'Satış maliyeti','value':round(-cogs,2),'kind':'decrease'},
            {'label':'Brüt kâr','value':round(profit,2),'kind':'result'}],
        'breakdowns': {'category': breakdown('Malzeme Grubu'), 'customer': breakdown('Müsteri Ünvani'),
                       'seller': breakdown('Satici'), 'warehouse': breakdown('Ambar')},
        'risks': {'zeroCost': len(zero_issues), 'lossRows': loss_rows, 'lowMarginRows': low_rows, 'returnRate': high_returns},
        'quarantine': [{'line': i.get('line'), 'field': i.get('field'), 'value': i.get('raw'), 'message': i.get('message')} for i in zero_issues[:500]],
    }


PRODUCT_RULES = [
    ('PRODUCT_NEGATIVE_MARGIN','Zararına satılan','Kârlılık'),
    ('PRODUCT_LOW_MARGIN','Düşük marjlı','Kârlılık'),
    ('PRODUCT_HIGH_MARGIN','Yüksek marjlı','Kârlılık'),
    ('PRODUCT_MARGIN_EROSION','Marjı eriyen','Kârlılık'),
    ('PRODUCT_MARGIN_RECOVERY','Marjı güçlenen','Kârlılık'),
    ('PRODUCT_REVENUE_ACCELERATING','Satışı hızlanan','Hareket'),
    ('PRODUCT_REVENUE_SLOWING','Satışı yavaşlayan','Hareket'),
    ('PRODUCT_STOPPED','Satışı duran','Hareket'),
    ('PRODUCT_NEW_MOMENTUM','Yeni hareket kazanan','Hareket'),
    ('PRODUCT_REVENUE_LEADER','Ciro lideri','Katkı'),
    ('PRODUCT_PROFIT_LEADER','Kâr lideri','Katkı'),
    ('PRODUCT_STRATEGIC','Stratejik ürün','Katkı'),
    ('PRODUCT_HIGH_REVENUE_LOW_YIELD','Yüksek ciro, düşük verim','Katkı'),
    ('PRODUCT_PRICE_RISING','Fiyatı yükselen','Fiyat ve maliyet'),
    ('PRODUCT_PRICE_FALLING','Fiyatı düşen','Fiyat ve maliyet'),
    ('PRODUCT_COST_RISING','Maliyeti yükselen','Fiyat ve maliyet'),
    ('PRODUCT_COST_FALLING','Maliyeti düşen','Fiyat ve maliyet'),
    ('PRODUCT_PRICE_BEHIND_COST','Fiyat maliyetin gerisinde','Fiyat ve maliyet'),
    ('PRODUCT_REPLACEMENT_MARGIN_RISK','Yerine koyma marjı riskli','Fiyat ve maliyet'),
    ('PRODUCT_REPLACEMENT_MISLEADING','Gerçekleşen marj yanıltıcı','Fiyat ve maliyet'),
    ('PRODUCT_BROAD_REACH','Geniş müşteri erişimi','Müşteri'),
    ('PRODUCT_NICHE','Niş ürün','Müşteri'),
    ('PRODUCT_CUSTOMER_GROWING','Müşteri erişimi büyüyor','Müşteri'),
    ('PRODUCT_CUSTOMER_SHRINKING','Müşteri erişimi daralıyor','Müşteri'),
    ('PRODUCT_CUSTOMER_DEPENDENT','Tek müşteriye bağımlı','Müşteri'),
    ('PRODUCT_CUSTOMER_CONCENTRATED','Müşteri yoğunlaşması yüksek','Müşteri'),
    ('PRODUCT_REPEAT_STRONG','Tekrar alımı güçlü','Müşteri'),
    ('PRODUCT_HIGH_RETURN','Yüksek iade oranı','İade'),
    ('PRODUCT_RETURN_RISING','İadesi artıyor','İade'),
    ('PRODUCT_RETURN_WIDESPREAD','Yaygın iade sorunu','İade'),
    ('PRODUCT_ZERO_COST','Sıfır maliyetli kayıt içeriyor','Veri güveni'),
    ('PRODUCT_INSUFFICIENT_HISTORY','Yetersiz geçmiş','Veri güveni'),
]


def _product_tags(data):
    """Explainable product tags for a selected demo analysis date."""
    requested = str(data.get('analysisDate') or '')
    with closing(db()) as con:
        movement = con.execute("SELECT id FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1").fetchone()
        stock = con.execute("SELECT id FROM batches WHERE kind='stock' ORDER BY created DESC LIMIT 1").fetchone()
        if not movement:
            return {'status':'no_data','products':[],'summary':{},'tagCounts':[]}
        rows = []
        for stored in con.execute("SELECT source_line, converted FROM records WHERE kind='movement' AND batch_id=?", (movement['id'],)):
            parsed = json.loads(stored['converted']); parsed['_sourceLine'] = stored['source_line']; rows.append(parsed)
        stock_rows = [json.loads(r['converted']) for r in con.execute(
            "SELECT converted FROM records WHERE kind='stock' AND batch_id=?", (stock['id'],))] if stock else []

    usable = [r for r in rows if invoice_kind(r) in ('sale','return') and r.get('Fatura Tarihi') and r.get('Malzeme Kodu')]
    dates = sorted(datetime.fromisoformat(r['Fatura Tarihi']).date() for r in usable)
    if not dates:
        return {'status':'no_data','products':[],'summary':{},'tagCounts':[]}
    min_date, max_date = dates[0], dates[-1]
    try: analysis_date = datetime.fromisoformat(requested).date() if requested else max_date
    except ValueError: analysis_date = max_date
    analysis_date = min(max(analysis_date, min_date), max_date)
    cur_start = analysis_date - timedelta(days=89)
    prev_end = cur_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=89)

    stock_map = defaultdict(lambda:{'quantity':0.0,'value':0.0,'content':None,'cost':None,'replacement':None})
    for r in stock_rows:
        code = r.get('Kodu')
        if not code: continue
        s = stock_map[code]
        s['quantity'] += _float(r.get('Stok Miktari')); s['value'] += _float(r.get('Stok Degeri'))
        if r.get('Icerik') is not None: s['content'] = _float(r.get('Icerik'))
        if r.get('Maliyet Fiyati') is not None: s['cost'] = _float(r.get('Maliyet Fiyati'))
        if r.get('Bestand nach letzter EK RE') is not None: s['replacement'] = _float(r.get('Bestand nach letzter EK RE'))

    def blank():
        return {'sales':0.0,'qty':0.0,'profit':0.0,'cost':0.0,'replacementCost':0.0,'returns':0.0,
                'salesCost':0.0,'salesReplacementCost':0.0,
                'returnQty':0.0,'invoices':set(),'returnInvoices':set(),'customers':set(),'customerSales':defaultdict(float),
                'prices':[],'costUnits':[],'replacementUnits':[],'units':set(),'zeroCost':0}
    products = defaultdict(lambda:{'name':'','category':'Tanımsız','current':blank(),'previous':blank(),'allCustomers':set()})
    for r in usable:
        d = datetime.fromisoformat(r['Fatura Tarihi']).date()
        if d > analysis_date or d < prev_start: continue
        bucket = 'current' if d >= cur_start else 'previous'
        code = str(r['Malzeme Kodu']); p = products[code]
        p['name'] = r.get('Malzeme Aciklamasi') or p['name'] or code
        p['category'] = r.get('Malzeme Grubu') or p['category']
        b = p[bucket]; k = invoice_kind(r); sign = -1 if k == 'return' else 1
        amount = abs(_float(r.get('Net Satir Tutari'))); qty = abs(_float(r.get('Miktar')))
        customer = r.get('Müsteri Kodu')
        if k == 'return':
            b['returns'] += amount; b['returnQty'] += qty
            if r.get('Fatura No'): b['returnInvoices'].add(r['Fatura No'])
        else:
            b['sales'] += amount; b['qty'] += qty
            if r.get('Fatura No'): b['invoices'].add(r['Fatura No'])
            if customer:
                b['customers'].add(customer); b['customerSales'][customer] += amount; p['allCustomers'].add(customer)
            if qty:
                b['prices'].append(amount/qty)
                b['costUnits'].append(abs(_float(r.get('Satir Maliyeti')))/qty)
                b['replacementUnits'].append(abs(_float(r.get('Maliyet nach letzter EK RE')))/qty)
            if _float(r.get('Maliyet Fiyati')) == 0 or _float(r.get('Satir Maliyeti')) == 0: b['zeroCost'] += 1
        if not (k == 'sale' and (_float(r.get('Maliyet Fiyati')) == 0 or _float(r.get('Satir Maliyeti')) == 0)):
            b['cost'] += sign * abs(_float(r.get('Satir Maliyeti')))
            line_profit=_float(r.get('Satir Kari'))
            b['profit'] += line_profit if k == 'sale' else -abs(line_profit)
            b['replacementCost'] += sign * abs(_float(r.get('Maliyet nach letzter EK RE')))
            if k == 'sale':
                b['salesCost'] += abs(_float(r.get('Satir Maliyeti')))
                b['salesReplacementCost'] += abs(_float(r.get('Maliyet nach letzter EK RE')))
        if r.get('Birim'): b['units'].add(r['Birim'])

    current_total = sum(p['current']['sales']-p['current']['returns'] for p in products.values())
    previous_total = sum(p['previous']['sales']-p['previous']['returns'] for p in products.values())
    base = []
    for code,p in products.items():
        c,v = p['current'],p['previous']; net = c['sales']-c['returns']; prev_net = v['sales']-v['returns']
        margin = c['profit']/net*100 if net and c['cost'] else None
        prev_margin = v['profit']/prev_net*100 if prev_net and v['cost'] else None
        replacement_profit = net-c['replacementCost']; replacement_margin = replacement_profit/net*100 if net and c['replacementCost'] else None
        price = c['sales']/c['qty'] if c['qty'] else None; prev_price = v['sales']/v['qty'] if v['qty'] else None
        unit_cost = c['salesCost']/c['qty'] if c['qty'] and c['salesCost'] else None; prev_cost = v['salesCost']/v['qty'] if v['qty'] and v['salesCost'] else None
        replacement_unit_cost = c['salesReplacementCost']/c['qty'] if c['qty'] and c['salesReplacementCost'] else None
        share = net/current_total*100 if current_total else 0; prev_share = prev_net/previous_total*100 if previous_total else 0
        customer_shares = sorted(c['customerSales'].values(),reverse=True)
        base.append({'code':code,'name':p['name'],'category':p['category'],'sales':net,'previousSales':prev_net,
          'profit':c['profit'],'margin':margin,'previousMargin':prev_margin,'replacementProfit':replacement_profit,
          'replacementMargin':replacement_margin,'replacementCost':replacement_unit_cost,
          'replacementUnitProfit':price-replacement_unit_cost if price is not None and replacement_unit_cost is not None else None,
          'price':price,'previousPrice':prev_price,'cost':unit_cost,'previousCost':prev_cost,
          'share':share,'previousShare':prev_share,'shareDelta':share-prev_share,'quantity':c['qty']-c['returnQty'],
          'previousQuantity':v['qty']-v['returnQty'],
          'invoices':len(c['invoices']),'customers':len(c['customers']),'previousCustomers':len(v['customers']),
          'repeatCustomers':len(c['customers'] & v['customers']),'topCustomerShare':customer_shares[0]/c['sales']*100 if customer_shares and c['sales'] else 0,
          'top3CustomerShare':sum(customer_shares[:3])/c['sales']*100 if c['sales'] else 0,
          'returns':c['returns'],'returnRate':c['returns']/c['sales']*100 if c['sales'] else 0,
          'previousReturnRate':v['returns']/v['sales']*100 if v['sales'] else 0,'returnInvoices':len(c['returnInvoices']),
          'returnCustomers':len({x for x in c['customerSales'] if x}),'zeroCostRows':c['zeroCost'],
          'stock':stock_map.get(code,{}),'tags':[]})

    total_positive_profit = sum(max(0, x['profit']) for x in base)
    for x in base:
        x['profitShare'] = max(0, x['profit'])/total_positive_profit*100 if total_positive_profit else 0
        x['revenueProfitGap'] = x['share'] - x['profitShare']

    def cuts(values):
        vals=sorted(values)
        if not vals:return (0,0)
        return vals[int((len(vals)-1)*.2)], vals[int((len(vals)-1)*.8)]
    revenue_lo,revenue_hi=cuts([x['sales'] for x in base]); profit_lo,profit_hi=cuts([x['profit'] for x in base])
    momentum_lo,momentum_hi=cuts([x['shareDelta'] for x in base]); reach_lo,reach_hi=cuts([x['customers'] for x in base])
    price_changes=[(x['price']/x['previousPrice']-1)*100 for x in base if x['price'] and x['previousPrice']]
    cost_changes=[(x['cost']/x['previousCost']-1)*100 for x in base if x['cost'] and x['previousCost']]
    price_lo,price_hi=cuts(price_changes); cost_lo,cost_hi=cuts(cost_changes)
    names=dict((c,n) for c,n,_ in PRODUCT_RULES)
    priority={'PRODUCT_NEGATIVE_MARGIN':1,'PRODUCT_REPLACEMENT_MARGIN_RISK':2,'PRODUCT_PRICE_BEHIND_COST':3,
      'PRODUCT_MARGIN_EROSION':4,'PRODUCT_HIGH_RETURN':5,'PRODUCT_STOPPED':6,'PRODUCT_REVENUE_SLOWING':7,
      'PRODUCT_CUSTOMER_SHRINKING':8,'PRODUCT_CUSTOMER_DEPENDENT':9,'PRODUCT_REVENUE_LEADER':12,
      'PRODUCT_PROFIT_LEADER':13,'PRODUCT_REVENUE_ACCELERATING':14,'PRODUCT_MARGIN_RECOVERY':15}
    counts=Counter()
    for x in base:
        tags=[]
        def add(code,severity='info',observed=None,reference=None,impact=None,confidence='Yüksek'):
            severity_score=SEVERITY_CATALOG.get(severity,SEVERITY_CATALOG['info'])['weight']
            impact_score=100 if x['sales']>=revenue_hi else 60 if x['sales']>=revenue_lo else 30
            confidence_score={'Yüksek':100,'Orta':70,'Düşük':40}.get(confidence,70)
            score=round(severity_score*.65+impact_score*.2+confidence_score*.1+100*.05)
            score=min(100,score+(15 if x['sales']>=revenue_hi and severity in ('high','critical') else 0))
            signal_id=stable_signal_id('product',x['code'],code)
            tags.append({'code':code,'name':names[code],'severity':severity,'score':score,'confidence':confidence,'signalId':signal_id,
              'scoreBreakdown':{'severity':severity_score,'impact':impact_score,'confidence':confidence_score,'recency':100},
              'recommendedAction':recommended_action(code),
              'evidence':{'observed':observed,'reference':reference,'impact':round(impact if impact is not None else x['sales'],2),
              'currentPeriod':[cur_start.isoformat(),analysis_date.isoformat()],'previousPeriod':[prev_start.isoformat(),prev_end.isoformat()]}}); counts[code]+=1
        if x['zeroCostRows']: add('PRODUCT_ZERO_COST','attention',x['zeroCostRows'],0,0)
        if x['margin'] is None: add('PRODUCT_INSUFFICIENT_HISTORY','info',None,None,0,'Düşük')
        elif x['margin']<0: add('PRODUCT_NEGATIVE_MARGIN','critical',x['margin'],0,abs(x['profit']))
        elif x['margin']<15: add('PRODUCT_LOW_MARGIN','high',x['margin'],15,max(0,x['sales']*.15-x['profit']))
        elif x['margin']>=30: add('PRODUCT_HIGH_MARGIN','info',x['margin'],30,x['profit'])
        if x['margin'] is not None and x['previousMargin'] is not None:
            delta=x['margin']-x['previousMargin']
            if delta<=-5:add('PRODUCT_MARGIN_EROSION','high',delta,-5,max(0,(x['previousMargin']-x['margin'])/100*x['sales']))
            elif delta>=5:add('PRODUCT_MARGIN_RECOVERY','info',delta,5,x['profit'])
        if x['previousSales']>0 and x['sales']==0:add('PRODUCT_STOPPED','high',0,x['previousSales'],x['previousSales'])
        elif x['previousSales']==0 and x['sales']>0:add('PRODUCT_NEW_MOMENTUM','info',x['share'],0,x['sales'])
        elif x['shareDelta']>=momentum_hi:add('PRODUCT_REVENUE_ACCELERATING','info',x['shareDelta'],momentum_hi,x['sales'])
        elif x['shareDelta']<=momentum_lo:add('PRODUCT_REVENUE_SLOWING','attention',x['shareDelta'],momentum_lo,x['sales'])
        if x['sales']>=revenue_hi:add('PRODUCT_REVENUE_LEADER','info',x['share'],None,x['sales'])
        if x['profit']>=profit_hi:add('PRODUCT_PROFIT_LEADER','info',x['profit'],None,x['profit'])
        if x['sales']>=revenue_hi and x['profit']>=profit_hi:add('PRODUCT_STRATEGIC','info',x['share'],None,x['profit'])
        if x['sales']>=revenue_hi and x['margin'] is not None and x['margin']<15:add('PRODUCT_HIGH_REVENUE_LOW_YIELD','high',x['margin'],15,x['sales'])
        if x['price'] and x['previousPrice']:
            pc=(x['price']/x['previousPrice']-1)*100
            if pc>=price_hi:add('PRODUCT_PRICE_RISING','info',pc,price_hi,x['sales'])
            elif pc<=price_lo:add('PRODUCT_PRICE_FALLING','attention',pc,price_lo,x['sales'])
        else: pc=None
        if x['cost'] and x['previousCost']:
            cc=(x['cost']/x['previousCost']-1)*100
            if cc>=cost_hi:add('PRODUCT_COST_RISING','attention',cc,cost_hi,x['sales'])
            elif cc<=cost_lo:add('PRODUCT_COST_FALLING','info',cc,cost_lo,x['sales'])
            if pc is not None and cc-pc>=5:add('PRODUCT_PRICE_BEHIND_COST','high',cc-pc,5,x['sales'])
        if x['replacementMargin'] is not None and x['replacementMargin']<15:add('PRODUCT_REPLACEMENT_MARGIN_RISK','high',x['replacementMargin'],15,max(0,x['profit']-x['replacementProfit']))
        if x['margin'] is not None and x['replacementMargin'] is not None and x['margin']-x['replacementMargin']>=5:add('PRODUCT_REPLACEMENT_MISLEADING','high',x['margin']-x['replacementMargin'],5,max(0,x['profit']-x['replacementProfit']))
        if x['customers']>=reach_hi:add('PRODUCT_BROAD_REACH','info',x['customers'],reach_hi,x['sales'])
        elif x['customers']<=reach_lo and x['sales']>0:add('PRODUCT_NICHE','info',x['customers'],reach_lo,x['sales'])
        if x['previousCustomers'] and (x['customers']/x['previousCustomers']-1)*100>=20:add('PRODUCT_CUSTOMER_GROWING','info',x['customers'],x['previousCustomers'],x['sales'])
        if x['previousCustomers'] and (x['customers']/x['previousCustomers']-1)*100<=-20:add('PRODUCT_CUSTOMER_SHRINKING','attention',x['customers'],x['previousCustomers'],x['sales'])
        if x['topCustomerShare']>60:add('PRODUCT_CUSTOMER_DEPENDENT','high',x['topCustomerShare'],60,x['sales']*x['topCustomerShare']/100)
        if x['top3CustomerShare']>80:add('PRODUCT_CUSTOMER_CONCENTRATED','attention',x['top3CustomerShare'],80,x['sales']*x['top3CustomerShare']/100)
        if x['customers'] and x['repeatCustomers']/x['customers']>=.5:add('PRODUCT_REPEAT_STRONG','info',x['repeatCustomers']/x['customers']*100,50,x['sales'])
        if x['invoices']>=4 and x['returnRate']>3:add('PRODUCT_HIGH_RETURN','high',x['returnRate'],3,x['returns'])
        if x['invoices']>=4 and x['returnRate']-x['previousReturnRate']>=2:add('PRODUCT_RETURN_RISING','attention',x['returnRate']-x['previousReturnRate'],2,x['returns'])
        x['tags']=sorted(tags,key=lambda t:(priority.get(t['code'],50),-t['score']))

    official = analysis_date == max_date
    if official and data.get('persist', True):
        run_id=hashlib.sha256(f"{movement['id']}|{analysis_date.isoformat()}|1".encode()).hexdigest()[:32]
        now=datetime.now().astimezone().isoformat()
        with closing(db()) as con:
            for code,name,category in PRODUCT_RULES:
                con.execute("INSERT OR REPLACE INTO tag_rules(code,version,name,category,definition,active) VALUES(?,?,?,?,?,1)",(code,1,name,category,name))
            con.execute("INSERT OR REPLACE INTO tag_runs(id,analysis_date,movement_batch,official,created,rule_version) VALUES(?,?,?,?,?,1)",(run_id,analysis_date.isoformat(),movement['id'],1,datetime.now().astimezone().isoformat()))
            con.execute("DELETE FROM tag_instances WHERE run_id=?",(run_id,))
            for x in base:
                for t in x['tags']:
                    ident=hashlib.sha256(f"{run_id}|{x['code']}|{t['code']}".encode()).hexdigest()[:32]
                    con.execute("INSERT INTO tag_instances VALUES(?,?,?,?,?,?,?,?,?,?)",(ident,run_id,'product',x['code'],t['code'],t['severity'],t['score'],t['confidence'],t['evidence']['impact'],json.dumps(t['evidence'],ensure_ascii=False)))
                    if t['score'] >= 40:
                        previous=con.execute("SELECT first_seen FROM signal_instances WHERE id=?",(t['signalId'],)).fetchone()
                        first_seen=previous['first_seen'] if previous else now
                        con.execute("INSERT OR REPLACE INTO signal_instances VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (t['signalId'],run_id,'product',x['code'],t['code'],t['name'],t['severity'],t['score'],t['confidence'],t['evidence']['impact'],'active',first_seen,now,json.dumps(t['evidence'],ensure_ascii=False),t['recommendedAction']))
                        if t['score'] >= 60:
                            alert_id=hashlib.sha256(f"alert|{t['signalId']}".encode()).hexdigest()[:32]
                            old=con.execute("SELECT first_seen,status,acknowledged_at FROM alerts WHERE id=?",(alert_id,)).fetchone()
                            con.execute("INSERT OR REPLACE INTO alerts VALUES(?,?,?,?,?,?,?,?,?)",(alert_id,t['signalId'],f"{x['name']}: {t['name']}",t['severity'],
                              old['status'] if old and old['status']=='acknowledged' else 'open',old['first_seen'] if old else now,now,old['acknowledged_at'] if old else None,None))
            con.execute("UPDATE signal_instances SET status='inactive' WHERE run_id<>? AND status='active'",(run_id,))
            con.execute("UPDATE alerts SET status='resolved',resolved_at=? WHERE status IN ('open','acknowledged') AND signal_id IN (SELECT id FROM signal_instances WHERE status='inactive')",(now,))
            con.commit()
    base.sort(key=lambda x:x['sales'],reverse=True)
    return {'status':'ready','analysisDate':analysis_date.isoformat(),'defaultDate':max_date.isoformat(),
      'minDate':min_date.isoformat(),'simulation':not official,'periods':{'current':[cur_start.isoformat(),analysis_date.isoformat()],'previous':[prev_start.isoformat(),prev_end.isoformat()]},
      'summary':{'products':len(base),'tagged':sum(bool(x['tags']) for x in base),'signals':sum(any(t['score']>=40 for t in x['tags']) for x in base),
        'high':sum(any(t['score']>=60 for t in x['tags']) for x in base),'critical':sum(any(t['score']>=80 for t in x['tags']) for x in base)},
      'tagCounts':[{'code':c,'name':names.get(c,c),'count':n} for c,n in counts.most_common()], 'products':base}


def signals(data):
    return _product_tags(data)


def decision_catalog(_data):
    return {'metrics': METRIC_CATALOG, 'severities': SEVERITY_CATALOG,
      'invoiceKinds': {'sale':'Satış','return':'Satış iadesi','purchase':'Satın alma','purchase_return':'Satın alma iadesi'},
      'actionStatuses': {'open':'Açık','in_progress':'Devam ediyor','completed':'Tamamlandı','rejected':'Reddedildi'},
      'outcomes': {'converted':'Siparişe dönüştü','no_result':'Sonuçsuz','postponed':'Ertelendi','unmeasurable':'Ölçülemedi'}}


def decision_center(_data):
    with closing(db()) as con:
        actions=[dict(r) for r in con.execute("SELECT * FROM actions ORDER BY CASE status WHEN 'open' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END, due_date, updated DESC")]
        alerts=[dict(r) for r in con.execute("SELECT a.*,s.entity_type,s.entity_id,s.tag_code,s.score,s.confidence,s.impact_value,s.evidence,s.recommended_action FROM alerts a JOIN signal_instances s ON s.id=a.signal_id ORDER BY CASE a.severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 ELSE 2 END,s.score DESC")]
        counts=dict(con.execute("SELECT status,COUNT(*) FROM actions GROUP BY status").fetchall())
    for alert in alerts:
        alert['evidence']=json.loads(alert['evidence'])
    overdue=sum(1 for a in actions if a['due_date'] and a['due_date'] < date.today().isoformat() and a['status'] not in ('completed','rejected'))
    return {'status':'ready','summary':{'open':counts.get('open',0),'inProgress':counts.get('in_progress',0),
      'completed':counts.get('completed',0),'overdue':overdue,'activeAlerts':sum(a['status']!='resolved' for a in alerts)},
      'actions':actions,'alerts':alerts,'catalog':decision_catalog({})}


def module_analytics(data):
    """Shared explainable datasets for decision modules."""
    module=str(data.get('module') or '')
    with closing(db()) as con:
        movement=con.execute("SELECT id FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1").fetchone()
        if not movement:return {'status':'no_data','module':module,'rows':[]}
        rows=[json.loads(r['converted']) for r in con.execute("SELECT converted FROM records WHERE kind='movement' AND batch_id=?",(movement['id'],))]
    valid=[r for r in rows if r.get('Fatura Tarihi') and invoice_kind(r)]
    if not valid:return {'status':'no_data','module':module,'rows':[]}
    dates=[datetime.fromisoformat(r['Fatura Tarihi']).date() for r in valid]; min_date,max_date=min(dates),max(dates)
    sales=[r for r in valid if invoice_kind(r) in ('sale','return')]; purchases=[r for r in valid if invoice_kind(r) in ('purchase','purchase_return')]
    def sign(r):return -1 if invoice_kind(r) in ('return','purchase_return') else 1
    def amount(r):return sign(r)*abs(_float(r.get('Net Satir Tutari')))
    def row_profit(r):
        value=_float(r.get('Satir Kari'));return value if invoice_kind(r)=='sale' else -abs(value)
    def aggregate(source,key):
        grouped=defaultdict(lambda:{'sales':0.0,'profit':0.0,'returns':0.0,'invoices':set(),'customers':set(),'products':set(),'quantity':0.0,'discount':0.0})
        for r in source:
            label=str(r.get(key) or 'Bilinmiyor');g=grouped[label];k=invoice_kind(r);g['sales']+=amount(r);g['profit']+=row_profit(r);g['quantity']+=sign(r)*abs(_float(r.get('Miktar')));g['discount']+=abs(_float(r.get('Indirim Tutari')))
            if k=='return':g['returns']+=abs(_float(r.get('Net Satir Tutari')))
            if r.get('Fatura No'):g['invoices'].add(r['Fatura No'])
            if r.get('Müsteri Kodu'):g['customers'].add(r['Müsteri Kodu'])
            if r.get('Malzeme Kodu'):g['products'].add(r['Malzeme Kodu'])
        return [{'name':k,'sales':round(v['sales'],2),'profit':round(v['profit'],2),'margin':round(v['profit']/v['sales']*100,1) if v['sales'] else None,'returns':round(v['returns'],2),'invoices':len(v['invoices']),'customers':len(v['customers']),'products':len(v['products']),'quantity':round(v['quantity'],2),'discount':round(v['discount'],2)} for k,v in grouped.items()]
    base={'status':'ready','module':module,'range':[min_date.isoformat(),max_date.isoformat()],'currency':'EUR','demo':False}
    if module=='sales_profit':
        total=sum(amount(r) for r in sales);profit=sum(row_profit(r) for r in sales);returns=sum(abs(_float(r.get('Net Satir Tutari'))) for r in sales if invoice_kind(r)=='return')
        return {**base,'title':'Satış ve Kârlılık','kpis':[('Net satış',total,'EUR'),('Brüt kâr',profit,'EUR'),('Marj',profit/total*100 if total else 0,'%'),('İade',returns,'EUR')],'rows':sorted(aggregate(sales,'Malzeme Grubu'),key=lambda x:x['sales'],reverse=True),'rowLabel':'Kategori'}
    if module=='customers_360':
        grouped=defaultdict(lambda:{'name':'Bilinmiyor','sales':0.0,'profit':0.0,'returns':0.0,'invoices':defaultdict(set),'products':set(),'dates':set()})
        for r in sales:
            code=str(r.get('Müsteri Kodu') or 'Bilinmiyor');g=grouped[code];g['name']=r.get('Müsteri Ünvani') or g['name'];g['sales']+=amount(r);g['profit']+=row_profit(r)
            if invoice_kind(r)=='return':g['returns']+=abs(_float(r.get('Net Satir Tutari')))
            if r.get('Fatura No'):g['invoices'][r['Fatura No']].add(r.get('Malzeme Kodu'))
            if r.get('Malzeme Kodu'):g['products'].add(r['Malzeme Kodu'])
            g['dates'].add(datetime.fromisoformat(r['Fatura Tarihi']).date())
        result=[]
        for code,g in grouped.items():
            dates=sorted(g['dates']);gaps=[(b-a).days for a,b in zip(dates,dates[1:])];recency=(max_date-dates[-1]).days if dates else None;cadence=median(gaps) if gaps else None;late=bool(cadence and recency>cadence*1.5)
            result.append({'code':code,'name':g['name'],'sales':round(g['sales'],2),'profit':round(g['profit'],2),'margin':round(g['profit']/g['sales']*100,1) if g['sales'] else None,'returns':round(g['returns'],2),'invoices':len(g['invoices']),'customers':1,'products':len(g['products']),'recency':recency,'cadence':cadence,'late':late,'basket':round(sum(len(x) for x in g['invoices'].values())/len(g['invoices']),1) if g['invoices'] else 0,'segment':'Kayıp riski' if late else 'Aktif'})
        return {**base,'title':'Müşteri 360','kpis':[('Aktif müşteri',sum(not x['late'] for x in result),'adet'),('Toplam ciro',sum(x['sales'] for x in result),'EUR'),('Geciken müşteri',sum(x['late'] for x in result),'adet'),('Müşteri başına ciro',sum(x['sales'] for x in result)/len(result) if result else 0,'EUR')],'rows':sorted(result,key=lambda x:(not x['late'],-x['sales'])),'rowLabel':'Müşteri','note':'Kayıp riski: son siparişten geçen süre müşterinin medyan alışveriş aralığının 1,5 katını aştığında oluşur.'}
    if module=='returns_analysis':
        result=[x for x in aggregate(sales,'Müsteri Ünvani') if x['returns']>0]
        for x in result:x['returnRate']=round(x['returns']/(x['sales']+x['returns'])*100,1) if x['sales']+x['returns'] else None
        total_returns=sum(x['returns'] for x in result);gross=sum(abs(_float(r.get('Net Satir Tutari'))) for r in sales if invoice_kind(r)=='sale')
        return {**base,'title':'İade Analizi','kpis':[('İade tutarı',total_returns,'EUR'),('İade oranı',total_returns/gross*100 if gross else 0,'%'),('İade yapan müşteri',len(result),'adet'),('Etkilenen ürün',len({r.get('Malzeme Kodu') for r in sales if invoice_kind(r)=='return'}),'adet')],'rows':sorted(result,key=lambda x:x['returns'],reverse=True),'rowLabel':'Müşteri','note':'İade etkisi satış iadelerinin mutlak tutarıdır; satın alma iadeleri bu ekrana dahil edilmez.'}
    if module=='salespeople':
        result=aggregate(sales,'Satici');total=sum(x['sales'] for x in result)
        return {**base,'title':'Satıcı Performansı','kpis':[('Aktif satıcı',len(result),'adet'),('Toplam ciro',total,'EUR'),('Ortalama marj',sum(x['profit'] for x in result)/total*100 if total else 0,'%'),('Atanmamış ciro',next((x['sales'] for x in result if x['name']=='Bilinmiyor'),0),'EUR')],'rows':sorted(result,key=lambda x:x['sales'],reverse=True),'rowLabel':'Satıcı'}
    if module=='geography':
        result=aggregate(sales,'Sehir')
        return {**base,'title':'Coğrafi Analiz','kpis':[('Şehir',len(result),'adet'),('Ülke',len({r.get('Ülke') for r in sales if r.get('Ülke')}),'adet'),('Bölgesel ciro',sum(x['sales'] for x in result),'EUR'),('Bilinmeyen şehir',next((x['sales'] for x in result if x['name']=='Bilinmiyor'),0),'EUR')],'rows':sorted(result,key=lambda x:x['sales'],reverse=True),'rowLabel':'Şehir'}
    if module=='pricing_costs':
        products=_product_tags({'analysisDate':max_date.isoformat(), 'persist':False})['products'];result=[{'name':x['name'],'code':x['code'],'sales':x['sales'],'profit':x['profit'],'margin':x['margin'],'price':x['price'],'cost':x['cost'],'replacementCost':x['replacementCost'],'replacementMargin':x['replacementMargin'],'customers':x['customers'],'invoices':x['invoices']} for x in products];risky=[x for x in result if x['replacementMargin'] is not None and x['replacementMargin']<15];known=[x['replacementMargin'] for x in result if x['replacementMargin'] is not None]
        return {**base,'title':'Fiyat ve Maliyet','kpis':[('İncelenen ürün',len(result),'adet'),('Fiyat aksiyonu',len(risky),'adet'),('Riskli ciro',sum(x['sales'] for x in risky),'EUR'),('Ort. yerine koyma marjı',sum(known)/len(known) if known else 0,'%')],'rows':sorted(result,key=lambda x:(x['replacementMargin'] if x['replacementMargin'] is not None else 999)),'rowLabel':'Ürün'}
    if module=='purchasing_balance':
        result=aggregate(purchases,'Malzeme Grubu');total=sum(amount(r) for r in purchases);returned=sum(abs(_float(r.get('Net Satir Tutari'))) for r in purchases if invoice_kind(r)=='purchase_return')
        return {**base,'title':'Satın Alma ve Stok Dengesi','kpis':[('Net satın alma',total,'EUR'),('Alım iadesi',returned,'EUR'),('Ürün',len({r.get('Malzeme Kodu') for r in purchases}),'adet'),('Fatura',len({r.get('Fatura No') for r in purchases}),'adet')],'rows':sorted(result,key=lambda x:x['sales'],reverse=True),'rowLabel':'Kategori','note':'Stok miktarı demo modelinden; satın alma tutarları hareket kaynağından gelir.'}
    if module=='cross_sell':
        baskets=defaultdict(set)
        for r in sales:
            if invoice_kind(r)=='sale' and r.get('Fatura No') and r.get('Malzeme Grubu'):baskets[r['Fatura No']].add(r['Malzeme Grubu'])
        pairs=Counter()
        for items in baskets.values():
            ordered=sorted(items)
            for i,a in enumerate(ordered):
                for b in ordered[i+1:]:pairs[(a,b)]+=1
        result=[{'name':f'{a} + {b}','invoices':n,'support':round(n/len(baskets)*100,1) if baskets else 0,'sales':0,'profit':0,'margin':None,'customers':0,'products':2,'returns':0} for (a,b),n in pairs.most_common(100)]
        return {**base,'title':'Sepet ve Çapraz Satış','kpis':[('Sepet',len(baskets),'adet'),('Ort. kategori',sum(map(len,baskets.values()))/len(baskets) if baskets else 0,'adet'),('Güçlü eşleşme',sum(x['support']>=5 for x in result),'adet'),('Öneri adayı',len(result),'adet')],'rows':result,'rowLabel':'Kategori eşleşmesi','note':'Eşleşmeler aynı faturada görülme sıklığına dayanır; nedensellik iddiası taşımaz.'}
    if module=='forecasting':
        cutoff=max_date-timedelta(days=27);prior_start=cutoff-timedelta(days=28);recent=aggregate([r for r in sales if datetime.fromisoformat(r['Fatura Tarihi']).date()>=cutoff],'Malzeme Grubu');prior={x['name']:x for x in aggregate([r for r in sales if prior_start<=datetime.fromisoformat(r['Fatura Tarihi']).date()<cutoff],'Malzeme Grubu')}
        for x in recent:x['forecast']=round(max(0,x['quantity']*.6+prior.get(x['name'],{}).get('quantity',x['quantity'])*.4),1)
        return {**base,'title':'Öngörüler','demo':True,'kpis':[('4 haftalık talep',sum(x['forecast'] for x in recent),'birim'),('Kategori',len(recent),'adet'),('Yöntem',1,'referans'),('ML yayınlandı',0,'hayır')],'rows':sorted(recent,key=lambda x:x['forecast'],reverse=True),'rowLabel':'Kategori','note':'Referans tahmini: son 28 gün %60, önceki 28 gün %40. ML doğrulanana kadar yayınlanmaz.'}
    raise ValueError('Desteklenmeyen analiz modülü.')


def action_create(data):
    signal_id=str(data.get('signalId') or '')
    with closing(db()) as con:
        signal=con.execute("SELECT s.*,a.id alert_id FROM signal_instances s LEFT JOIN alerts a ON a.signal_id=s.id WHERE s.id=?",(signal_id,)).fetchone()
        if not signal: raise ValueError('Aksiyon oluşturulacak sinyal bulunamadı.')
        existing=con.execute("SELECT id,status FROM actions WHERE signal_id=? AND status IN ('open','in_progress') ORDER BY created DESC LIMIT 1",(signal_id,)).fetchone()
        if existing: return {'id':existing['id'],'status':existing['status'],'existing':True}
        now=datetime.now().astimezone().isoformat(); ident=uuid.uuid4().hex
        title=str(data.get('title') or signal['title']).strip()[:160]
        description=str(data.get('description') or signal['recommended_action']).strip()[:1200]
        priority=str(data.get('priority') or signal['severity'])
        if priority not in SEVERITY_CATALOG: raise ValueError('Geçersiz aksiyon önceliği.')
        owner=str(data.get('owner') or 'Atanmamış').strip()[:120] or 'Atanmamış'
        due=str(data.get('dueDate') or '').strip() or None
        if due:
            try: datetime.fromisoformat(due)
            except ValueError: raise ValueError('Geçersiz termin tarihi.')
        con.execute("INSERT INTO actions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(ident,signal['alert_id'],signal_id,signal['entity_type'],signal['entity_id'],title,description,priority,'open',owner,due,None,None,now,now))
        con.execute("INSERT INTO action_events(action_id,event_type,to_status,note,created) VALUES(?,?,?,?,?)",(ident,'created','open','Sinyalden aksiyon oluşturuldu.',now))
        if signal['alert_id']: con.execute("UPDATE alerts SET status='acknowledged',acknowledged_at=? WHERE id=?",(now,signal['alert_id']))
        con.commit()
    return {'id':ident,'status':'open'}


def action_update(data):
    ident=str(data.get('id') or ''); status=str(data.get('status') or '')
    allowed=('open','in_progress','completed','rejected')
    if status not in allowed: raise ValueError('Geçersiz aksiyon durumu.')
    outcome=str(data.get('outcome') or '') or None
    if status in ('completed','rejected') and outcome not in ('converted','no_result','postponed','unmeasurable'):
        raise ValueError('Aksiyon kapanırken sonuç seçilmelidir.')
    impact=data.get('realizedImpact'); impact=float(impact) if impact not in (None,'') else None
    note=str(data.get('note') or '').strip()[:1200]; now=datetime.now().astimezone().isoformat()
    with closing(db()) as con:
        current=con.execute("SELECT * FROM actions WHERE id=?",(ident,)).fetchone()
        if not current: raise ValueError('Aksiyon bulunamadı.')
        con.execute("UPDATE actions SET status=?,outcome=?,realized_impact=?,updated=? WHERE id=?",(status,outcome,impact,now,ident))
        con.execute("INSERT INTO action_events(action_id,event_type,from_status,to_status,note,created) VALUES(?,?,?,?,?,?)",(ident,'status_changed',current['status'],status,note,now))
        con.commit()
    return {'id':ident,'status':status}


def stock_analysis(data):
    """Deterministic demo inventory derived from normalized product demand."""
    product_data = _product_tags({**data, 'persist': False})
    if product_data.get('status') != 'ready':
        return {'status':'no_data','products':[],'summary':{}}
    with closing(db()) as con:
        stock = con.execute("SELECT id FROM batches WHERE kind='stock' ORDER BY created DESC LIMIT 1").fetchone()
        movement = con.execute("SELECT id FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1").fetchone()
        stock_rows = [json.loads(r['converted']) for r in con.execute(
            "SELECT converted FROM records WHERE kind='stock' AND batch_id=?", (stock['id'],))] if stock else []
        movement_rows = [json.loads(r['converted']) for r in con.execute(
            "SELECT converted FROM records WHERE kind='movement' AND batch_id=?", (movement['id'],))] if movement else []

    # The stock upload is a packaging catalogue for this demo. Its quantities,
    # warehouses and monetary totals are deliberately not treated as inventory.
    stock_map = defaultdict(lambda:{'content':None,'name':'','category':'Tanımsız'})
    for r in stock_rows:
        code = str(r.get('Kodu') or '').strip()
        if not code: continue
        s=stock_map[code]
        s['name'] = r.get('Aciklamasi') or s['name'] or code
        s['category'] = r.get('Malzeme Grubu') or s['category']
        content=_float(r.get('Icerik'))
        if content>0: s['content']=content

    products=product_data['products']
    total_sales=sum(max(0,p['sales']) for p in products) or 1
    cumulative=0.0; abc={}
    for p in sorted(products,key=lambda x:x['sales'],reverse=True):
        before=cumulative/total_sales*100; cumulative += max(0,p['sales'])
        abc[p['code']]='A' if before<80 else 'B' if before<95 else 'C'

    analysis_date=datetime.fromisoformat(product_data['analysisDate']).date()
    current_start=analysis_date-timedelta(days=89)
    previous_start=current_start-timedelta(days=90)
    demand=defaultdict(lambda:{'currentBase':0.0,'previousBase':0.0,'cost':0.0,'replacementCost':0.0,
      'costBase':0.0,'contentCounts':Counter()})
    def invoice_kind(r):
        value=normalize(str(r.get('Fatura Türü') or ''))
        if value in ('satis','satis faturasi'):return 'sale'
        if value in ('satis iadesi','satis iade faturasi'):return 'return'
        return None
    for r in movement_rows:
        kind=invoice_kind(r); code=str(r.get('Malzeme Kodu') or '').strip(); raw_date=r.get('Fatura Tarihi')
        if not kind or not code or not raw_date:continue
        day=datetime.fromisoformat(raw_date).date()
        if day>analysis_date or day<previous_start:continue
        qty=abs(_float(r.get('Miktar'))); content=_float(r.get('Icerik')) or 1.0
        base_qty=qty*content; sign=-1 if kind=='return' else 1
        bucket='currentBase' if day>=current_start else 'previousBase'
        demand[code][bucket]+=sign*base_qty
        if kind=='sale':
            demand[code]['contentCounts'][(str(r.get('Birim') or ''),content)]+=qty
            if day>=current_start:
                row_cost=abs(_float(r.get('Satir Maliyeti')))
                replacement_cost=abs(_float(r.get('Maliyet nach letzter EK RE')))
                if row_cost>0:
                    demand[code]['cost']+=row_cost; demand[code]['costBase']+=base_qty
                if replacement_cost>0:demand[code]['replacementCost']+=replacement_cost

    def inferred_content(code):
        source=stock_map.get(code)
        if source and source.get('content'):return source['content'],'Stok tablosu'
        counts=demand[code]['contentCounts']
        package=[(count,content) for (unit,content),count in counts.items() if normalize(unit)=='pk' and content>0]
        choices=package or [(count,content) for (_,content),count in counts.items() if content>0]
        return (max(choices)[1],'Hareket birimi') if choices else (1.0,'Varsayılan tekil birim')

    def target_days(code,abc_class):
        # Stable pseudo-randomness: the same product/date always creates the same scenario.
        seed=int(hashlib.sha256(f"demo-stock|{analysis_date.isoformat()}|{code}".encode()).hexdigest()[:8],16)
        low,high={'A':(10,42),'B':(20,60),'C':(30,90)}.get(abc_class,(25,60))
        return low+(seed%(high-low+1))
    def status(coverage,daily,quantity):
        if daily<=0:return 'Hareketsiz' if quantity>0 else 'Satış geçmişi yetersiz'
        if coverage<15:return 'Kritik'
        if coverage<30:return 'Düşük'
        if coverage<=60:return 'Dengeli'
        return 'Fazla stok'

    result=[]; seen=set()
    for p in products:
        code=p['code']; seen.add(code); stats=demand[code]; content,content_source=inferred_content(code)
        current_daily_base=max(0,stats['currentBase'])/90
        previous_daily_base=max(0,stats['previousBase'])/90
        daily_base=current_daily_base or previous_daily_base
        daily_packages=daily_base/content if content else 0
        planned_days=target_days(code,abc[code])
        if daily_packages>0:qty=max(1,int(daily_packages*planned_days+.999999))
        else:
            seed=int(hashlib.sha256(f"inactive-stock|{code}".encode()).hexdigest()[:8],16)
            qty=1+(seed%12)
        coverage=qty/daily_packages if daily_packages>0 else None
        base_cost=stats['cost']/stats['costBase'] if stats['costBase'] else 0
        replacement_base_cost=stats['replacementCost']/stats['costBase'] if stats['costBase'] and stats['replacementCost'] else base_cost
        value=qty*content*base_cost
        replacement_value=qty*content*replacement_base_cost
        result.append({'code':code,'name':p['name'],'category':p['category'],'abc':abc[code],
          'source':'demo','quantity':qty,'content':round(content,2),'contentSource':content_source,
          'baseQuantity':round(qty*content,2),'value':round(value,2),
          'replacementValue':round(replacement_value,2),'replacementDelta':round(replacement_value-value,2),
          'dailySales':round(daily_packages,3),'dailyBaseSales':round(daily_base,3),
          'monthlySales':round(daily_packages*30,2),'coverageDays':round(coverage,1) if coverage is not None else None,
          'targetCoverageDays':planned_days,'velocityBasis':'Son 90 gün' if current_daily_base else 'Önceki 90 gün' if previous_daily_base else 'Veri yok',
          'status':status(coverage if coverage is not None else 0,daily_packages,qty),'sales':p['sales'],
          'profit':p['profit'],'margin':p['margin']})
    for code,s in stock_map.items():
        if code in seen:continue
        content=s['content'] or 1.0; seed=int(hashlib.sha256(f"inactive-stock|{code}".encode()).hexdigest()[:8],16); qty=1+(seed%12)
        result.append({'code':code,'name':s['name'],'category':s['category'],'abc':None,'source':'demo',
          'quantity':qty,'content':round(content,2),'contentSource':'Stok tablosu','baseQuantity':round(qty*content,2),
          'value':0,'replacementValue':0,'replacementDelta':0,'dailySales':0,'dailyBaseSales':0,
          'monthlySales':0,'coverageDays':None,'targetCoverageDays':None,
          'velocityBasis':'Veri yok','status':'Hareketsiz',
          'sales':0,'profit':0,'margin':None})
    result.sort(key=lambda x:(x['status']!='Kritik',x['coverageDays'] if x['coverageDays'] is not None else 999999,-x['value']))
    content_from_stock=sum(x['contentSource']=='Stok tablosu' for x in result)
    return {'status':'ready','analysisDate':product_data['analysisDate'],'stockAsOf':product_data['analysisDate'],
      'method':{'windowDays':90,'model':'deterministic_demo','contentFromStock':content_from_stock,
        'contentInferred':len(result)-content_from_stock,'coverageBands':{'A':[10,42],'B':[20,60],'C':[30,90]}},
      'summary':{'products':len(result),'modeled':len(result),'contentFromStock':content_from_stock,
        'critical':sum(x['status']=='Kritik' for x in result),'excess':sum(x['status']=='Fazla stok' for x in result),
        'inactive':sum(x['status']=='Hareketsiz' for x in result),'value':round(sum(x['value'] for x in result),2)},
      'products':result}


def product_detail(data):
    """Time-series and commercial evidence for one product at the selected analysis date."""
    code = str(data.get('code') or '').strip()
    if not code:
        raise ValueError('Ürün kodu gerekli.')
    with closing(db()) as con:
        movement = con.execute("SELECT id FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1").fetchone()
        stock = con.execute("SELECT id FROM batches WHERE kind='stock' ORDER BY created DESC LIMIT 1").fetchone()
        if not movement:
            return {'status':'no_data'}
        rows = []
        for stored in con.execute("SELECT source_line, converted FROM records WHERE kind='movement' AND batch_id=?", (movement['id'],)):
            parsed = json.loads(stored['converted']); parsed['_sourceLine'] = stored['source_line']; rows.append(parsed)
        stock_rows = [json.loads(r['converted']) for r in con.execute(
            "SELECT converted FROM records WHERE kind='stock' AND batch_id=?", (stock['id'],))] if stock else []

    def invoice_kind(r):
        value = normalize(str(r.get('Fatura Türü') or ''))
        if value in ('satis','satis faturasi'): return 'sale'
        if value in ('satis iadesi','satis iade faturasi'): return 'return'
        return None

    selected = [r for r in rows if str(r.get('Malzeme Kodu') or '') == code and invoice_kind(r) and r.get('Fatura Tarihi')]
    if not selected:
        return {'status':'not_found'}
    all_dates = [datetime.fromisoformat(r['Fatura Tarihi']).date() for r in rows if invoice_kind(r) and r.get('Fatura Tarihi')]
    max_date = max(all_dates)
    min_date = min(all_dates)
    try: analysis_date = datetime.fromisoformat(str(data.get('analysisDate') or '')).date()
    except ValueError: analysis_date = max_date
    analysis_date = min(max(analysis_date, min_date), max_date)
    start = analysis_date - timedelta(days=179)
    current_start = analysis_date - timedelta(days=89)
    month_start = date(start.year, start.month, 1)
    buckets = {}
    return_customers = defaultdict(lambda:{'name':'Bilinmiyor','amount':0.0,'invoices':set()})
    buying_customers = defaultdict(lambda:{'name':'Bilinmiyor','amount':0.0,'quantity':0.0,'invoices':set()})
    product_name, category, unit = code, 'Tanımsız', '—'
    for r in selected:
        d = datetime.fromisoformat(r['Fatura Tarihi']).date()
        if d > analysis_date: continue
        product_name = r.get('Malzeme Aciklamasi') or product_name
        category = r.get('Malzeme Grubu') or category
        unit = r.get('Birim') or unit
        if invoice_kind(r) == 'return' and current_start <= d <= analysis_date:
            customer = str(r.get('Müsteri Kodu') or 'Bilinmiyor')
            rc = return_customers[customer]
            rc['name'] = r.get('Müsteri Ünvani') or customer
            rc['amount'] += abs(_float(r.get('Net Satir Tutari')))
            if r.get('Fatura No'): rc['invoices'].add(r['Fatura No'])
        if invoice_kind(r) == 'sale' and current_start <= d <= analysis_date:
            customer = str(r.get('Müsteri Kodu') or 'Bilinmiyor')
            bc = buying_customers[customer]
            bc['name'] = r.get('Müsteri Ünvani') or customer
            bc['amount'] += abs(_float(r.get('Net Satir Tutari')))
            bc['quantity'] += abs(_float(r.get('Miktar')))
            if r.get('Fatura No'): bc['invoices'].add(r['Fatura No'])
        if d < month_start: continue
        key = f'{d.year:04d}-{d.month:02d}'
        b = buckets.setdefault(key, {'sales':0.0,'returns':0.0,'qty':0.0,'cost':0.0,'profit':0.0,'replacement':0.0,'customers':set(),'prices':[]})
        amount, qty = abs(_float(r.get('Net Satir Tutari'))), abs(_float(r.get('Miktar')))
        if invoice_kind(r) == 'return':
            b['returns'] += amount
        else:
            b['sales'] += amount; b['qty'] += qty
            if r.get('Müsteri Kodu'): b['customers'].add(r['Müsteri Kodu'])
            if qty: b['prices'].append(amount/qty)
        zero_cost = _float(r.get('Maliyet Fiyati')) == 0 or _float(r.get('Satir Maliyeti')) == 0
        if not zero_cost:
            sign = -1 if invoice_kind(r) == 'return' else 1
            b['cost'] += sign * abs(_float(r.get('Satir Maliyeti')))
            b['profit'] += _float(r.get('Satir Kari')) if sign > 0 else -abs(_float(r.get('Satir Kari')))
            b['replacement'] += sign * abs(_float(r.get('Maliyet nach letzter EK RE')))

    points=[]
    cursor=month_start
    while cursor <= analysis_date:
        key=f'{cursor.year:04d}-{cursor.month:02d}'; b=buckets.get(key, {'sales':0.0,'returns':0.0,'qty':0.0,'cost':0.0,'profit':0.0,'replacement':0.0,'customers':set(),'prices':[]})
        net=b['sales']-b['returns']; qty=b['qty']
        points.append({'period':key,'sales':round(net,2),'quantity':round(qty,2),'price':round(b['sales']/qty,4) if qty else None,
          'cost':round(b['cost']/qty,4) if qty and b['cost'] else None,'margin':round(b['profit']/net*100,2) if net and b['cost'] else None,
          'replacementMargin':round((net-b['replacement'])/net*100,2) if net and b['replacement'] else None,
          'customers':len(b['customers']),'returns':round(b['returns'],2)})
        cursor = date(cursor.year + (cursor.month == 12), 1 if cursor.month == 12 else cursor.month + 1, 1)

    corridor_rows=[]
    for r in selected:
        d=datetime.fromisoformat(r['Fatura Tarihi']).date(); qty=abs(_float(r.get('Miktar')))
        amount=abs(_float(r.get('Net Satir Tutari')))
        if start <= d <= analysis_date and invoice_kind(r)=='sale' and qty and amount > 0 and (r.get('Birim') or '—') == unit:
            corridor_rows.append((amount/qty, str(r.get('Müsteri Kodu') or '')))
    prices=sorted(p for p,_ in corridor_rows); customers={c for _,c in corridor_rows if c}
    eligible=len(prices)>=8 and len(customers)>=3
    def quantile(vals, q):
        if not vals:return None
        pos=(len(vals)-1)*q; lo=int(pos); hi=min(lo+1,len(vals)-1); return vals[lo]+(vals[hi]-vals[lo])*(pos-lo)
    corridor={'eligible':eligible,'rows':len(prices),'customers':len(customers),'q1':round(quantile(prices,.25),4) if eligible else None,
      'q3':round(quantile(prices,.75),4) if eligible else None,'min':round(min(prices),4) if prices else None,'max':round(max(prices),4) if prices else None}

    stock_items=[r for r in stock_rows if str(r.get('Kodu') or '')==code]
    stock_qty=sum(_float(r.get('Stok Miktari')) for r in stock_items)
    stock_value=sum(_float(r.get('Stok Degeri')) for r in stock_items)
    stock_info={'quantity':round(stock_qty,2),'value':round(stock_value,2),'content':next((_float(r.get('Icerik')) for r in stock_items if r.get('Icerik') is not None),None),
      'cost':next((_float(r.get('Maliyet Fiyati')) for r in stock_items if r.get('Maliyet Fiyati') is not None),None),
      'warehouses':len({r.get('Ambar') for r in stock_items if r.get('Ambar')})}
    top_returns=sorted(({'code':c,'name':v['name'],'amount':round(v['amount'],2),'invoices':len(v['invoices'])} for c,v in return_customers.items()),key=lambda x:x['amount'],reverse=True)[:5]
    top_customers=sorted(({'code':c,'name':v['name'],'amount':round(v['amount'],2),'quantity':round(v['quantity'],2),
      'averagePrice':round(v['amount']/v['quantity'],4) if v['quantity'] else None,'invoices':len(v['invoices'])} for c,v in buying_customers.items()),key=lambda x:x['amount'],reverse=True)
    transactions=[]
    for r in selected:
        d=datetime.fromisoformat(r['Fatura Tarihi']).date()
        if current_start <= d <= analysis_date:
            qty=abs(_float(r.get('Miktar'))); amount=abs(_float(r.get('Net Satir Tutari')))
            transactions.append({'line':r.get('_sourceLine'),'date':r['Fatura Tarihi'],'invoice':r.get('Fatura No') or '—',
              'type':'İade' if invoice_kind(r)=='return' else 'Satış','customerCode':r.get('Müsteri Kodu') or '—',
              'customer':r.get('Müsteri Ünvani') or r.get('Müsteri Kodu') or 'Bilinmiyor','quantity':round(qty,2),
              'unitPrice':round(amount/qty,4) if qty else None,'net':round(amount,2),
              'unitCost':round(abs(_float(r.get('Satir Maliyeti')))/qty,4) if qty and _float(r.get('Satir Maliyeti')) else None})
    transactions.sort(key=lambda x:(x['date'],x['invoice']),reverse=True)
    from analysis.predictive_engine import predict_product_target_customers
    target_customers = predict_product_target_customers(code, analysis_date, rows, stock_qty=stock_qty, max_results=8)
    return {'status':'ready','analysisDate':analysis_date.isoformat(),'product':{'code':code,'name':product_name,'category':category,'unit':unit},
      'series':points,'corridor':corridor,'stock':stock_info,'topReturnCustomers':top_returns,'customers':top_customers,
      'targetCustomers':target_customers,
      'transactions':transactions[:100],'transactionCount':len(transactions)}

def main(data):
    action = data.get('action')
    if action in {'case_list', 'case_detail', 'case_demo_prepare', 'case_evaluate', 'case_mutate', 'case_from_entity'}:
        from analysis.decision_cases import dispatch
        return dispatch(data)
    if action == 'inspect': return inspect(data)
    if action == 'analyze': return analyze(data)
    if action == 'commit': return commit(data)
    if action == 'list': return listing()
    if action == 'report': return get_report(data)
    if action == 'export': return export_issues(data)
    if action == 'schema': return {'stock': STOCK, 'movement': MOVEMENT}
    if action == 'cockpit': return cockpit(data)
    if action == 'signals': return signals({**data, 'persist': False})
    if action == 'decision_catalog': return decision_catalog(data)
    if action == 'decision_center': return decision_center(data)
    if action == 'module_analytics': return module_analytics(data)
    if action in {'customer_analytics', 'customer_detail'}:
        from analysis.customer_analytics import customer_analytics, customer_detail
        return customer_analytics(data) if action == 'customer_analytics' else customer_detail(data)
    if action in {'pricing_analytics', 'seller_analytics'}:
        from analysis.commercial_analytics import pricing_analytics, seller_analytics
        return pricing_analytics(data) if action == 'pricing_analytics' else seller_analytics(data)
    if action == 'opportunity_analytics':
        from analysis.opportunity_analytics import opportunity_analytics
        return opportunity_analytics(data)
    if action == 'forecasting_analytics':
        from analysis.forecasting_analytics import forecasting_analytics
        return forecasting_analytics(data)
    if action in {'sales_profitability', 'executive_snapshot'}:
        from analysis.profitability_analytics import sales_profitability, executive_snapshot
        return sales_profitability(data) if action == 'sales_profitability' else executive_snapshot(data)
    if action in {'unified_decision_center', 'signal_review', 'enhanced_action_update'}:
        from analysis.decision_workflow import unified_center, review_signal, update_action
        if action == 'unified_decision_center': return unified_center(data)
        if action == 'signal_review': return review_signal(data)
        return update_action(data)
    if action == 'action_create': return action_create(data)
    if action == 'action_update': return action_update(data)
    if action == 'stock_analysis': return stock_analysis(data)
    if action == 'product_detail': return product_detail(data)
    raise ValueError('Desteklenmeyen işlem.')


if __name__ == '__main__':
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(json.dumps({'ok': True, 'data': main(json.load(sys.stdin))}, ensure_ascii=False))
    except (ValueError, OSError, KeyError, sqlite3.Error) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
    except Exception:
        print(json.dumps({'ok': False, 'error': 'İşlem tamamlanamadı. Kaynak dosyayı ve aktarım ayarlarını kontrol edin.'}, ensure_ascii=False))
