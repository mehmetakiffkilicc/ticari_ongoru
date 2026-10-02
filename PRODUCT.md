# Ticari Öngörü Merkezi

## Ürün tanımı

Ticari Öngörü Merkezi; yönetici, satış, satın alma ve veri sorumlusu rollerinin aynı ticari gerçeklik üzerinden çalıştığı, Euro bazlı bir karar destek demosudur. Ana deneyim Veri → Etiket → Sinyal → İçgörü → Kullanıcı onayı → Aksiyon → Geri bildirim hattıdır. Karar dosyası kanıtı, öneri sürümlerini, onayı, uygulamayı ve sonucu birlikte korur. Uzman analizler Ticari İnceleme altında erişilebilir.

Ürün yalnızca rapor göstermez. Her sinyalin nedenini, ticari etkisini, önemini ve önerilen sonraki aksiyonu görünür kılar. Aynı kavram bütün sayfalarda aynı ad, renk ve hesaplama kuralıyla kullanılır.

## Kullanıcılar ve temel amaçlar

- **Yönetici:** Şirketin ticari sağlığını, riskleri ve fırsatları tek bakışta görmek; ayrıntıya güvenle inmek.
- **Satış yöneticisi ve satıcı:** Müşteri ve ürün performansını, fiyat/marj sapmalarını ve aksiyon fırsatlarını görmek.
- **Satın almacı:** Talep hızı, stok kapsama, tedarik ve yerine koyma ekonomisini birlikte değerlendirmek.
- **Veri sorumlusu:** Kaynak dosyaları doğrulamak, karantina kayıtlarını incelemek ve analitik sonuçların izini kaynak satırına kadar sürmek.

## Karar merkezleri ve demo

- Ana menü: Karar Özeti, Sinyaller ve İçgörüler, Onay Kuyruğu, Aksiyonlar, Sonuçlar ve Geri Bildirim, Ticari İnceleme, Veri ve Etiketler. İlk açılış Karar Özeti; sonraki yenilemeler mevcut oturumun görünümünü korur.
- Ticari İnceleme: Satış ve Kârlılık, Müşteri ve Pazar, Ürün ve Tedarik, Öngörüler. Stok detayının tek sahibi Stok; satın alma önerilen miktar ve alım ekonomisine odaklanır.
- Tek aşamalı onay görev oluşturur; başlatma ve uygulandı kaydı ayrı işlemlerdir. Kapsam değişirse önceki görev geçersizleşir, eski onay korunur ve yeni sürüm onay bekler.
- Takip uygulamadan sonra başlar: stok 7, müşteri 14, fiyat/marj 30 gün; kullanıcı 1–365 gün seçebilir. Sonuç: hedef karşılandı, kısmen karşılandı, karşılanmadı veya ölçülemedi.
- Dokuz kalıcı demo dosyası ayrı alandadır; gerçek kaynak toplamlarına eklenmez. Demo tarihi 30.12.2024, işlem zamanları gerçek yerel zamandır. Zaman ilerletme yoktur; yeni uygulanan demo görevi erken sonuç alamaz.
- Hazır stok takip örneği değerlendirme gününe ulaşmıştır; diğer bekleyen örnekler gelecekteki takip gününü gösterir. Tamamlanmış üç örnek başarı, kısmi başarı ve başarısızlık içerir.
- Liste okumak değerlendirme yapmaz. Yüklenmiş veri için **Veriyi değerlendir** açık işlemi yeni, kanıtı dondurulmuş dosyalar oluşturur; aynı kaynak ve tarihte tekrar değerlendirme dosyaları çoğaltmaz.
- Geri bildirim kullanıcı tarafından kaynak belirtilerek girilir; otomatik etki ölçümü, nedensellik iddiası, harici ERP işlemi veya model eğitimi yoktur.
- Eski aksiyonlar yüklenmiş veri alanında salt okunur geçmiş olarak korunur. Geçmişte bulunmayan onay veya sonuç türetilmez.

## Kesinleşen ürün kararları

- Varsayılan dönem bütün analitik sayfalarda **Tüm Zamanlar (2023–2024)** olur.
- Demo değerlendirme tarihi kullanıcı tarafından seçilebilir; dönemsel sinyaller bu tarihe göre üretilir.
- Ortak üst filtreler sayfalar arasında tutarlı davranır; sayfaya özgü gelişmiş filtreler sağ çekmecede yer alır.
- Satış ve satış iadeleri ticari analizlerde işlenir; satın alma ve satın alma iadesi ciroya dahil edilmez.
- Sıfır maliyetli satırlar kârlılık hesaplarını bozmaz; karantinada, aranabilir ve dışa aktarılabilir biçimde gösterilir.
- Para birimi Euro'dur. Satış fiyatı, kayıtlı maliyet ve yerine koyma maliyeti ürünün birim değeri üzerinden sunulur.
- 90 günlük dönemler değişim sinyallerinin temelidir. Yeterli geçmiş yoksa sistem tahmin uydurmaz, **Yetersiz Geçmiş** durumunu gösterir.
- Stok anlık miktarları demo için tahmini olabilir; koli/paket yapısı kaynak veriden, tüketim hızı gerçek satış hareketlerinden türetilir ve tahmini değer açıkça etiketlenir.
- Etiket, sinyal, önem seviyesi ve aksiyon durumu ortak bir sözlük kullanır.

