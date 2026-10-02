# Ticari Öngörü Merkezi — Teslimat Kontrol Listesi

Bu belge son demo kabulünde tekrarlanacak kontrolleri tanımlar. Bir madde yalnız otomatik test ve/veya tarayıcı kanıtı görüldüğünde tamamlanmış sayılır.

## Karar hattı kabulü — 23 Eylül 2026

- [x] Yedi ana merkez, dört uzman analiz grubu; varsayılan Karar Özeti.
- [x] Üç senaryo, dokuz kalıcı demo dosyası; ayrı kapsam ve güvenli demo sıfırlama.
- [x] Yedi aşamalı tam sayfa dosya, sürümlü öneriler ve tarihli olay geçmişi.
- [x] Onaydan önce başlatma engeli; eşzamanlı onaylarda tek görev; kapsam değişince yeniden onay.
- [x] Uygulama ile başarı sonucu ayrı; erken geri bildirim engeli; veri yokken ölçülemedi.
- [x] Önceki karar korunarak yeni inceleme; sayfa yenilemede dosya ve çalışma alanının korunması.
- [x] Gerçek CSV → karar kanıtı → kalite raporu → karar dosyasına dönüş.
- [x] Uzman fiyat analizine ilgili ürün ve kanıt tarihiyle geçiş.
- [x] Ekran okumalarında yeni değerlendirme yok; gelecekteki kaynak satırları geçmiş kanıta eklenmiyor.
- [x] Eski aksiyonlar ve canlı dosyalar demo sıfırlamasından etkilenmiyor.
- [x] CSV aktarımı, kolon eşleme, karantina, onay, dışa aktarım ve tekrar dosya engeli tarayıcı regresyonu.
- [x] Masaüstü, 1024/768/390 px karar dosyası, mobil özet, klavye erişimi ve sıfır tarayıcı hatası.

Doğrulama: 71 Python testi, TypeScript denetimi ve üretim derlemesi. Tarayıcı senaryoları `tests/browser.cjs`, `tests/decision-browser.cjs` ve `tests/profile-browser.cjs`; ekran kanıtları `test-results/decision-*.png` ve `test-results/*profile*.png`. Testler yalnız izole veri dizinlerinde çalıştırılır.

## Detaylı inceleme kabulü

- [x] Karar Özeti kısayolları ve dört grupta 12 uzman analizin açıklamalı dizini.
- [x] Müşteri 360 / Ürün 360 tam sayfa profilleri; müşteri → ürün → müşteri geçişi.
- [x] Profil kanıtından kullanıcı önerisi oluşturma, ilişkili dosyalar ve onaysız başlatma engeli.
- [x] Aynı profil önerisinde tekrar gönderim güvenliği; bilinmeyen kimlik reddi.
- [x] Müşterinin zarar eden satışında kâr işaretinin özet, zaman çizgisi, ürün ve fatura görünümünde korunması.
- [x] Masaüstü, tablet ve mobil profil yerleşimi; iç içe dikey kaydırma olmaması.

## Hesap mutabakatı

- [ ] Net satış = satış faturaları − satış iadeleri; satın alma faturaları dışarıda.
- [ ] Net satın alma = alış faturaları − alış iadeleri; satış faturaları dışarıda.
- [ ] Kâr, marj ve yerine koyma değerleri aynı satır kapsamından hesaplanıyor.
- [ ] Analiz tarihi sonrasındaki kayıt hiçbir sinyal veya tahmine sızmıyor.
- [ ] Simülasyon tarihi kalıcı resmî sinyal üretmiyor.
- [ ] Para birimi tüm ticari ekranlarda EUR.

`analysis.delivery_audit.delivery_audit` son hareket partisini kaynak alarak satış ve satın alma mutabakatını makinece okunabilir biçimde üretir.

## Tahmin kabulü

