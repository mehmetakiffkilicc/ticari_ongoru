# Ticari Öngörü — Veri Merkezi

React / Next.js arayüzü, Node.js API katmanı ve Python/SQLite motoruyla yerel ticari karar demosu. Veri → Etiket → Sinyal → İçgörü → Kullanıcı onayı → Aksiyon → Geri bildirim hattını sürümlü karar dosyalarında gösterir. Uzman analizler ve CSV kalite akışı korunur.

## Anonim sunum ve asıl veriler

Uygulama varsayılan olarak `data/anonymous` içindeki ayrı sunum kopyasını kullanır. Asıl `data/center.sqlite`, ham CSV dosyaları, aktarım raporları ve karar geçmişi değiştirilmez. Anonim kopya yoksa boş veri ekranı açılır; asıl verilere otomatik dönüş yapılmaz.

Yereldeki veriden sunum kopyasını bir kez hazırlayın:

```powershell
python -m scripts.prepare_anonymous
npm run dev
```

İsimler, müşteri/ürün/fatura kodları, depo ve temsilciler takma değerlerle değiştirilir. Tarihler, konumlar, satış tutarları, maliyetler ve stok miktarları kaynak değerlerden bağımsız üretilir. Ham dosyalar ve eski karar/not geçmişi kopyalanmaz; raporlar örnek kayıtlardan yeniden oluşturulur. Eşleme tablosu kaydedilmez. Kopya zaten varsa komut üzerine yazmayı reddeder.

Satır sayıları ve müşteri–ürün ilişkileri korunur; bu sunum kopyası istatistiksel anonimlik garantisi vermez. Analizler ve öneriler örnek değerlerden hesaplanır, gerçek ticari kararlar için kullanılamaz. Kopya da Git dışında tutulur.

Anonim sunumda CSV yükleme/onaylama sunucuda kapalıdır. API yanıtları ve dışa aktarımlar yalnız sunum kopyasından gelir. Hazır dokuz karar senaryosu tamamen kurgusaldır.

Asıl verilere yalnız yerel, özel kullanım için dönmek gerektiğinde `.env.local` içinde `APP_DATA_MODE=original` ayarlayıp sunucuyu yeniden başlatın. Varsayılan `APP_DATA_MODE=anonymous` değeridir; tarayıcıdan gerçek verilere geçiş düğmesi yoktur. `DATA_DIR` kullanılıyorsa sunum kopyası bu klasörün `anonymous` alt dizinine yazılır. Mod değişiminden sonra açık sekmeleri yenileyin.

## Karar demosunu gösterme

1. Karar Özeti → **Dokuz demo örneğini hazırla**. Üç ticari hikâyenin onay, takip ve sonuç aşamaları ayrı örneklerdir.
2. Onay Kuyruğu → bir varlık → yedi aşamadan kanıtı incele. Öneri kapsamı, sorumlu, termin, başarı ölçütü ve takip süresini düzenle.
3. **Onayla ve görev oluştur → Aksiyonu başlat → Uygulandı olarak kaydet**. Takip tarihi uygulamadan itibaren hesaplanır; erken sonuç girilemez.
4. Sonuçlar ve Geri Bildirim → hazır stok örneğinde **Sonucu değerlendir**. Ölçüm yoksa **Ölçülemedi** seç; varsa önce/sonra, birim, kaynak ve değerlendirme notunu gir.
5. Tamamlanmış örneklerde başarı, kısmi başarı ve sonuç alınamamasını incele. **Sonuçtan yeni inceleme başlat** geçmişi değiştirmeden bağlı bir dosya oluşturur.
6. **Demoyu sıfırla** yalnız demo kararlarını yeniden hazırlar. Gerçek kaynaklar, eski aksiyonlar ve yüklenmiş veriden üretilmiş dosyalar korunur.

Demo saati 30.12.2024'te sabittir; ileri sarma yoktur. Gerçek işlem zamanları ayrıca saklanır. Yeni uygulanan demo aksiyonunda ilerideki takip sonucunu göstermek için ayrı hazır örneğe geçin. Dış sisteme sipariş/fiyat işlemi gönderilmez. Geri bildirim otomatik ölçüm değil, kaynak belirten kullanıcı değerlendirmesidir.

