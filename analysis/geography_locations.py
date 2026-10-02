"""Offline conservative country/city matching; never infer a missing country."""
import json
import gzip
import unicodedata
from functools import lru_cache
from pathlib import Path

def fold(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(value or '').replace('ı','i').casefold()) if not unicodedata.combining(c)).strip()

@lru_cache(maxsize=1)
def index():
    data=json.loads(Path(__file__).with_name('places.json').read_text(encoding='utf-8'))
    countries={fold(a):c['code'] for c in data['countries'] for a in c['aliases']}
    countries.update({'hollanda':'NLD','avusturya':'AUT','almanya':'DEU'})
    places={}
    for city in data['cities']:
        for alias in city['aliases']:
            key=(city['country'],fold(alias))
            point=(city['lat'],city['lon'])
            places.setdefault(key,set()).add(point)
    return countries,places

@lru_cache(maxsize=32)
def city_index(code):
    path=Path(__file__).with_name("geocities") / f"{code}.json.gz"
    return json.loads(gzip.decompress(path.read_bytes())) if path.exists() else {}

def locate(country,city):
    countries,places=index()
    code=countries.get(fold(country))
    gazetteer=city_index(code) if code else {}
    key=fold(city)
    if key in gazetteer:
        point=gazetteer[key]
        return {'countryCode':code,'latitude':point[0] if point else None,'longitude':point[1] if point else None,'locationStatus':'matched' if point else 'ambiguous'}
    points=places.get((code,key),set())
    if len(points)==1:
        lat,lon=next(iter(points))
        return {'countryCode':code,'latitude':lat,'longitude':lon,'locationStatus':'matched'}
    return {'countryCode':code,'latitude':None,'longitude':None,'locationStatus':'ambiguous' if len(points)>1 else 'unmatched'}