- [ ] Ürün ve kategori için dört haftalık tahmin bulunuyor.
- [ ] Hareketli ortalama ve yeterli geçmişte mevsimsel-naif baseline rolling-origin test edildi.
- [ ] MAE, WAPE ve bias kullanıcıya açıklanıyor.
- [ ] Tahmin hata bandı ve model kartı görünür.
- [ ] Yetersiz geçmiş, sıfır tahmin gibi gösterilmiyor.
- [ ] Deneysel aday en az 8 test noktasında baseline WAPE'ını en az %10 iyileştirmeden yayınlanmıyor.
- [ ] ML yayınlanmış gibi gösterilmiyor.

## API ve performans sözleşmesi

- [ ] Hatalar `{ok:false,error:{code,message,details,retryable,requestId}}` zarfını kullanıyor.
- [ ] Doğrulama, bulunamadı, boyut, zaman aşımı ve iç hata farklı HTTP durumları taşıyor.
- [ ] Python motorunun `{ok:false}` yanıtı HTTP 200 olarak dönmüyor.
- [ ] Liste uçları `offset`, `limit`, `total`, `hasNext` döndürüyor; limit en fazla 100.
- [ ] 100.000 satır CSV, 20 MB istek, 40 MB çıktı ve 120 saniye sınırları korunuyor.
- [ ] Büyük tablolar ilk boyamada en fazla 50–100 satır getiriyor.
- [ ] API kullanıcıya traceback, dosya yolu veya ham sistem hatası göstermiyor.

## Rol bazlı kabul

### Yönetici

- [ ] Kokpit, kârlılık ve aksiyon merkezindeki toplamlar mutabık.
- [ ] Kritik sinyalden kanıta, ürüne ve aksiyona kesintisiz geçiliyor.
- [ ] Tahminin yöntemi ve belirsizliği tek ekranda anlaşılabiliyor.

### Satış kullanıcısı

- [ ] Müşteri, satıcı, ürün ve çapraz satış listelerinde arama ve detay geçişi çalışıyor.
- [ ] İade liderinden ilgili ürün veya müşteri bağlamına ulaşılabiliyor.
- [ ] Klavye odağı, boş durum, hata ve yüklenme durumları görünür.

### Satın almacı

- [ ] Son 90 gün ile önceki 90 gün alış fiyatı ayrımı doğru.
- [ ] Demo stok, gerçek stok gibi etiketlenmiyor.
- [ ] Sipariş ve eritme adayları kapsama günleriyle açıklanıyor.
- [ ] Satın alma iadesi satış iadesine karışmıyor.

## Son komutlar

```powershell
python -m unittest discover -s tests -v
npx tsc --noEmit
npm run build
```

Ardından masaüstü ve dar ekranlarda tüm sol menü rotaları, tablo detayları, çekmeceler ve aksiyon akışı tarayıcı üzerinden test edilir.

## İleri inceleme kabulü — 23 Eylül 2026

- [x] Coğrafi analizde dünya/ülke/şehir, ölçüt, zoom, klavye, şehir-tablo filtresi ve eşleşmeyenler.
- [x] Yerel harita sözlüğü, ülke zorunluluğu ve belirsiz eşleşmede koordinat üretmeme.
- [x] Dört müşteri öneri türü, yetersiz örneklem engeli, gelecek tarih/satın alma/yüksek iade/zarar adaylarının dışlanması.
- [x] Öneriden düzenlenebilir karar formuna ve onay bekleyen dosyaya geçiş.
- [x] Kategori karşılaştırması → ürün analizi → stok senaryosu.
- [x] Tedarik varsayımı değişince alım hesabının güncellenmesi; görev oluşturmaması.
- [x] Coğrafi kâr ve ürünün aylık marjında zarar işaretinin korunması.
- [x] İzole veride masaüstü/tablet/mobil tarayıcı senaryosu ve 78 Python testi.

Kanıt: `tests/advanced-browser.cjs`, `tests/test_advanced_research.py`, `test-results/advanced-*.png`.
