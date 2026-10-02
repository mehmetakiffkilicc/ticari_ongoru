# Ticari Öngörü Merkezi — Uçtan Uca Uygulama Programı

Bu belge, uzun geliştirme sürecinde oturumlar yenilense bile çalışmanın kaldığı yerden devam etmesi için yaşayan kontrol listesidir. Ürün kararlarının ayrıntılı kaynağı `YOL_HARITASI.md`; bu dosya ise uygulanma sırası, kabul kapıları, açık kararlar ve gerçekleşme kaydıdır.

## 1. Kullanım protokolü

- Her geliştirme turunun başında bu dosya ve `YOL_HARITASI.md` okunur.
- Yalnız doğrulanmış işler `[x]`, aktif işler `[-]`, bekleyen işler `[ ]`, karar bekleyenler `[?]` ile işaretlenir.
- Her faz, hesaplama testi + API testi + arayüz kabulü + üretim derlemesi tamamlanmadan kapatılmaz.
- Demo veya tahmini sonuçlar hiçbir ekranda gerçek ölçüm gibi sunulmaz.
- Aynı kavram bütün modüllerde aynı kodu, adı, rengi, önem seviyesini ve açıklama biçimini kullanır.
- Yeni kararlar önce Bölüm 4'e, kesinleşince `YOL_HARITASI.md` ile ilgili faza işlenir.

## 2. Mevcut doğrulanmış temel

- [x] CSV aktarımı, şema kontrolü, karantina ve tekrar yükleme koruması
- [x] Yerel SQLite kayıt katmanı ve Python analiz motoru
- [x] Ortak lacivert uygulama kabuğu, sabit sol menü ve ortak analiz tarihi
- [x] Yönetim Kokpiti ilk sürümü
- [x] Ürün etiketlerinin ilk kural kataloğu ve 90 günlük dönem karşılaştırmaları
- [x] Ürün ve Kategori sayfası; arama, sıralamalar, ABC, kategori katkısı ve ürün detayı
- [x] Tüketim hızına bağlı, tam kolili ve açıkça işaretlenmiş demo stok modeli
- [x] 55 Python testi, TypeScript kontrolü ve Next.js üretim derlemesi
- [x] Kalıcı mimari bilgi grafiği (`graphify-out`)

## 3. Bağlayıcı uygulama sırası

### Faz A — Ortak karar motoru

- [x] Tek metrik sözlüğünü kod seviyesinde merkezileştir
- [x] Fatura türü, işaret, birim, para ve tarih normalizasyonunu ortak semantik katmana taşı
- [x] Etiket kural kataloğunu ürün dışındaki varlıklara genişlet
- [x] Etiket kanıt şemasını standartlaştır: gözlem, referans, etki, dönem, güven
- [x] Sinyal puanını önem × etki × güven × güncellik bileşimiyle ortaklaştır
- [x] Aynı olayın tekrar üretilmesini önleyen sinyal/uyarı kimliği oluştur
- [x] Etiket → sinyal → uyarı → aksiyon izini SQLite içinde kalıcılaştır
- [x] Ortak durum sözlüğü: bilgi, dikkat, yüksek, kritik
- [x] Açıklanabilirlik paneli ve kaynak satırına geri dönüş sözleşmesi
- [x] Kural kataloğu ve eşik testleri

### Faz B — Müşteri 360 ve müşteri sinyalleri

- [x] Müşteri özetleri: ciro, kâr, sipariş, sepet, ürün çeşitliliği, iade
- [x] RFM ve alışveriş ritmi ölçüleri
- [x] Geciken müşteri / kayıp riski sinyali
- [x] Büyüyen, küçülen, yeni, geri kazanılan ve yoğunlaşma etiketleri
- [x] Müşteri arama, segmentler, zaman çizgisi ve ürün ilişkileri
- [x] Ürün detayından müşteri detayına çapraz geçiş
- [x] Müşteri sinyal ve arayüz kabul testleri

### Faz C — Fiyat ve Maliyet

