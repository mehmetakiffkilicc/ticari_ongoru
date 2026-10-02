"""Build a separate presentation copy. Read originals only; never copy raw files/history.

Run: python -m scripts.prepare_anonymous
Output: DATA_DIR/anonymous (must not already exist).
Relationships and row counts are retained; all identities, dates and measures are replaced.
"""
import base64
import csv
import io
import json
import os
import random
import sqlite3
import tempfile
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
from analysis import engine


def build(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination == source or source.is_relative_to(destination):
        raise ValueError('Output must be separate from the original data.')
    if destination.exists():
        raise ValueError('Output already exists; refusing to overwrite it.')
    # mode=ro also refuses to silently create an empty original database.
    with closing(sqlite3.connect((source / 'center.sqlite').as_uri() + '?mode=ro', uri=True)) as con:
        selected = {}
        for kind in engine.KINDS:
            batch = con.execute('SELECT id FROM batches WHERE kind=? ORDER BY created DESC LIMIT 1', (kind,)).fetchone()
            selected[kind] = [json.loads(r[0]) for r in con.execute(
                'SELECT converted FROM records WHERE batch_id=?', (batch[0],))] if batch else []
    rng = random.SystemRandom()
    maps = {}
    def alias(group, value):
        # Mapping is kept only in memory and never published or saved.
        key = str(value or '')
        table = maps.setdefault(group, {})
        if key not in table:
            table[key] = f'{group}-{len(table) + 1:05d}'
        return table[key]
    all_rows = [(kind, row) for kind, rows in selected.items() for row in rows]
    rng.shuffle(all_rows)
    prices, dates, places = {}, {}, {}
    generated = {kind: [] for kind in engine.KINDS}
    for kind, row in all_rows:
        product = alias('URUN', row.get('Kodu' if kind == 'stock' else 'Malzeme Kodu'))
        if product not in prices:
            prices[product] = (rng.randint(250, 4500) / 100, rng.choice([1, 6, 12]))
        cost, content = prices[product]
        category = alias('GRUP', row.get('Malzeme Grubu'))
        warehouse = alias('DEPO', row.get('Ambar'))
        qty = rng.randint(2, 180 if kind == 'stock' else 24)
        common = {'Ambar': warehouse, 'Malzeme Grubu': category, 'Icerik': content, 'Maliyet Fiyati': cost}
        if kind == 'stock':
            generated[kind].append({**common, 'Kodu': product, 'Aciklamasi': f'Örnek {product}',
                'Stok Miktari': qty, 'Stok Degeri': round(qty * cost, 2),
                'Bestand nach letzter EK RE': round(qty * cost, 2),
                'Stok Degeri (KDV Dahil)': round(qty * cost * 1.2, 2)})
            continue
        customer = alias('MUSTERI', row.get('Müsteri Kodu') or row.get('Müsteri Ünvani'))
        invoice = alias('FATURA', row.get('Fatura No'))
        if invoice not in dates:
            dates[invoice] = date(2023, 1, 2) + timedelta(days=rng.randint(0, 728))
        day = dates[invoice]
        if customer not in places:
            places[customer] = rng.choice([('Berlin', 'DE'), ('Paris', 'FR'), ('Ankara', 'TR')])
        city, country = places[customer]
        invoice_type = engine.invoice_kind(row) or 'sale'
        if invoice_type in {'return', 'purchase_return'}:
            qty = -qty
        price = round(cost * rng.uniform(.85, 1.65), 2)
        net, total_cost = round(qty * price, 2), round(qty * cost, 2)
        profit = round(net - total_cost, 2)
        generated[kind].append({**common, 'Satici': alias('TEMSILCI', row.get('Satici')),
            'Fatura Türü': {'sale': 'Satış Faturası', 'return': 'Satış İade Faturası',
                'purchase': 'Satın Alma Faturası', 'purchase_return': 'Satın Alma İade Faturası'}[invoice_type],
            'Fatura Tarihi': day.isoformat(), 'Fatura No': invoice,
            'Malzeme Kodu': product, 'Malzeme Aciklamasi': f'Örnek {product}', 'Birim': 'ST',
            'Miktar': qty, 'Birim Fiyati': price, 'Indirim Tutari': 0, 'Net Satir Tutari': net,
            'Satis Fiyati': price, 'Satir Maliyeti': total_cost, 'Satir Marji': round(profit / net * 100, 2),
            'Satir Kari': profit, 'Maliyet nach letzter EK RE': cost,
            'Kar nach letzter EK RE': profit, 'Marj nach letzter EK RE': round(profit / net * 100, 2),
            'Müsteri Kodu': customer, 'Müsteri Ünvani': f'Örnek {customer}',
            'Posta Kodu': '00000', 'Sehir': city, 'Ülke': country, 'Sevkiyat Adresi': 'Örnek adres',
            'Ay': day.month, 'Yil': day.year, 'Cari Tipi': 'Örnek', 'PrimVar': 'Hayır'})
    destination.parent.mkdir(parents=True, exist_ok=True)
    old_root = engine.ROOT
    counts = {}
    # Build off to the side; publish only a complete dataset. Temporary files contain synthetic data only.
    with tempfile.TemporaryDirectory(prefix='anonymous-build-', dir=destination.parent) as work:
        engine.ROOT = Path(work) / 'ready'
        try:
            for kind, rows in generated.items():
                if not rows:
                    counts[kind] = 0
                    continue
                output = io.StringIO(newline='')
                writer = csv.DictWriter(output, fieldnames=engine.KINDS[kind])
                writer.writeheader()
                writer.writerows(rows)
                info = engine.inspect({'kind': kind, 'name': f'ornek-{kind}.csv', 'encoding': 'utf-8-sig',
                    'file': base64.b64encode(output.getvalue().encode()).decode()})
                report = engine.analyze({'id': info['id'], 'mapping': info['mapping'], 'decimal': '.',
                    'dateFormat': 'iso', 'snapshot': '2024-12-30T12:00:00' if kind == 'stock' else ''})
                if report['accepted'] != len(rows):
                    raise ValueError('Synthetic records failed validation.')
                engine.commit({'id': info['id'], 'acknowledge': True})
                counts[kind] = len(rows)
            from analysis import decision_cases
            decision_cases.seed({'scope': 'demo'})
            (engine.ROOT / 'privacy.json').write_text(json.dumps({'version': 1, 'syntheticMeasures': True}), encoding='utf-8')
            engine.ROOT.rename(destination)
        finally:
            engine.ROOT = old_root
    return counts


if __name__ == '__main__':
    base = Path(os.environ.get('DATA_DIR', Path(__file__).resolve().parents[1] / 'data'))
    print(json.dumps(build(base, base / 'anonymous')))