## Yüklenmiş veriden karar üretme

**Veri ve Etiketler** üzerinden mevcut CSV akışını kullanın. Karar merkezinde **Yüklenmiş veri → Veriyi değerlendir** seçin. Aynı kaynak partileri, sinyal ve analiz tarihi için tek dosya oluşur. Yeni analiz önceki kanıtı veya onayı değiştirmez. Ekran okumaları değerlendirme geçmişini ilerletmez.

`decision_cases` tablosunda kapsamı (`demo` / `live`) ayrılmış JSON dosyaları tutulur. Dosya; kanıt anlık görüntüsü, öneri sürümleri, onaylar, görevler, geri bildirim ve olay geçmişini içerir. Yazmalar `BEGIN IMMEDIATE` ve dosya sürüm denetimiyle korunur; eski sekmeden işlem yapılırsa yenileme istenir. Önceki `actions` kayıtları değiştirilmez.

API `/api/data`: `case_list`, `case_detail`, `case_demo_prepare`, `case_evaluate`, `case_mutate`, `case_from_entity`. `case_mutate` için `id`, `scope`, `version`, `operation` kullanılır; işlemler `edit`, `approve`, `reject`, `start`, `apply`, `feedback`, `reopen`. `case_from_entity`, `scope: live`, `entityType: product|customer`, `code`, `analysisDate`, `description`, `successMetric` alır. Sunucuda doğrulanan profil kanıtıyla onay bekleyen dosya oluşturur; aynı kaynak, tarih ve öneriyle tekrar gönderim dosyayı çoğaltmaz. İstemci tipleri `app/decision-types.ts`; sunucu doğrulaması `analysis/decision_cases.py`.

## Detaylı incelemeden karara

Karar Özeti'ndeki **Müşteri 360**, **Ürün 360** ve **Tüm analizler** kısayolları ayrıntıya açılır. **Ticari İnceleme** dört grupta 12 uzman analize erişim sağlar.

- Müşteri profili: son 90 günün ciro/kârı, tüm geçmişte net satış, marj, sipariş ritmi, RFM, ürün yoğunlaşması, zaman çizgisi, ürün ilişkileri ve son 100 fatura. Dönem kapsamları ekranda belirtilir.
- Ürün profili: ABC/etiketler, sinyal kanıtları, fiyat/maliyet seyri, fiyat koridoru, iadeler, ürünü alan müşteriler ve kaynak satış hareketleri. Ayrıntılı stok için ilgili stok kaydına geçilir.
- Tam sayfa profillerden müşteri ↔ ürün geçişi yapılır. **Karar hazırla** ile işlem ve başarı ölçütü yazılır; profil kanıtı ve analiz tarihi sabitlenir. Kullanıcı önerisi olduğu açıkça belirtilir; görev ancak ayrıca onaylanınca oluşur.
- Ürün/müşteri listeleri 50 kayıtlık sayfalarla gezinilir; profil ilişkilerinin kalanları **Daha fazla göster** ile açılır. Profiller yüklenmiş veriyi kullanır, hazır karar demosuyla karışmaz.

`tests/profile-browser.cjs`, aynı izole sunucuda `tests/decision-browser.cjs` sonrasında çalıştırılır; onun CASE-P1 / CASE-C1 kayıtlarını kullanır. `TEST_URL` ile test sunucusu belirtilir. Profil geçişi, kaynaklı öneri, onay kapısı ve 1440/768/390 px yerleşimler kontrol edilir.

## Doğrulama

```powershell
npm test
npx tsc --noEmit
npm run build
```

CSV aktarımını sınayan tarayıcı testlerini yalnız izole bir veri dizini kullanan sunucuda çalıştırın. Anonim mod kontrolü için anonim sunucuya karşı `node tests/privacy-browser.cjs` kullanın (`TEST_URL`, varsayılan port 3015).

```powershell
$env:DATA_DIR = Join-Path $env:TEMP ('ongoru-test-' + [guid]::NewGuid())
$env:APP_DATA_MODE = 'original' # Yalnız bu boş, izole test dizininde CSV akışı için
npm run start -- --port 3011
```