- [x] Birim fiyat, birim kayıtlı maliyet ve birim yerine koyma maliyetini ortaklaştır
- [x] Fiyat/maliyet/marj değişim etiketleri
- [x] Fiyat koridoru, dağılım ve müşteri bazlı fiyat sapmaları
- [x] Hedef marj fiyatı ve fiyat açığı
- [x] Yerine koyma marj riski ve fiyat güncelleme adayları
- [x] Fiyat önerisinin kanıtı, etkisi ve güven seviyesi
- [x] Hesaplama ve uç değer testleri

### Faz D — Satıcı Performansı

- [x] Yalnız satış ve satış iadesi kapsamıyla satıcı metrikleri
- [x] Bilinmeyen satıcıyı ayrı ve açıklanmış grup olarak koru
- [x] Ciro, kâr, marj, sepet, müşteri erişimi, iade ve prim ölçüleri
- [x] Portföy kalitesi ve satıcı karşılaştırma etiketleri
- [x] Koçluk/fırsat sinyalleri ve müşteri/ürün kanıtları
- [x] Test ve kabul

### Faz E — Coğrafi Analiz

- [x] Ülke, şehir ve posta kodu standardizasyonu
- [x] Bölgesel ciro, kâr, müşteri, ürün ve iade yoğunluğu
- [x] White-space / portföy boşluğu sinyalleri
- [x] Bölgesel büyüme, daralma ve yoğunlaşma etiketleri
- [x] Harita kullanılacaksa yalnız doğrulanmış konum eşlemesi
- [x] Test ve kabul

### Faz F — Satın Alma ve Stok Dengesi

- [x] Satın alma ve satın alma iadesi semantik kapsamı
- [x] Birim alım maliyeti ve alım fiyatı değişimi
- [x] Demo stok tüketimiyle sipariş ve eritme adayları
- [x] Tedarikçi/ürün bazlı alım etkisi; veri yoksa iddia üretmeme
- [x] Önerilen sipariş miktarı için açık demo varsayımları
- [x] Kritik/fazla stok aksiyon adayları
- [x] Test ve kabul

### Faz G — Sepet ve Çapraz Satış

- [x] Fatura bazlı sepet veri kümesi
- [x] Destek, güven ve lift ölçüleri
- [x] Minimum örnek ve tesadüfi ilişki korumaları
- [x] Müşteri white-space fırsatları
- [x] Sepeti daralan müşteri sinyali
- [x] Ürün ve müşteri detayına çapraz geçiş
- [x] Test ve kabul

### Faz H — İade Analizi

- [x] Ayrı İade Analizi sayfası ve menü konumu
- [x] İade cirosu, miktarı, oranı, kâr etkisi ve yerine koyma etkisi
- [x] En çok iade edilen ürünler ve en çok iade yapan müşteriler
- [x] İade hızının sürmesi halinde 30/90 günlük etki senaryosu
- [x] Tekrar eden ve yükselen iade sinyalleri
- [x] Ürün/müşteri/satıcı çapraz geçişleri
- [x] Test ve kabul

### Faz I — Uyarılar ve Anomaliler

- [x] Bütün modül sinyallerini tek olay akışında birleştir
- [x] Kritik, yüksek, dikkat ve bilgi önem seviyeleri
- [x] Kural tabanlı + sağlam istatistiksel anomali tespiti
- [x] Tekrar birleştirme, ilk/son görülme, açık/kapalı yaşam döngüsü
- [x] Kanıt, iş etkisi, güven ve önerilen eylem
- [x] Yanlış pozitif inceleme akışı
- [x] Test ve kabul

### Faz J — Aksiyon Merkezi

- [x] Kalıcılık, sahiplik ve sonuç ölçümü kararı (D-01, D-03)
- [x] Sinyalden tek tıkla aksiyon oluşturma
- [x] Durum, öncelik, sorumlu, termin, not ve kanıt bağı
- [x] Açık, devam eden, tamamlanan, reddedilen ve geciken durumları
- [x] Aksiyon kapanış nedeni ve gerçekleşen etki
- [x] Aksiyon dönüşüm ve kapanış süreleri
- [x] Denetim izi ve testler

