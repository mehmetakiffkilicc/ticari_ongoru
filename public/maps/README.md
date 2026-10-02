# Harita verisi

Ülke sınırları: Natural Earth 1:110m Admin 0 Countries. Şehir merkezleri: Natural Earth 1:10m Populated Places (7.342 yerleşim). Public domain.

Kaynak: https://www.naturalearthdata.com/downloads/ ve https://github.com/nvkelso/natural-earth-vector/tree/master/geojson
Alınma tarihi: 2026-09-23. `scripts/prepare_maps.py` kaynak GeoJSON dosyalarını küçültür. Dünya geometrisi `public/maps/world.json`, ad eşleştirme sözlüğü `analysis/places.json` içindedir.

Şehirler ülke ve tam ad/yerel ad eşleştirmesiyle bulunur. Belirsiz veya sözlükte bulunmayan yerler uydurma koordinata yerleştirilmez; tabloda ve eşleşmeyenler listesinde korunur. Noktalar şehir merkezidir, il sınırı veya müşteri adresi değildir. Çalışma anında dış harita/geocoding isteği gönderilmez.

## Genişletilmiş şehir sözlüğü

GeoNames `cities1000.zip`: https://download.geonames.org/export/dump/cities1000.zip (2026-09-23). GeoNames verisi [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/) lisansıyla kullanılır. Kaynak/atıf: https://www.geonames.org/ . Adlar normalleştirildi, ülkeye göre ayrıldı ve sıkıştırıldı; aynı ülke/adın farklı koordinatları belirsiz bırakıldı.

`scripts/prepare_geocities.py` indirilmiş arşivden `analysis/geocities/*.json.gz` sözlüklerini oluşturur. Bu sözlükte bulunmayan adlar için Natural Earth şehir merkezleri yedektir. Ülke kodları Natural Earth dünya kapsamıyla eşlenir. Çalışma anında dış isteğe gerek yoktur.