Ayrı terminalde:

```powershell
$env:TEST_URL = 'http://127.0.0.1:3011'
node tests/browser.cjs
node tests/decision-browser.cjs
```

`tests/browser.cjs` boş veri alanı bekler. `decision-browser.cjs` demo alanını sıfırlar. Playwright yolu `PLAYWRIGHT_MODULE` ile değiştirilebilir; varsayılan yerel Codex runtime yoludur. Test tarayıcısı dış font isteğini engelleyerek çevrimdışı deterministik çalışır; arayüz sistem yazı tipi yedeğiyle de doğrulanır.

## Çalıştırma

Node.js 20.9+ ve Python 3.10+ gerekir. Python analiz motoru yalnız standart kütüphane kullanır.

```powershell
npm install
npm run dev
```

Tarayıcıda http://127.0.0.1:3000 açılır. Gerekirse `.env.example` dosyasını `.env.local` olarak kopyalayarak `PYTHON_PATH` belirleyin. Üretim derlemesi: `npm run build`; yerel sunucu: `npm start`.

## Akış

1. Stok (10 kolon) veya hareket (32 kolon) CSV seçin. Kolon isimleri `analysis/engine.py` içinde kullanıcının verdiği sırayla tanımlıdır. Boş şablon arayüzden indirilebilir.
2. CSV virgülle ayrılır. Virgül içeren sayı/metinler çift tırnak içinde olmalıdır. UTF-8 (BOM dahil), Windows-1254 ve UTF-16 açık seçimle desteklenir. En fazla 20 MB / 100.000 veri satırı.
3. Başlıklar adla eşleştirilir. Türkçe/ASCII yazım farkları için öneri üretilir; yinelenen ve eksik başlıklarda elle seçim gerekir. Her hedef alan farklı kaynak kolonuna bağlanmalıdır. Konuma göre sessiz eşleştirme yapılmaz.
4. Ondalık ayracı ve tarih biçimi kullanıcı seçimine dayanır. Kodlar metin olarak kalır. Boş hücre null olur. Marjlar rapordaki yüzde puan ölçeğinden orana çevrilir; bu varsayım UI'da görünür.
5. Stok için ayrıca görüntü tarih/saatini girin. Birim dönüşümünü doğrulayan ürün kartı bulunmadığı için miktar ve içerik çarpımı yapılmaz.
6. Hatalı yapı, dönüştürülemeyen hücre veya zorunlu boş alan satırı karantinaya alır. Diğer boş alanlar, sıfır maliyet, işaret, tarih, birim ve tekrar adayları uyarıdır. Tekrar adayları kullanıcı onayıyla korunur; otomatik silinmez.
7. Kalite raporunu inceleyip aktarımı onaylayın. Hatalı satırlar analitik kayıt tablosuna alınmaz; ham dosyada ve raporda korunur. Aynı dosyanın aynı türde tekrar aktarımı SHA-256 + SQLite UNIQUE kısıtıyla engellenir. Farklı dosyalardaki tam içerik eşleşmeleri uyarı verir, satır ID olmadığı için kesin tekrar sayılmaz.

## Veri sağlığı ölçümü

- **Şema uygunluğu:** kolon sayısı, boş satır ve eşleştirilmemiş kolon kontrolleri.
- **Tamlık:** zorunlu alanları üç kat ağırlıklandıran hücre doluluk puanı.
- **Geçerlilik:** tarih ve sayı dönüşümü, maliyet, içerik, stok, fatura türü ve birim sözlüğü kontrolleri.
- **Tutarlılık:** fatura türü–miktar işareti, tarih–Ay/Yıl, dosya içi tekrar ve önceki aktarımla çakışma kontrolleri.

Genel durum, bu dört kapının yanında hareket döneminin sonunu, stok görüntü tarihini ve hareket–stok ambar kapsamını dikkate alır. Modül hazırlığı yalnız alan doluluğuna değil, modülü etkileyen aktif kalite bulgularına da bağlıdır. Hesaplamada her veri türünün yalnız en son aktarımı kullanılır; eski partiler geçmiş olarak korunur.

## Saklama ve sınırlar