### Faz K — Satış ve Kârlılık

- [x] Brüt satış → indirim → iade → net satış → COGS → brüt kâr şelalesi
- [x] Günlük/aylık otomatik trend çözünürlüğü
- [x] Kategori, müşteri, satıcı ve ambar kırılımları
- [x] Kayıtlı ve yerine koyma ekonomisinin birlikte sunumu
- [x] Önceki modüllerden gelen sinyal ve aksiyon bağlantıları
- [x] Test ve kabul

### Faz L — Yönetim Kokpiti nihai entegrasyonu

- [x] En önemli sinyaller, riskler, fırsatlar ve aksiyonlar
- [x] Modüller arası çapraz filtre ve detay geçişleri
- [x] KPI sözlüğüyle birebir tutarlılık
- [x] Veri güveni ve demo/tahmin ayrımının görünürlüğü
- [x] Yönetici kabul senaryoları

### Faz M — Öngörüler ve model doğrulama

- [x] Model ailesi ve kabul eşiği kararı (D-04)
- [x] Basit referans modelleri ve geriye dönük test
- [x] Dört haftalık ürün/kategori talep öngörüsü
- [x] Beklenen müşteri siparişi
- [x] Tahmin aralığı, hata metriği ve yetersiz geçmiş durumu
- [x] Yalnız referans modeli anlamlı biçimde aşan modeli yayınla
- [x] Model kartı, veri kapsamı ve tekrar üretilebilirlik
- [x] Test ve kabul

### Faz N — Sistem sertleştirme ve teslim

- [x] Analiz motorunu alan modüllerine ayır
- [x] API sözleşme ve hata durumlarını merkezileştir
- [x] Büyük veri performansı, yükleme ve boş durumlar
- [x] Klavye, odak, kontrast ve mobil kabulü
- [x] Uçtan uca tarayıcı senaryoları
- [x] Hesap mutabakat raporu
- [x] Son yol haritası ve kullanıcı kılavuzu
- [x] Tam üretim derlemesi ve regresyon paketi

## 4. Uygulamadan önce kesinleşecek kararlar

### D-01 — Aksiyonların kalıcılığı ve sahipliği

- Durum: `[x] Onaylandı`
- Öneri: Aksiyonlar SQLite içinde kalıcı olsun. Sorumlu alanı mevcut satıcı sözlüğünden veya `Atanmamış` seçeneğinden gelsin; harici kullanıcı/rol sistemi bu demo kapsamına alınmasın.
- Etki: Aksiyon Merkezi gerçek bir görev akışı olur; yalnız öneri listesi olarak kalmaz.

### D-02 — Ortak zaman kontrolünün ayrımı

- Durum: `[x] Onaylandı`
- Öneri: Üst barda iki ayrı kavram bulunsun: varsayılan `Tüm Zamanlar` rapor dönemi ve 90 günlük etiket/sinyal penceresini bitiren `Analiz tarihi`. Sayfalar ikisini aynı anlamda kullanmasın.
- Etki: Kümülatif raporlarla “bu tarih itibarıyla” çalışan risk sinyalleri çelişmez.

### D-03 — Aksiyonun ticari sonuca dönüşmesi

- Durum: `[x] Onaylandı`
- Öneri: İlk demoda otomatik sipariş atfı yapılmasın. Kullanıcı aksiyonu kapatırken `Siparişe dönüştü / sonuçsuz / ertelendi / ölçülemedi` sonucu ve isteğe bağlı gerçekleşen Euro etkisini girsin.
- Etki: Kanıtlanamayacak otomatik başarı oranı üretilmez; dönüşüm KPI'ı gerçek kullanıcı kaydına dayanır.

### D-04 — Öngörü modeli yayınlama standardı

