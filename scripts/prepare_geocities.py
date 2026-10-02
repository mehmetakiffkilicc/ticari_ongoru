"""Build per-country offline GeoNames cities1000 name indexes (CC BY 4.0)."""
import gzip,json,zipfile
from pathlib import Path
from collections import defaultdict
from analysis.geography_locations import fold
root=Path(__file__).resolve().parents[1]
countries=json.loads((root/'analysis/places.json').read_text(encoding='utf-8'))['countries']
codes={a.upper():c['code'] for c in countries for a in c['aliases'] if len(a)==2}
indexes=defaultdict(dict)
with zipfile.ZipFile(root/'test-results/cities1000.zip') as z:
    for line in z.read('cities1000.txt').decode('utf-8').splitlines():
        r=line.split('\t');country=codes.get(r[8])
        if not country:continue
        point=[round(float(r[4]),4),round(float(r[5]),4)]
        for name in set([r[1],r[2],*r[3].split(',')]):
            if not name:continue
            key=fold(name);old=indexes[country].get(key,point)
            indexes[country][key]=point if old==point else None
out=root/'analysis/geocities';out.mkdir(exist_ok=True)
for country,entries in indexes.items():
    (out/f'{country}.json.gz').write_bytes(gzip.compress(json.dumps(entries,ensure_ascii=False,separators=(',',':')).encode('utf-8'),mtime=0))
print('Country indexes:',len(indexes),'Names:',sum(map(len,indexes.values())))
