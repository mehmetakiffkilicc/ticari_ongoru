"""
Fetch and prepare region (Admin-1 / province / department) polygons
for France, Germany, Turkey, Belgium, Luxembourg.
Saves optimized public/maps/regions.json
"""
import urllib.request
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out_file = root / 'public/maps/regions.json'

regions = []

# 1. France Departements
print("Fetching France departments...")
url_fr = 'https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson'
try:
    with urllib.request.urlopen(url_fr) as r:
        data_fr = json.loads(r.read().decode('utf-8'))
        for f in data_fr.get('features', []):
            p = f['properties']
            regions.append({
                'country': 'FRA',
                'name': p.get('nom', ''),
                'code': p.get('code', ''),
                'geometry': f['geometry']
            })
    print(f"Loaded {len(regions)} France departments.")
except Exception as e:
    print("France error:", e)

# 2. Germany Kreise (Districts / Cities)
print("Fetching Germany districts...")
url_de = 'https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/master/4_kreise/4_niedrig.geo.json'
try:
    with urllib.request.urlopen(url_de) as r:
        data_de = json.loads(r.read().decode('utf-8'))
        count_before = len(regions)
        for f in data_de.get('features', []):
            p = f['properties']
            regions.append({
                'country': 'DEU',
                'name': p.get('NAME_3') or p.get('NAME_2') or p.get('NAME_1') or '',
                'code': str(p.get('CCA_2') or p.get('ID_2') or ''),
                'geometry': f['geometry']
            })
    print(f"Loaded {len(regions) - count_before} Germany districts.")
except Exception as e:
    print("Germany error:", e)

# 3. Turkey Provinces (81 İl)
print("Fetching Turkey provinces...")
url_tr = 'https://raw.githubusercontent.com/cihadturhan/tr-geojson/master/geo/tr-cities-utf8.json'
try:
    with urllib.request.urlopen(url_tr) as r:
        data_tr = json.loads(r.read().decode('utf-8'))
        count_before = len(regions)
        for f in data_tr.get('features', []):
            p = f['properties']
            regions.append({
                'country': 'TUR',
                'name': p.get('name', ''),
                'code': str(p.get('id', '')),
                'geometry': f['geometry']
            })
    print(f"Loaded {len(regions) - count_before} Turkey provinces.")
except Exception as e:
    print("Turkey error:", e)

# 4. Belgium & Luxembourg
try:
    with urllib.request.urlopen('https://raw.githubusercontent.com/johan/world.geo.json/master/countries/BEL.geo.json') as r:
        d = json.loads(r.read().decode('utf-8'))
        for f in d.get('features', []):
            regions.append({'country': 'BEL', 'name': 'Belçika', 'code': 'BEL', 'geometry': f['geometry']})
    with urllib.request.urlopen('https://raw.githubusercontent.com/johan/world.geo.json/master/countries/LUX.geo.json') as r:
        d = json.loads(r.read().decode('utf-8'))
        for f in d.get('features', []):
            regions.append({'country': 'LUX', 'name': 'Lüksemburg', 'code': 'LUX', 'geometry': f['geometry']})
    print("Loaded BEL & LUX.")
except Exception as e:
    print("BEL/LUX error:", e)

def round_coords(coords):
    if not coords:
        return coords
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], 2), round(coords[1], 2)]
    return [round_coords(c) for c in coords]

print("Optimizing geometries...")
for r in regions:
    geom = r['geometry']
    geom['coordinates'] = round_coords(geom['coordinates'])

out_file.parent.mkdir(parents=True, exist_ok=True)
out_file.write_text(json.dumps(regions, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
size_kb = out_file.stat().st_size / 1024
print(f"Saved {len(regions)} regions to {out_file} ({size_kb:.1f} KB)")