## Ürün ilkeleri

### Karar merkezine bağlı detaylı inceleme

Ticari İnceleme, dört grupta 12 analiz için açıklamalı bir giriş ekranıdır. Karar Özeti'nden Müşteri 360 ve Ürün 360'a doğrudan erişilir. Detaylar tam sayfa profillerdir: müşteri geçmişi, RFM, sipariş ritmi, ürün ilişkileri ve fatura dökümü; ürünün etiket kanıtı, fiyat/maliyet seyri, müşteri dağılımı ve kaynak hareketleri birlikte araştırılabilir. Müşteri ile ürün arasında çift yönlü geçiş vardır.

Profil göstergeleri son 90 günü, müşteri zaman çizgisi analiz tarihine kadar geçmişi kapsar; fatura listesi en yeni 100 kaydı gösterir. Ürün/müşteri portföyleri 50'şer kayıtla sayfalanır. İlişkili ürünler ve müşteriler kademeli açılır.

Kullanıcı profilden işlem ve başarı ölçütü yazarak karar hazırlayabilir. Bu öneri otomatik tespit edilmiş sinyal gibi sunulmaz. Sunucu kimliği kaynakta doğrular, kanıtı ve tarihi saklar, aynı öneriyi çoğaltmaz. Onay bekleyen dosya mevcut karar hattına girer; profil ekranından onaysız aksiyon oluşmaz. Profilde varlığa bağlı önceki dosyalara da erişilir.

- Ham kaydı koru; dönüştürülmüş değeri ve hata nedenini ayrı göster.
- Bilinmeyeni sıfır, kesin veya başarılı gibi sunma.
- Kaynak ile tahmini değeri görsel ve metinsel olarak ayır.
- Her KPI ve sinyal için açıklama, formül bağlamı ve ayrıntıya iniş yolu sağla.
- Filtre ve navigasyon durumunu sayfalar arasında öngörülebilir tut.
- Gerçek veri yokken boş durum göster; örnek veriyi gerçek sonuç gibi sunma.
- Kararı hızlandır: risk/fırsat → kanıt → önerilen aksiyon → takip durumu zincirini koru.

## Erişilebilirlik ve kalite

Klavye erişimi, görünür odak, metinli durum etiketleri, yeterli renk kontrastı, azaltılmış hareket desteği, açıklayıcı boş/hata/yüklenme durumları ve duyarlı yerleşim teslimat ölçütüdür. Kritik akışlar yönetici, kullanıcı/satış ve satın almacı perspektiflerinden test edilir.

## İleri inceleme — uygulanan davranış

Müşteri önerileri dört ayrı gerekçe taşır: yenileme, geri kazanım, kategori içi çeşitlendirme ve yeni kategori. Aynı ürünün üç ayrı satın alma günü olmadan ritme dayalı yenileme önerilmez. İki eski alım ve 90 günü aşan boşluk geri kazanım adayıdır. Ortak ürün alan en az beş başka müşterinin en az üçünde görülen, pozitif kâr katkısı taşıyan yeni ürün portföy önerisi olabilir. %30 ve üstü iade payı adayları bastırır. Muadil ürün veya satın alma olasılığı iddiası yoktur. Öneriler kullanıcı düzenlemesi ve mevcut tek aşamalı onaya tabidir.

Kategori stratejisi, ürün portföyü içinde ayrı çalışma görünümüdür. Kategori katkısı, ağırlıklı marj, dönem değişimi, yoğunlaşma ve zarar eden ürün sayısı üzerinden ürün detayına geçilir. Stok senaryosu tedarik varsayımlarıyla geçici hesap yapar; demo stok fiziksel stok yerine kabul edilmez.

Coğrafi performans ülke toplamları ve şehir merkezi noktalarıyla gösterilir. Ülke/şehir eşleştirmesi yerel sözlüklerden yapılır; müşteri adresleri dış servise gönderilmez. Kesin eşleşmeyenler, tablo toplamından çıkarılmadan ayrıca gösterilir. Haritada il sınırı dolgusu bu sürümün kapsamı değildir.