- Ham CSV, metadata ve tam kalite raporu `data/staging` içinde saklanır. Onaylanan kayıtlar ve aktarım geçmişi `data/center.sqlite` içinde ayrı stok/hareket türleriyle tutulur. Veri dosyaları Git dışında bırakılmıştır.
- Stok görüntüleri zaman üzerinden toplanmaz. Ana ekran yalnız son aktarılan stok görüntüsünün kabul edilen satır sayısını gösterir; bu stok miktarı değildir.
- Kaynak kapsamı karantinadaki kayıtları da içerir. Veri sağlığı puanları tanımlı teknik kuralları özetler; doğrulanmamış ticari KPI üretilmez.
- Para birimi, birim dönüşümü, indirim ve fatura türlerinin işletmeye özel tanımları sonraki aşamada doğrulanmalıdır. Şimdilik fatura türü işaretleri rapordaki Türkçe adlarla kontrol edilir; tanınmayan tür uyarı üretir.
- Demo tek kullanıcı için localhost'a bağlanır. Kimlik doğrulama, yetki rolleri, uzak sunucu, otomatik senkronizasyon ve kurumsal dağıtım bu sürümde yoktur. Ağ yayını yapılmamıştır.
- Hata raporu CSV dışa aktarımında formül başlangıçları etkisizleştirilir. Ham dosya aynen korunur.
- Tekrar kontrolü aynı dosyayı farklı stok tarihiyle de engeller. Aynı içeriğin yeni tarihli gerçek stok görüntüsü olarak kullanılması gerekiyorsa sonraki aşamada açık sürüm politikası tanımlanmalıdır.

## Doğrulama

```powershell
python -m unittest discover -s tests -v
npm run build
```

Testler geçici dizin kullanır; gerçek aktarım verisine yazmaz. Yapay test kayıtları ayrı test dizininde ve test sunucusunda değerlendirilir.

## İleri ticari inceleme

- **Müşteri:** tekrar sipariş, geçmişte kaybolan ürün, mevcut kategoride çeşitlendirme ve yeni kategori önerileri. En az 5 benzer portföy ve aday üründe en az 3 alıcı olmadan portföy önerisi çıkmaz. Kanıt, örneklem, güven ve sınırlamalar görünür. “Karara taşı” açıklamayı onay bekleyen dosyaya aktarır. Kategori dengesi tablosu tüm müşteri geçmişini gösterir.
- **Kategori:** Ürün ve Kategori içindeki **Kategori stratejisi** sekmesi; güncel/önceki 90 gün, net ciro katkısı, ağırlıklı marj, en büyük ürün payı, riskli ve zarar eden ürünler. Kategoriden ürüne inilir.
- **Ürün:** ilk üç müşteri yoğunlaşması (iade öncesi tutarlar), dönem büyümesi ve fatura başına net satış. Zarar eden satışlar ürünün aylık marjında da negatif kalır.
- **Stok:** kapsama, değer veya tüketim hızına göre sıralama; 50 kayıtlık sayfalama. Detayda tedarik süresi, güvenlik payı ve hedef kapsama ile geçici alım senaryosu. Demo stok, açık sipariş ve tedarikçi verisi eksikliği görünür; sipariş/görev oluşturulmaz.
- **Coğrafya:** çevrimdışı dünya haritası, ülke seçimi, sürükleme, yakınlaştırma, klavye gezinmesi; ciro/kâr/marj renkleri ve şehir → tablo filtresi. Şehirler noktayla gösterilir. Belirsiz/eksik eşleşmeler tahmin edilmeden listelenir. Natural Earth (public domain) ve GeoNames (CC BY 4.0) kaynakları arayüzde belirtilir.

İleri akış testi: önce yeni bir `test-results` alt dizini için `python -m tests.seed_advanced <tam-dizin>` çalıştırın. Aynı dizini `DATA_DIR` olarak kullanarak 3014 portunda sunucu başlatın; ardından `node tests/advanced-browser.cjs` çalıştırın. `TEST_URL` farklı port seçmeye izin verir. Bu test gerçek veri alanında çalıştırılmaz. Toplam 78 Python testi mevcuttur.
