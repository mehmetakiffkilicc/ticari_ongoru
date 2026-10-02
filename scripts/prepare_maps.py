"""Prepare offline, public-domain Natural Earth assets from downloaded GeoJSON."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
world = json.loads((root/'test-results/world-source.json').read_text(encoding='utf-8'))
cities = json.loads((root/'test-results/cities-source.json').read_text(encoding='utf-8'))
def names(p, keys):
    return list(dict.fromkeys(str(p[k]) for k in keys if p.get(k) and str(p[k]) != '-99'))
countries=[]
for f in world['features']:
    p=f['properties']
    countries.append({'code':p['ADM0_A3'],'name':p['NAME_TR'],'aliases':names(p,['NAME','NAME_TR','NAME_EN','NAME_DE','NAME_LONG','ISO_A2','ISO_A2_EH','ISO_A3','ADM0_A3']), 'geometry':f['geometry']})
(root/'public/maps/world.json').write_text(json.dumps(countries,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
places=[]
for f in cities['features']:
    p=f['properties']
    places.append({'country':p['ADM0_A3'],'name':p['NAME'],'aliases':names(p,['NAME','NAMEASCII','NAME_TR','NAME_EN','NAME_DE','NAME_FR','NAME_NL']), 'lon':round(f['geometry']['coordinates'][0],4),'lat':round(f['geometry']['coordinates'][1],4)})
(root/'analysis/places.json').write_text(json.dumps({'countries':[{k:v for k,v in c.items() if k!='geometry'} for c in countries],'cities':places},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