- Durum: `[x] Onaylandı`
- Öneri: Önce mevsimsel-naif ve hareketli ortalama referansları kurulsun; zaman serisi çapraz doğrulamasında yeterli örnek ve anlamlı hata iyileşmesi olmadan karmaşık ML modeli gösterilmesin.
- Etki: Demo, uydurma bir “AI doğruluk oranı” yerine ölçülebilir model performansı sunar.

### D-05 — Coğrafi görselleştirme

- Durum: `[x] Onaylandı`
- Öneri: Harici geocoding kullanılmasın. İlk sürüm ülke/şehir/posta kodu kırılımlı yoğunluk tablosu ve sıralı çubuklarla kurulsun; ancak doğrulanmış çevrimdışı koordinat sözlüğü eklenirse harita açılsın.
- Etki: Yanlış koordinat veya ağ bağımlılığı oluşmaz.

## 5. Her fazın tamamlanmışlık kapısı

- [x] Metrik formülü ve veri kapsamı dokümana işlendi
- [x] Demo, tahmin ve gerçek alanları arayüzde ayrıldı
- [x] Eksik/yetersiz veri davranışı tanımlandı
- [x] Etiket kodu, sinyal puanı ve aksiyon bağı tanımlandı
- [x] Hesaplama testleri eklendi
- [x] API sözleşmesi test edildi
- [x] Arayüz boş, yükleniyor, hata ve dolu durumları doğrulandı
- [x] En az bir uçtan uca iş senaryosu doğrulandı
- [x] Next.js üretim derlemesi geçti
- [x] Bu kontrol listesi ve `YOL_HARITASI.md` güncellendi

## 6. Çalışma günlüğü

### 21 Eylül 2026

- [x] Proje kodu ve karar dokümanları bilgi grafiğine dönüştürüldü.
- [x] Uçtan uca faz sırası etiket → sinyal → uyarı → aksiyon omurgası etrafında sabitlendi.
- [x] Beş maddelik karar kapısı oluşturuldu.
- [x] Karar kapısı tamamlandı; Faz A uygulamasına geçildi. (Tarihsel kayıt)

### 22 Eylül 2026

- [x] Beş karar kapısı kullanıcı onayıyla kesinleştirildi.
- [x] Ortak metrik, fatura semantiği, önem ve sinyal puanı sözlükleri kod seviyesinde kuruldu.
- [x] Sinyal, uyarı, aksiyon ve aksiyon olayları SQLite içinde kalıcılaştırıldı; tekrar önleme testi eklendi.
- [x] Uyarılar ve Aksiyon Merkezi gerçek menü sayfalarına bağlandı ve tarayıcıda doğrulandı.
- [x] Satış, müşteri, satıcı, coğrafya, fiyat, satın alma, sepet ve öngörü menüleri ortak analiz API'sine bağlandı.
- [x] Müşteri, fiyat, satıcı, coğrafya, satın alma, sepet ve iade uzman modülleri gerçek veriye bağlandı.
- [x] Birleşik olay inceleme akışı ve ölçülebilir Aksiyon Merkezi tamamlandı.
- [x] Satış ve Kârlılık uzman ekranı ile Yönetim Kokpiti karar şeridi tamamlandı.
- [x] Baseline/backtest tabanlı Öngörü ekranı ve model kartları tamamlandı.
- [x] 19.335 satırda satış–satın alma mutabakatı ve 55 test geçti; TypeScript ve üretim derlemesi temiz.
- [x] Müşteri sipariş beklentisi; medyan ritim, beklenen tarih, gecikme ve güven seviyesiyle Öngörüler'e eklendi.
- [x] Sinyal ayrıntıları doğrulanabilir kaynak satırı/fatura kanıtına bağlandı; güvenilir eşleşme yoksa toplu kanıt olarak işaretlendi.
- [x] Modal/çekmece odak yönetimi, klavye etkileşimi, mobil sabit navigasyon ve lacivert tema kabul katmanı tamamlandı.
- [x] Yönetici, satış ve satın alma temel tarayıcı senaryoları doğrulandı; ana sayfadaki gereksiz olay tablosu kaldırıldı.
