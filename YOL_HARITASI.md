# Ticari Öngörü Merkezi — Ana Ürün ve Uygulama Yol Haritası

> **Belge statüsü:** Bağlayıcı ana kılavuz  
> **Son karar tarihi:** 21 Eylül 2026  
> **Kapsam:** Demo ürünün veri alımından etiketleme, uzmanlık modülleri, birleşik karar ekranları ve öngörü modellerine kadar uçtan uca geliştirilmesi

## Bu belge nasıl kullanılmalıdır?

Bu dosya projenin tek doğruluk kaynağıdır. Ürün kapsamı, iş kuralları, terimler, geliştirme sırası, sayfa tasarım ilkeleri, veri gereksinimleri ve bir aşamanın tamamlanmış sayılma koşulları burada tutulur.

Oturumlar arası günlük uygulama takibi, karar kapıları ve tiklenebilir faz listesi `UYGULAMA_PROGRAMI.md` dosyasında tutulur. Bu yol haritası **ne ve neden**, uygulama programı ise **hangi sırayla ve hangi kabul kapısıyla** sorusunun bağlayıcı cevabıdır.

Yeni bir fikir ortaya çıktığında yol haritası baştan yazılmaz. Fikir, aşağıdaki sınıflardan uygun olanına eklenir:

1. Onaylanmış karar ise ilgili ana bölüme işlenir ve değişiklik kaydına eklenir.
2. Henüz kararlaştırılmadıysa **Karar Bekleyen Konular** bölümüne yazılır.
3. Mevcut veriyle yapılamıyorsa **Ek Veri Gerektiren Özellikler** bölümüne yazılır.
4. İleri aşamaya aitse ilgili aşamanın kapsamına eklenir; aktif aşamanın sırası bozulmaz.
5. Önceki bir karar değiştirildiyse eski karar silinmez; **Değişiklik Geçmişi** bölümünde neden değiştiği belirtilir.

Bu belgedeki öncelik sırası şöyledir:

1. **Nihai kararlar ve güncel geliştirme planı** bağlayıcıdır.
2. Sayfa içerik haritası hedef kapsamı tarif eder.
3. İleri analitik metodolojiler hesaplama ayrıntılarını tarif eder.
4. Tarihsel plan bölümleri yalnız geçmiş bağlamı korur; güncel sırayı değiştirmez.

---

# Bölüm I — Nihai Ürün Kararları

## 1. Ürün vizyonu

Ticari Öngörü Merkezi yalnızca grafik ve KPI gösteren bir raporlama ekranı değildir. Amaç; satış, ürün, stok, müşteri, fiyat, maliyet, satıcı ve coğrafya verilerini aynı ticari dil altında birleştirerek kullanıcıyı bulgudan aksiyona götüren açıklanabilir bir karar destek sistemi oluşturmaktır.

Hedef karar zinciri:

**Ham veri → doğrulama → ortak metrik → etiket → sinyal → uyarı/anomali → kök neden → aksiyon → ölçülen sonuç → öngörü**

Her sonuç:

- Kaynak satıra kadar izlenebilir olmalıdır.
- Kullanılan dönem, filtre ve hesaplama kuralını göstermelidir.
- Veri yetersizse kesin sonuç gibi sunulmamalıdır.
- Kullanıcıya yalnız “ne oldu?” değil, mümkün olduğunda “neden oldu?” ve “ne yapılabilir?” sorularının cevabını vermelidir.
- Aynı kavramı bütün sayfalarda aynı isim, formül, renk ve etkileşimle kullanmalıdır.

## 2. Değişmez ürün ilkeleri

1. **Tek ticari sözlük:** Net satış, brüt kâr, marj, aktif müşteri veya kritik stok gibi kavramlar sayfaya göre anlam değiştiremez.
2. **Açıklanabilirlik:** Etiket, uyarı ve model çıktısı gerekçesi ve kanıtıyla gösterilir.
3. **Veri güveni:** Bilinmeyen değer sıfır kabul edilmez; eksik ve karantina kayıtları görünür kalır.
4. **Kaynağa iniş:** KPI, grafik, sinyal ve tablodan kaynak kayda inilebilmelidir.
5. **Kademeli zekâ:** Önce doğrulanabilir kurallar, sonra istatistiksel anomaliler, yeterli veri oluştuğunda makine öğrenmesi kullanılır.
6. **Yeniden kullanılabilir arayüz:** Filtreler, etiketler, sinyaller, durumlar ve detay çekmeceleri ortak bileşenlerle uygulanır.
7. **Modüler ilerleme:** Aktif aşama tamamlanmadan daha sonraki bir modül geliştirme sırasını bozmaz.
8. **Euro standardı:** Mevcut demonun bütün parasal tutarları Euro (`€`) ile sunulur. Çoklu para birimi ayrıca veri ve kur altyapısı gerektirir.
9. **Lacivert tasarım sistemi:** Nihai görsel yön koyu lacivert/mavi gezinme, açık içerik yüzeyleri ve işlevsel durum renkleridir.
10. **Profesyonel dil:** Aynı durum için her sayfada aynı terim kullanılır; eş anlamlı fakat farklı kullanıcı dili üretilmez.

## 3. Nihai ortak filtre standardı

### 3.1 Bütün sayfalarda ortak üst bar

Her analitik sayfada aynı sırayla şu kontroller bulunur:

- **Dönem:** Varsayılan `Tüm Zamanlar (2023–2024)`.
- **Ambar:** Tekli veya çoklu seçim; bilinmeyen ambar kapsamı açıkça gösterilir.
- **Satıcı:** Tekli veya çoklu seçim; atanmamış kayıtlar ayrı seçenek olabilir.
- **Sıfırla:** Bütün ortak ve sayfaya özel filtreleri varsayılan duruma getirir.
- **Sayfa filtreleri:** Sağdan kayan bağlamsal filtre çekmecesini açar.

Ürün, kategori, müşteri, şehir, ülke, fatura türü, marj seviyesi, etiket ve veri güveni **global üst bar filtresi değildir**. Bunlar yalnız ilgili sayfanın sağ çekmecesinde, kullanıcıyla sayfa öncesinde kararlaştırılarak kullanılır.

### 3.2 Ortak dönem davranışı

- Bütün sayfalar ilk açılışta `Tüm Zamanlar (2023–2024)` ile yüklenir.
- Yıl seçilmeden yalnız ay seçilirse aynı ayın iki yıldaki toplamı gösterilir; örneğin Mayıs seçimi Mayıs 2023 + Mayıs 2024 anlamına gelir.
- Ay ve yıl birlikte seçilirse yalnız o dönem gösterilir.
- Yıl seçilirse seçilen yıl gösterilir.
- Özel başlangıç ve bitiş tarihi desteklenir.
- Seçilen aralık 90 günden kısaysa veya tek ay seçildiyse zaman grafikleri günlük kırılıma döner.
- Daha uzun aralıklarda zaman grafikleri aylık kırılım kullanır.
- Grafik noktasına tıklama, kapsamı ilgili döneme indiren çapraz filtreleme olarak çalışabilir.
- Sayfalar arasında gezinildiğinde ortak filtre durumu korunur.

### 3.3 Sayfaya özel çekmece zorunluluğu

Her yeni sayfa kodlanmadan önce aşağıdakiler kullanıcıyla onaylanır:

1. Çekmecede hangi bağlamsal filtrelerin bulunacağı
2. Her filtrenin varsayılan değeri
3. Birden fazla filtrenin birlikte çalışma biçimi
4. Filtrenin KPI, grafik, tablo, etiket ve dışa aktarıma etkisi
5. Karantina kayıtlarının dahil edilme davranışı

Bu onay alınmadan yeni sayfanın arayüzü veya hesaplama katmanı uygulanmaz.

## 4. Ortak kavram modeli

| Kavram | Kesin anlamı | Kullanıcıya gösterilecek temel içerik |
|---|---|---|
| Metrik | Doğrudan veya türetilmiş sayısal ölçüm | Değer, birim, dönem, formül |
| Etiket | Bir varlığın açıklanabilir durum sınıfı | Ad, kategori, önem, kanıt, dönem |
| Sinyal | Etiket veya metrik değişiminin ticari etkisi hesaplanmış hali | Etki, öncelik, ilgili varlıklar |
| Uyarı | Kullanıcı incelemesi veya aksiyonu gerektiren aktif sinyal | Durum, sorumlu, termin, kaynak |
| Anomali | Beklenen davranıştan istatistiksel veya kuralsal sapma | Beklenen, gerçekleşen, sapma, güven |
| Aksiyon | Analiz, sinyal veya uyarıdan üretilen iş | Sorumlu, termin, durum, sonuç |
| Öngörü | Geleceğe dönük model tahmini | Tahmin, aralık, model, hata, güven |

Bir etiket kendiliğinden uyarı değildir. Örneğin “düşük marjlı” etiketi bir durumu tanımlar. Cirosu yüksek ve marjı hızla düşen bir üründeki bu etiket yüksek ticari etkiye sahipse sinyale; belirlenen eşik aşılmış ve inceleme gerekiyorsa uyarıya dönüşür.

## 5. Ortak metrik sözlüğünün çekirdeği

Bu formüller bütün sayfalarda aynı uygulanır. Ayrıntılı alan eşleştirmeleri veri uygunluk çalışmasında kesinleştirilir.

| Metrik | Tanım |
|---|---|
| Brüt satış | Satış iadeleri düşülmeden önceki satış fatura büyüklüğü; satın alma hareketleri dahil değildir |
| Satış iadesi | Satış iade faturalarının mutlak ticari tutarı |
| Net satış | Brüt satış − satış iadeleri; indirim alanlarının veri anlamı doğrulandıktan sonra onaylı indirim etkisi ayrıca uygulanır |
| Satış maliyeti / COGS | Satılan ürünlerin doğrulanmış kayıtlı maliyet toplamı |
| Brüt ticari kâr | Net satış − satış maliyeti |
| Ağırlıklı brüt marj | Toplam brüt ticari kâr / toplam net satış |
| Ortalama fatura | Net satış / tekil satış faturası sayısı |
| Aktif ürün | Seçili kapsamda satış hareketi bulunan tekil ürün |
| Aktif müşteri | Seçili kapsamda satış faturası bulunan tekil müşteri |
| İade oranı | Satış iadesi / brüt satış |
| İndirim oranı | Doğrulanmış indirim tutarı / indirim öncesi uygun satış tabanı |
| Stok değeri | Stok miktarı × doğrulanmış birim maliyet |
| Stok kapsama günü | Kullanılabilir stok / doğrulanmış günlük satış hızı |

### 5.1 Fatura kapsamı

- Satış ve satış iadesi ticari satış hesaplarında kullanılır.
- Satın alma ve satın alma iadesi ciroya hiçbir zaman dahil edilmez.
- Satın alma hareketleri Stok ile Satın Alma ve Stok Dengesi modüllerinde ayrı işlenir.
- Tanımsız veya işaret kuralı doğrulanmamış fatura türleri karantinaya alınır.

### 5.2 Sıfır maliyet davranışı

- Sıfır maliyetli satışlar ciro ve adet analizinde görünür kalabilir.
- Doğrulanana kadar kârlılık ve marj hesaplarından varsayılan olarak çıkarılır.
- Hariç tutulan kayıt sayısı ve etkilenen satış tutarı kullanıcıya gösterilir.
- Kaynak kayıtlar aranabilir ve dışa aktarılabilir karantina görünümünde sunulur.

### 5.3 Fiyat şelalesi seviyeleri

**Demo için geçerli şelale:**

`Gerçekleşen brüt satış → indirimler → satış iadeleri → net satış → COGS → brüt ticari kâr`

**Gelecekteki genişletilmiş şelale:** Güvenilir liste fiyatı verisi geldiğinde ilk adım `Brüt liste hasılatı` olur; sözleşme ve fatura altı indirimler ayrı basamaklara ayrılır. Liste fiyatı bulunmadan mevcut brüt satış “liste hasılatı” olarak adlandırılmaz.

---

# Bölüm II — Etiketleme ve Sinyal Sistemi

## 6. Etiketleme sisteminin amacı

Etiket sistemi, modüller sonradan geliştirilirken sayfaların yeniden düzenlenmesini önleyecek ortak analitik omurgadır. Sistem yalnız metin rozeti üretmez; her etiket hesaplanabilir, açıklanabilir, sürümlenebilir, filtrelenebilir ve kaynağa kadar izlenebilir olmalıdır.

İlk teslimat iki parçadan oluşur:

1. Ortak etiket altyapısının eksiksiz kurulması
2. Mevcut veriden güvenilir biçimde üretilebilen ilk etiketlerin ön yüzde ortak bileşenlerle gösterilmesi

Henüz tasarlanmamış bir modül için varsayımsal eşikler uydurulmaz. Modüle özel etiketler, ilgili modül başlamadan önce katalogda kesinleştirilir ve mevcut motor üzerinden üretilir.

## 7. Etiket üretim seviyeleri

Etiketlerin bağlanabileceği standart analiz birimleri:

- Satış satırı × tarih
- Fatura × tarih
- Ürün × dönem
- Ürün × ambar × dönem
- Kategori × dönem
- Müşteri × dönem
- Müşteri × ürün × dönem
- Satıcı × dönem
- Şehir/ülke × dönem
- Ambar × dönem

Her etiket yalnız bir ana varlığa bağlanır; ilişkili varlıklar kanıt ve kapsam alanlarında tutulur.

## 8. Etiket kayıt şeması

Her üretilen etiket en az şu alanları taşımalıdır:

| Alan | Açıklama |
|---|---|
| `tag_instance_id` | Üretilen etiket kaydının tekil kimliği |
| `tag_code` | Değişmeyen makine kodu; ör. `PRODUCT_LOW_MARGIN` |
| `tag_version` | Kural sürümü |
| `entity_type` | Ürün, müşteri, ambar, fatura vb. |
| `entity_id` | Kaynak sistemdeki tekil kimlik |
| `period_start`, `period_end` | Etiketin kanıt dönemi |
| `status` | Aktif, sona erdi, bastırıldı, veri bekliyor |
| `severity` | Bilgi, dikkat, yüksek, kritik, veri sorunu |
| `score` | Varsa normalize edilmiş 0–100 önem puanı |
| `observed_value` | Gerçekleşen değer |
| `reference_value` | Eşik, kategori medyanı veya beklenen değer |
| `impact_metric`, `impact_value` | Etkilenen satış, kâr veya stok değeri |
| `evidence` | Kullanıcıya gösterilecek açıklanabilir kanıt |
| `rule_parameters` | Üretimde kullanılan eşikler |
| `source_scope` | Kullanılan kaynak ve filtre kapsamı |
| `calculated_at` | Hesaplama zamanı |

Etiket kodu kullanıcıya doğrudan gösterilmez. Kullanıcı adı ve açıklaması ortak terim kataloğundan gelir.

## 9. Kural kataloğu standardı

Her kural aşağıdaki biçimde belgelenir:

```text
Kod: PRODUCT_LOW_MARGIN
Kullanıcı adı: Düşük marjlı ürün
Ana varlık: Ürün
Kategori: Kârlılık
İş sorusu: Ürün kabul edilen marj seviyesinin altında mı?
Koşul: Ağırlıklı brüt marj < onaylı eşik
Asgari veri: En az N satış satırı ve sıfır olmayan doğrulanmış maliyet
Önem: Etki tutarı ve eşikten uzaklığa göre
Kanıt: Gerçekleşen marj, referans marj, net satış ve brüt kâr
Yenileme sıklığı: Veri güncellemesi sonrası
Geçerlilik: Seçili dönem
Hariç tutmalar: Sıfır maliyetli ve karantinadaki kayıtlar
Sürüm: 1
```

Kural eşikleri kaynak kod içine dağılmaz. Merkezi yapılandırmada saklanır ve sürüm değişiklikleri kayıt altına alınır.

## 10. İlk etiket kataloğu

### 10.1 Veri kalitesi etiketleri

- `DATA_ZERO_COST` — Sıfır maliyet
- `DATA_NEGATIVE_COST` — Negatif maliyet
- `DATA_MISSING_PRODUCT_CATEGORY` — Eksik ürün kategorisi
- `DATA_MISSING_CUSTOMER` — Eksik müşteri
- `DATA_MISSING_SELLER` — Atanmamış satıcı
- `DATA_UNKNOWN_WAREHOUSE` — Stok karşılığı bilinmeyen ambar
- `DATA_INVOICE_TYPE_MISMATCH` — Fatura türü ve işaret uyumsuzluğu
- `DATA_PRICE_OUTLIER` — İnceleme gerektiren fiyat uç değeri
- `DATA_INSUFFICIENT_HISTORY` — Karşılaştırma için yetersiz geçmiş

### 10.2 Ürün etiketleri

- `PRODUCT_HIGH_REVENUE_CONTRIBUTION` — Yüksek ciro katkısı
- `PRODUCT_HIGH_PROFIT_CONTRIBUTION` — Yüksek kâr katkısı
- `PRODUCT_LOW_MARGIN` — Düşük marj
- `PRODUCT_NEGATIVE_MARGIN` — Zararına satış
- `PRODUCT_REVENUE_GROWING` — Cirosu büyüyen
- `PRODUCT_REVENUE_DECLINING` — Cirosu düşen
- `PRODUCT_MARGIN_EROSION` — Marjı eriyen
- `PRODUCT_FAST_MOVING` — Hızlı hareket eden
- `PRODUCT_SLOW_MOVING` — Yavaş hareket eden
- `PRODUCT_DORMANT` — Hareketsiz
- `PRODUCT_CUSTOMER_CONCENTRATION` — Az müşteriye bağımlı
- `PRODUCT_HIGH_RETURN_RATE` — Yüksek iade oranlı

### 10.3 Stok etiketleri

- `STOCK_CRITICAL` — Kritik stok
- `STOCK_OUT_RISK` — Stok tükenme riski
- `STOCK_EXCESS` — Fazla stok
- `STOCK_DEAD` — Ölü stok
- `STOCK_HIGH_VALUE_LOW_MOVEMENT` — Yüksek değerli ve düşük hareketli stok
- `STOCK_WAREHOUSE_IMBALANCE` — Ambarlar arası dengesiz
- `STOCK_WITHOUT_SALES` — Stok var, satış yok
- `SALES_WITHOUT_KNOWN_STOCK` — Satış var, stok kapsamı bilinmiyor
- `STOCK_NEGATIVE` — Negatif stok

### 10.4 Müşteri etiketleri

- `CUSTOMER_NEW` — Yeni müşteri
- `CUSTOMER_ACTIVE` — Aktif müşteri
- `CUSTOMER_HIGH_VALUE` — Yüksek değerli müşteri
- `CUSTOMER_GROWING` — Satışı büyüyen müşteri
- `CUSTOMER_ACTIVITY_DECLINING` — Aktivitesi düşen müşteri
- `CUSTOMER_CHURN_RISK` — Müşteri kayıp riski
- `CUSTOMER_LOST` — Kaybedilmiş müşteri
- `CUSTOMER_LOW_MARGIN` — Düşük marjlı müşteri
- `CUSTOMER_PORTFOLIO_CONCENTRATION` — Ürün veya kategoriye bağımlı
- `CUSTOMER_HIGH_RETURN_RATE` — Yüksek iade oranlı

### 10.5 Fiyat ve satış etiketleri

- `SALE_HIGH_DISCOUNT` — Yüksek indirimli satış
- `SALE_BELOW_COST` — Maliyet altı satış
- `SALE_LOW_MARGIN` — Düşük marjlı satış
- `SALE_HIGH_RETURN_EFFECT` — Yüksek iade etkisi
- `PRICE_BELOW_CORRIDOR` — Fiyat koridoru altında
- `PRICE_ABOVE_CORRIDOR` — Fiyat koridoru üzerinde
- `PRICE_MARGIN_EROSION` — Fiyat kaynaklı marj erozyonu

Etiketler veri uygunluk matrisi tamamlandıktan sonra `Üretilebilir`, `Yaklaşık üretilebilir`, `Yeni veri gerektirir` veya `Güvenilmez` durumlarından biriyle işaretlenir. Yalnız üretilebilir ve iş kuralı onaylanmış etiketler aktif edilir.

## 11. Önem ve sinyal puanlama

İlk sürümde açıklanabilir bileşik puan kullanılır:

- Eşikten sapma: %35
- Etkilenen Euro tutarı: %35
- Etkilenen kayıt/müşteri/ürün kapsamı: %20
- Devam süresi veya tekrar sayısı: %10

Puan bileşenleri etikete göre uygulanabilirlik gösterir. Kullanıcıya yalnız puan değil, puanı oluşturan bileşenler gösterilir. Kritik sınıfın otomatik göreve dönüşmesi ayrıca onay gerektirir.

## 12. Etiket yaşam döngüsü

1. Veri yüklenir ve doğrulanır.
2. Ortak metrik özetleri hesaplanır.
3. Kural sürümüyle etiket adayı üretilir.
4. Asgari veri ve güven koşulu kontrol edilir.
5. Aynı varlık–etiket–dönem tekrarı birleştirilir.
6. Önceki aktif kayıtla karşılaştırılır.
7. Etiket yeni, devam ediyor veya sona erdi olarak kaydedilir.
8. Ticari etki hesaplanabiliyorsa sinyal puanı üretilir.
9. Uyarı eşiği aşılırsa Uyarılar ve Anomaliler merkezine aktarılır.
10. Kullanıcı aksiyonu ve sonuç etikete geri bağlanır.

## 13. Ön yüzde ortak etiket standardı

- Etiketler ortak `TagBadge` bileşeniyle gösterilir.
- Satırda en fazla iki rozet görünür; fazlası `+N` ile açılır.
- Rozet adı bütün sayfalarda aynı terim kataloğundan gelir.
- Üzerine gelme veya odaklanma halinde açıklama, dönem, gerçek değer ve referans gösterilir.
- Etikete tıklama ilgili sayfayı o etikete göre filtreler.
- Etiket detayı kaynak kanıta ve kural sürümüne erişim verir.
- Renk tek başına anlam taşımaz; ikon veya metinle desteklenir.
- Bilgi/fırsat mavi, dikkat sarı, yüksek risk turuncu, kritik kırmızı, veri sorunu gri ailesiyle gösterilir.
- Renk, anlam ve öncelik eşlemesi bütün uygulamada değişmez.
- Tablo, kart, detay çekmecesi ve dışa aktarım aynı etiketi aynı kodla kullanır.

## 14. Etiket altyapısı tamamlanma ölçütleri

Etiket aşaması aşağıdakilerin tamamı sağlanmadan bitmiş sayılmaz:

- Veri alanı ve uygunluk matrisi hazırlanmış olmalı.
- Ortak metrik hesapları tek kaynaktan çalışmalı.
- Kural kataloğu ve sürümleme mekanizması bulunmalı.
- Etiket kayıtları kalıcı ve tekrar üretilebilir olmalı.
- Aynı veri tekrar işlendiğinde yinelenen etiket oluşmamalı.
- En az bir veri kalitesi, ürün, stok, müşteri ve satış etiketi uçtan uca doğrulanmalı.
- Etiket kanıtı kaynak satırla uzlaşmalı.
- Ortak ön yüz bileşenleri erişilebilir olmalı.
- Etiket, önem ve durum filtreleri çalışmalı.
- Birim ve entegrasyon testleri başarılı olmalı.

---

# Bölüm III — Bağlayıcı Geliştirme Planı

## 15. Güncel aşama sırası

Bu sıra bağlayıcıdır. Aşağıdaki tarihsel aşama listeleri kapsam kaybını önlemek amacıyla belgede korunabilir ancak geliştirme sırasını değiştirmez.

### Aşama 0 — Veri Merkezi ve ortak uygulama iskeleti

**Durum:** İlk sürüm tamamlandı; kalite kuralları geliştirilmeye devam eder.

**Çıkış ölçütü:** Kaynak veri korunuyor, tekrar yükleme kontrolü çalışıyor, kalite sorunları görünür ve analiz kapsamı izlenebilir olmalıdır.

### Aşama 1 — Yönetim Kokpiti ilk sürümü

**Durum:** Tamamlandı; birleşik sinyal entegrasyonu ve nihai yönetim katmanı daha sonraki aşamada yapılacaktır.

### Aşama 2 — Etiketleme ve sinyal altyapısı

**Durum:** Sıradaki aktif çalışma.

**Sıra:** Veri envanteri → uygunluk matrisi → metrik sözlüğü doğrulaması → veri modeli → kural kataloğu → etiket motoru → ortak UI bileşenleri → doğrulama.

### Aşama 3 — Ürün ve Kategori

Ürün; satış, stok, fiyat ve müşteri ilişkilerinin ortak referansıdır. İlk uzmanlık modülü olarak ürün performansı, portföy katkısı, yaşam sinyalleri ve etiketleri uygulanır.

### Aşama 4 — Stok

Stok miktarı tek başına değil; ürün önemi, satış hızı, değer, ambar kapsamı ve etiketlerle birlikte değerlendirilir.

### Aşama 5 — Müşteri 360

Müşteri değeri, sipariş ritmi, ürün ilişkisi, iade/indirim davranışı ve kayıp sinyalleri aynı görünümde birleştirilir.

### Aşama 6 — Fiyat ve Maliyet

Fiyat dağılımı, fiyat koridoru, maliyet, indirim ve marj erozyonu ürün ve müşteri bağlamında açıklanır.

### Aşama 7 — Satıcı Performansı

Satıcı performansı yalnız ciro sıralamasıyla değil; portföy yapısı, müşteri sinyalleri, fiyat disiplini, marj ve görev sonuçlarıyla değerlendirilir.

### Aşama 8 — Coğrafi Analiz

Şehir ve ülke bazındaki performans, kapsam kaybı, müşteri yoğunluğu, ürün tercihleri ve bölgesel fırsatlar gösterilir.

### Aşama 9 — Satın Alma ve Stok Dengesi

Satın alma hareketleri satıştan ayrılarak alım, satış ve stok dengesi analiz edilir. Açık sipariş veya tedarik süresi bulunmadan kesin sipariş önerisi üretilmez.

### Aşama 10 — Sepet ve Çapraz Satış

Birlikte alım ve B2B portföy boşluğu fırsatları, ürün uygunluğu, stok ve marj koşullarıyla birlikte üretilir.

### Aşama 11 — Uyarılar ve Anomaliler

Uzmanlık modüllerinin etiket ve sinyalleri tek merkezde birleştirilir. Kural tabanlı uyarı ile istatistiksel anomali ayrı gösterilir.

### Aşama 12 — Aksiyon Merkezi

Uyarı veya analiz görev haline getirilir; sorumlu, termin, sonuç ve ölçülen ticari etki kaydedilir.

### Aşama 13 — Satış ve Kârlılık

Bu sayfa temel modüllerin sonuçlarını birleştiren teşhis katmanıdır. Ciro ve kâr değişiminin ürün, müşteri, stok, fiyat, satıcı ve coğrafya kaynaklarını açıklar.

### Aşama 14 — Yönetim Kokpiti nihai entegrasyonu

Kokpit, tamamlanan modüllerden gelen en önemli sinyalleri, değişim nedenlerini, açık aksiyonları ve ölçülen etkileri yönetime özetler.

### Aşama 15 — Öngörüler ve makine öğrenmesi

Talep tahmini, müşteri kayıp riski, stok riski, dinamik anomali ve segmentasyon modelleri yalnız veri yeterliliği ve referans model başarısı kanıtlandıktan sonra devreye alınır.

## 16. Her aşamada zorunlu çalışma akışı

1. İş soruları yazılır.
2. Gerekli veri alanları ve veri yeterliliği kontrol edilir.
3. Ortak metriklerden kullanılacak olanlar belirlenir.
4. Yeni etiketler ve eşikler kullanıcıyla onaylanır.
5. Üst bar davranışı ve sayfaya özel çekmece filtreleri onaylanır.
6. KPI, grafik, tablo, detay açılımı ve aksiyon noktaları kararlaştırılır.
7. Boş, yükleniyor, veri yetersiz, hata ve karantina durumları tasarlanır.
8. Sayfa taslağı hazırlanır ve kullanıcı onayı alınır.
9. Hesaplama/API katmanı uygulanır.
10. Ortak arayüz bileşenleriyle ön yüz uygulanır.
11. Kaynak kayıtlarla sayısal doğrulama yapılır.
12. Erişilebilirlik, responsive görünüm ve tarayıcı testi yapılır.
13. Belge ve değişiklik kaydı güncellenir.
14. Aşamanın çıkış ölçütü sağlandıktan sonra sonraki aşamaya geçilir.

## 17. Makine öğrenmesine geçiş kapısı

Makine öğrenmesi sırf ürünün “akıllı” görünmesi için kullanılmaz. Her model için aşağıdakiler zorunludur:

- Açık ve ölçülebilir iş sorusu
- Yeterli tarihsel uzunluk ve örnek sayısı
- Eğitim/test ayrımının zaman sırasıyla yapılması
- Veri sızıntısı kontrolü
- Basit kural veya referans modele karşı ölçülebilir iyileşme
- MAE/WAPE gibi uygun hata ölçümleri
- Tahmin aralığı veya güven göstergesi
- Model sürümü ve eğitim dönemi
- Açıklanabilir girdiler
- Model sapması ve yeniden eğitim takibi
- Kullanıcının model çıktısını reddetme veya yanlış işaretleme imkânı

Model çıktıları ayrı ve kopuk bir “AI ekranına” taşınmaz. Mevcut etiket ve sinyal sistemine yeni bir kaynak olarak bağlanır.

---

# Bölüm IV — Ayrıntılı Kapsam Kataloğu

## Amaç

Bu belge, Ticari Öngörü Merkezi demosunun onaylanan menü mimarisini, geliştirme sırasını ve her aşamanın ilerleme koşullarını tanımlar. Çalışma adım adım yürütülür. Bir aşamanın ekran içeriği kullanıcıyla kararlaştırılmadan uygulamaya alınmaz.

## Temel yaklaşım

Uygulama şu karar döngüsünü destekler:

1. Veriyi al ve doğrula.
2. Göstergeleri ortak kurallarla hesapla.
3. Sapma, risk veya fırsatı belirle.
4. Bulguyu kaynak kayıtlarla açıkla.
5. Bulguyu sorumlu ve termin içeren bir aksiyona dönüştür.
6. Sonucu kaydet ve ticari etkisini ölç.
7. Yeterli geçmiş oluştuğunda öngörü modellerini devreye al.

Her analiz kaynağına kadar izlenebilir olmalıdır. Eksik veri, bilinmeyen ambar veya doğrulanmamış hesap kuralı sonuç ekranında görünür. Bu durumlarda sistem kesin sonuç üretmek yerine ilgili ölçümü kısmen hazır veya hesaplanamıyor olarak işaretler.

## Onaylanan menü mimarisi

### 1. Genel Bakış

- Yönetim Kokpiti
- Uyarılar ve Anomaliler

### 2. Ticari Analiz

- Satış ve Kârlılık
- Ürün ve Kategori
- Müşteri 360
- Satıcı Performansı
- Coğrafi Analiz

### 3. Operasyon

- Stok
- Fiyat ve Maliyet
- Satın Alma ve Stok Dengesi

### 4. Fırsatlar

- Sepet ve Çapraz Satış
- Öngörüler

### 5. Yönetim

- Aksiyon Merkezi
- Veri Merkezi

## Sayfa içerik haritası

Bu bölüm, menüdeki her sayfanın hedef içeriğini hiyerarşik olarak tanımlar. Bütün ticari sayfalar ortak üst bardaki tarih, ambar ve satıcı filtrelerini destekler. Fatura türü, ürün grubu, ürün, müşteri, şehir, ülke, etiket ve diğer bağlamsal filtreler ilgili sayfanın sağ çekmecesinde kullanıcıyla önceden kararlaştırılır. Kullanıcı bir KPI, grafik noktası, etiket veya tablo satırından ilgili hareket ve fatura satırlarına inebilmelidir.

### 1. Genel Bakış

#### 1.1 Yönetim Kokpiti

**Üst KPI alanı**

- Net satış
- Brüt satış
- Satış iadesi
- Toplam indirim
- Satış maliyeti
- Brüt ticari kâr
- Brüt marj
- Yerine koyma maliyetine göre kâr
- Yerine koyma maliyetine göre marj
- Satılan miktar
- Fatura sayısı
- Aktif müşteri sayısı
- Aktif ürün sayısı
- Ortalama fatura tutarı
- Müşteri başına ciro
- Ürün başına ciro

**Karşılaştırmalar**

- Önceki aya göre tutar ve yüzde değişim
- Önceki yılın aynı dönemine göre tutar ve yüzde değişim
- Seçilen dönemin önceki eşit uzunluktaki döneme göre değişimi
- Satış değişiminin miktar, fiyat, müşteri ve ürün bileşenleri
- Gerçekleşen kâr ile yerine koyma kârı farkı

**Yönetim grafikleri**

- Zaman içinde net satış, kâr ve marj eğilimi
- Fiyat Şelalesi (Price Waterfall): Brüt satıştan net satışa ve kâra geçiş, iskonto ve maliyet sızıntıları
- Brüt satıştan net satışa geçiş: iade ve indirim etkisi
- Satış ve kâr katkısına göre ilk ürün grupları
- Satış ve kâr katkısına göre ilk müşteriler
- Satıcı bazında ticari performans
- Ambar bazında satış, hareket ve stok kapsamı
- Şehir veya ülke bazında satış dağılımı

**Risk ve fırsat özeti**

- Satışı düşen ürün ve müşteriler
- Düşük marjlı veya zararına satışlar
- Kritik ve fazla stok adayları
- Stokta karşılığı olmayan hareket ambarları
- Sıfır maliyet ve tanımsız fatura türü bulguları
- Açık ve gecikmiş aksiyonlar

**Detay tabloları**

- Ürün, müşteri, satıcı ve ambar bazında karşılaştırmalı performans
- En yüksek artış ve düşüş gösteren kayıtlar
- KPI hesaplarına dahil edilmeyen veya güven sorunu bulunan kayıtlar

#### 1.2 Uyarılar ve Anomaliler

**Özet KPI alanı**

- Açık uyarı sayısı
- Kritik uyarı sayısı
- Yeni uyarı sayısı
- İncelenen uyarı sayısı
- Göreve dönüşen uyarı sayısı
- Kapatılan uyarı sayısı
- Uyarıların etkilediği net satış, kâr veya stok değeri
- Ortalama açık kalma süresi

**Uyarı türleri**

- Ani satış düşüşü veya artışı
- Müşteri Churn Erken Uyarısı (Z-Score Sipariş Sapması >= 2.0)
- Fiyat Koridoru Dışı Satış (Taban fiyat sızıntısı veya aşırı iskonto)
- Müşteri sipariş gecikmesi
- Müşterinin bıraktığı ürün veya kategori
- Yüksek satış iadesi
- Olağandışı indirim
- Olağandışı satış fiyatı
- Sıfır maliyet
- Düşük marjlı veya zararına satış
- Kritik stok
- Fazla veya hareketsiz stok
- Hareket bulunan fakat stoku bilinmeyen ambar
- Fatura türü ve miktar işareti uyumsuzluğu
- Tarih, tekrar ve veri dönüşüm anomalileri

**Uyarı listesi**

- Önem derecesi
- Uyarı türü
- İlgili müşteri, ürün, satıcı veya ambar
- Kanıt dönemi
- Beklenen ve gerçekleşen değer
- Ticari etki
- Veri güven düzeyi
- Sorumlu
- Durum ve termin

**Uyarı detayı**

- Uyarının neden üretildiği
- Kullanılan eşik ve kural sürümü
- Geçmiş dönem karşılaştırması
- Kaynak fatura ve hareket satırları
- Olası açıklamalar
- Aksiyon oluşturma ve yanlış uyarı olarak işaretleme

### 2. Ticari Analiz

#### 2.1 Satış ve Kârlılık

**Üst KPI alanı**

- Brüt satış
- Satış iadesi
- Net satış
- Toplam indirim
- İndirim oranı
- Satış maliyeti
- Brüt ticari kâr
- Ağırlıklı brüt marj
- Yerine koyma maliyetine göre kâr ve marj
- Satılan miktar
- Fatura sayısı
- Ortalama fatura tutarı
- Fatura başına ürün çeşidi

**Fiyat Şelalesi (Price Waterfall) Analizi**

- Brüt Liste Hasılatı -> Sözleşme İndirimleri -> Fatura Altı İskontolar -> İade ve Düzeltmeler -> Net Satış -> Satılan Malın Maliyeti (COGS) -> Brüt Ticari Kâr
- Kâr sızıntı noktalarının (Leakage) tutar ve yüzde payı
- Dönemsel ve müşteri bazında şelale karşılaştırması

**Zaman analizi**

- Günlük, haftalık, aylık ve yıllık satış eğilimi
- Satış, maliyet, kâr ve marjın birlikte değişimi
- Önceki ay ve önceki yıl karşılaştırması
- Hareketli satış ve marj ortalaması
- En yüksek ve en düşük performans dönemleri

**Kârlılık kırılımları**

- Ürün ve ürün grubu
- Müşteri
- Satıcı
- Ambar
- Şehir ve ülke
- Fatura türü
- Birim

**Kontrol ve fırsat listeleri**

- Zararına satışlar
- Sıfır maliyetli satışlar
- En düşük ve en yüksek marjlı satışlar
- Yüksek indirimli işlemler
- İade oranı yüksek ürün ve müşteriler
- Kayıtlı kâr ile yeniden hesaplanan kârı uyuşmayan satırlar
- Gerçekleşen ve yerine koyma kârı arasında büyük fark bulunan satışlar

#### 2.2 Ürün ve Kategori

**Üst KPI alanı**

- Aktif ürün sayısı
- Aktif ürün grubu sayısı
- Net satış
- Satılan miktar
- Ticari kâr ve marj
- Ürün başına ciro
- Ürün başına müşteri sayısı
- Ürün başına ortalama satış fiyatı
- Ürün başına ortalama fatura sayısı
- Satışı olmayan stoklu ürün sayısı

**Ürün performansı**

- Ürün bazında satış, miktar, kâr ve marj
- Ürün grubu bazında katkı
- Önceki ay ve önceki yıl karşılaştırması
- Satış büyüme ve düşüş sıralaması
- Satış, kâr ve müşteri katkısına göre ABC sınıflaması
- Ciro payı ile kâr payı karşılaştırması
- Ürünün müşteri ve satıcı yaygınlığı

**Fiyat ve maliyet görünümü**

- Ortalama, en düşük ve en yüksek satış fiyatı
- Müşteriler arasındaki fiyat farkı
- Kayıtlı ve yerine koyma maliyeti
- Gerçekleşen ve yerine koyma marjı
- İndirim ve iade oranı

**Ürün yaşam sinyalleri**

- Yeni satılmaya başlayan ürünler
- Satışı hızlanan ürünler
- Satışı yavaşlayan ürünler
- Satışı duran ürünler
- Belirli müşterilerde bırakılan ürünler
- Stoku olup satış görmeyen ürünler

**Ana veri kontrolleri**

- Aynı ürün kodundaki farklı açıklamalar
- Aynı ürün kodundaki farklı kategoriler
- Birim ve içerik tutarsızlıkları
- Eksik ürün veya kategori bilgileri

**Ürün detay sayfası**

- Ürün kimliği, açıklaması, kategorisi, birimi ve içeriği
- Satış, kâr, marj ve fiyat geçmişi
- Müşteri ve satıcı dağılımı
- Ambar bazında stok
- İade ve indirim geçmişi
- İlgili uyarılar ve aksiyonlar

#### 2.3 Müşteri 360

**Üst KPI alanı**

- Aktif müşteri sayısı
- Yeni müşteri sayısı
- Tekrar alışveriş yapan müşteri sayısı
- Uzun süredir alışveriş yapmayan müşteri sayısı
- Müşteri başına ciro
- Müşteri başına kâr
- Ortalama fatura tutarı
- Ortalama alışveriş sıklığı
- Ortalama ürün ve kategori çeşidi
- Müşteri iade oranı

**Müşteri segmentleri ve Churn Erken Uyarı Skoru**

- Churn Erken Uyarı Skoru (Z-Score): Sipariş periyodundan 2 standart sapma uzaklaşan riskli müşteriler
- Churn Risk Matrisi: Kritik Risk (Z >= 2.0), Uyarı (1.0 <= Z < 2.0), Normal (Z < 1.0)
- Yeni müşteriler
- Aktif müşteriler
- Düzenli müşteriler
- Satışı büyüyen müşteriler
- Satışı azalan müşteriler
- Geciken müşteriler
- Uzun süredir alışveriş yapmayan müşteriler
- Yüksek ciro, düşük marj müşterileri
- Yüksek kâr katkılı müşteriler
- Tek ürüne veya kategoriye bağımlı müşteriler

**Müşteri performans tablosu**

- Net satış, miktar, kâr ve marj
- Fatura sayısı ve ortalama fatura tutarı
- İlk ve son alışveriş tarihi
- Ortalama sipariş aralığı
- Ürün ve kategori çeşitliliği
- İade ve indirim oranı
- İlgili satıcı, şehir ve ülke
- Önceki ay ve önceki yıl değişimi

**Müşteri davranışı**

- Satın alma zaman çizelgesi
- Alışveriş sıklığı ve gecikme
- Satın alınan ve bırakılan ürünler
- Satın alınan ve bırakılan kategoriler
- Birlikte alınan ürünler
- Ürün ve kategori boşlukları
- Fiyat ve indirim profili

**Müşteri detay sayfası**

- Kimlik, unvan, cari tipi ve konum
- İlgili satıcı
- Ticari performans özeti
- Fatura ve ürün geçmişi
- Sipariş ritmi
- Sepet ve çapraz satış fırsatları
- Açık uyarı ve aksiyonlar

#### 2.4 Satıcı Performansı

**Üst KPI alanı**

- Aktif satıcı sayısı
- Atanmamış satış tutarı ve oranı
- Satıcı başına satış
- Satıcı başına kâr
- Satıcı başına müşteri sayısı
- Satıcı başına ürün sayısı
- Ortalama fatura tutarı
- Ortalama marj
- İade ve indirim oranı

**Performans karşılaştırması**

- Satış, kâr, marj ve miktar sıralaması
- Önceki ay ve önceki yıl değişimi
- Aktif, yeni, azalan ve geciken müşteri sayısı
- Ürün ve kategori çeşitliliği
- Portföy yoğunlaşması
- Düşük marjlı satış payı
- Yüksek indirim ve iade payı

**Portföy görünümü**

- Satıcının müşteri listesi
- Müşteri başına satış ve kâr
- Müşteri risk ve fırsatları
- Satıcının güçlü ve zayıf ürün kategorileri
- Bölgesel dağılım
- Açık uyarı ve görevler

**Satıcı detay sayfası**

- Dönemsel performans
- Müşteri kazanımı ve kaybı
- Müşteri ziyaret veya teklif verisi geldiğinde saha performansı
- Tamamlanan görevler ve ölçülen sonuçlar

#### 2.5 Coğrafi Analiz

**Üst KPI alanı**

- Aktif ülke sayısı
- Aktif şehir sayısı
- Konumu eksik müşteri ve satış oranı
- Şehir başına satış ve kâr
- En yüksek satışlı şehir
- En yüksek marjlı şehir

**Coğrafi performans**

- Ülke, şehir ve posta kodu bazında satış
- Bölge bazında kâr ve marj
- Aktif müşteri ve ürün sayısı
- Ortalama fatura tutarı
- İade ve indirim oranı
- Önceki ay ve önceki yıl değişimi

**Harita ve dağılımlar**

- Satış yoğunluğu haritası
- Kâr ve marj haritası
- Müşteri yoğunluğu
- Ürün ve kategori tercihleri
- Satıcıların coğrafi portföyü

**Fırsat ve kapsam listeleri**

- Satışı büyüyen ve daralan şehirler
- Benzer müşteri yapısına rağmen düşük satışlı bölgeler
- Belirli ürün veya kategorinin zayıf olduğu bölgeler
- Konum bilgisi eksik kayıtlar
- Sevkiyat adresi doluluk durumu

### 3. Operasyon

#### 3.1 Stok

**Üst KPI alanı**

- Toplam stok miktarı
- Tekil birime çevrilebilen stok miktarı
- Kayıtlı stok değeri
- KDV dahil stok değeri
- Yerine koyma stok değeri
- Aktif stoklu ürün sayısı
- Stoksuz ürün sayısı
- Negatif stok sayısı
- Çöp ambarı miktarı ve değeri
- Hareket bulunan fakat stoku bilinmeyen ambar sayısı

**Stok performansı**

- Ambar bazında miktar ve değer
- Ürün ve kategori bazında stok
- Stok değerinin ürün gruplarına dağılımı
- Satış hızı ile stok miktarı karşılaştırması
- Tahmini stok kapsama günü
- Stok devir hızı ve sermaye verimliliği
- Önceki stok görüntüleri biriktikçe stok değişimi

**Risk listeleri**

- Kritik stok adayları
- Fazla stok adayları
- Hareketsiz stok adayları
- Stoku bulunup satışı olmayan ürünler
- Satışı bulunup stoku bilinmeyen ürün ve ambarlar
- Negatif stoklar
- Değeri yüksek fakat hareketi düşük ürünler
- Çöp ambarındaki ürünler

**Stok detay sayfası**

- Ürün ve ambar bazında mevcut miktar
- Kayıtlı ve yerine koyma değeri
- Son dönem satış hızı
- Tahmini kapsama süresi
- İlgili müşteri talebi
- Uyarı ve aksiyon geçmişi

**Koşullu analizler**

- Kesin yeniden sipariş noktası için tedarik süresi ve güvenlik stoğu gerekir.
- Gerçek fire oranı için tarihli fire hareketi gerekir.
- Raf ömrü riski için parti ve son kullanma tarihi gerekir.

#### 3.2 Fiyat ve Maliyet

**Üst KPI alanı**

- Ortalama gerçekleşen satış fiyatı
- Ortalama kayıtlı maliyet
- Ortalama yerine koyma maliyeti
- Gerçekleşen kâr ve marj
- Yerine koyma kârı ve marjı
- İndirimli satış oranı
- Zararına satış tutarı
- Sıfır maliyetli satış tutarı
- Fiyat anomalisi sayısı

**Fiyat analizi ve Fiyat Koridoru (Price Dispersion & Corridor)**

- Ürün bazında Fiyat Dağılımı (Boxplot: Min, %25 Çeyreklik Q1, Medyan, %75 Çeyreklik Q3, Max)
- Dinamik Fiyat Koridoru tanımlaması (İdeal taban ve tavan fiyat aralığı)
- Fiyat Koridoru altı satışlar (Marj sızıntısı / Fiyat erozyonu)
- Müşteri ve satıcı bazında fiyat saçılımı
- Ürün bazında ortalama, en düşük ve en yüksek fiyat
- Müşteri bazında fiyat farkları
- Satıcı bazında fiyat farkları
- Şehir ve ülke bazında fiyat farkları
- Zaman içinde fiyat değişimi
- Miktar ile gerçekleşen birim fiyat ilişkisi
- İndirim oranı ve marj ilişkisi

**Maliyet analizi**

- Kayıtlı maliyet ile yerine koyma maliyeti farkı
- Maliyet değişiminin ürün ve kategori dağılımı
- Maliyet artışının marj üzerindeki etkisi
- Kayıtlı satır maliyeti ile yeniden hesaplanan maliyet farkı
- Maliyeti eksik veya sıfır kayıtlar

**Kontrol listeleri**

- Zararına satışlar
- Hedefin altında marjlı satışlar
- Aynı ürün için olağandışı düşük veya yüksek fiyatlar
- Gerçekleşen ve yerine koyma marjı arasında büyük fark bulunan ürünler
- Yüksek indirimli müşteriler ve faturalar

#### 3.3 Satın Alma ve Stok Dengesi

**Üst KPI alanı**

- Net satın alma tutarı
- Net satın alma miktarı
- Satın alma iadesi
- Ortalama satın alma fiyatı
- Alım yapılan ürün sayısı
- Alım bulunan ambar sayısı
- Net alış ile net satış farkı
- Alım yapıldığı halde satış görmeyen ürün sayısı

**Denge analizi**

- Ürün bazında alış, satış ve stok
- Ürün grubu bazında alış ve satış dengesi
- Ambar bazında giriş, çıkış ve mevcut stok
- Dönemsel satın alma ve satış eğilimi
- Satın alma fiyatı ile satış maliyeti karşılaştırması
- Alım miktarı ile satış hızı karşılaştırması

**Risk listeleri**

- Satış hızının üzerinde alım yapılan ürünler
- Satış olmadığı halde alımı süren ürünler
- Satış hızının altında alım yapılan ürünler
- Yüksek stok değerine rağmen düşük satış gösteren ürünler
- Alım yapılan fakat stok görüntüsünde bulunmayan ürünler

**Koşullu analizler**

- Tedarikçi performansı için cari rolünün ve tedarikçi kimliğinin doğrulanması gerekir.
- Sipariş önerisi için açık sipariş, beklenen giriş, tedarik süresi ve minimum sipariş miktarı gerekir.

### 4. Fırsatlar

#### 4.1 Sepet ve Çapraz Satış

**Üst KPI alanı**

- Analize giren satış faturası sayısı
- Ortalama sepet tutarı
- Ortalama sepet ürün çeşidi
- Tek ürünlü fatura oranı
- Birlikte alınan ürün çifti sayısı
- Öneri üretilebilen müşteri sayısı
- Tahmini fırsat kapsamı

**Sepet analizi**

- En sık birlikte alınan ürünler
- En sık birlikte alınan kategoriler
- Destek, güven ve lift değerleri
- Ürün bazında tamamlayıcı ürünler
- Müşteri segmentine göre sepet farkları
- Satıcı ve bölge bazında sepet yapısı

**White-Spot (Portföy Boşluğu) Analizi ve Fırsatlar**

- Müşteri Portföy Boşluğu Matrisi (Aynı segment/sektördeki akran müşterilerin %70+ aldığı fakat hedef müşteride eksik ürünler)
- Müşteri bazında kaçırılan ciro potansiyeli (White-Spot fırsat tutarı)
- Ürün yaygınlaştırma öncelik sıralaması
- Bir ürünü alıp tamamlayıcı ürünü almayan müşteriler
- Benzer müşterilere göre eksik kategoriler
- Geçmişte aldığı ürünü artık almayan müşteriler
- Stokta bulunan ve marjı uygun tamamlayıcı ürünler
- Fazla stokla eşleşen geçmiş alıcılar

**Öneri detayı**

- Önerilen ürün
- Önerinin gerekçesi
- Benzer müşteri veya geçmiş alış kanıtı
- Destek, güven ve lift
- Mevcut stok ve marj
- İlgili müşteri ve satıcı
- Aksiyona dönüştürme

#### 4.2 Öngörüler

**Üst KPI alanı**

- Tahmin kapsamına giren ürün sayısı
- Tahmin kapsamına giren müşteri sayısı
- Yeterli geçmişi olmayan seri sayısı
- Güncel tahmin hatası
- Aşırı ve eksik tahmin yönü
- Kritik stok riski taşıyan ürün sayısı
- Siparişi gecikmesi beklenen müşteri sayısı

**Talep tahmini**

- Ürün ve kategori bazında haftalık satış tahmini
- Müşteri ve ürün bazında beklenen talep
- Tahmin alt ve üst aralığı
- Gerçekleşen ve tahmin edilen satış
- Basit referans modelle karşılaştırma
- Tahmin hatası ve yönlü sapma

**Müşteri öngörüleri**

- Beklenen sonraki sipariş tarihi
- Sipariş gecikme riski
- Müşteri satış düşüşü riski
- Ürün veya kategori bırakma riski
- Tahmini müşteri değeri için veri yeterliliği

**Stok öngörüleri**

- Yaklaşan kritik stok riski
- Fazla stok riski
- Tahmini stok kapsama süresi
- Tahmin ve mevcut stok karşılaştırması
- Tedarik verisi geldiğinde önerilen sipariş zamanı

**Model izleme**

- Model sürümü ve eğitim dönemi
- Son test dönemi
- MAE, WAPE ve yönlü hata
- Basit modele göre iyileşme
- Veri kalitesi ve model sapması
- Modelin kullanıma açık veya kapalı olma durumu

### 5. Yönetim

#### 5.1 Aksiyon Merkezi

**Üst KPI alanı**

- Açık görev sayısı
- Gecikmiş görev sayısı
- Bugün tamamlanacak görev sayısı
- Tamamlanan görev sayısı
- Zamanında tamamlama oranı
- Sonuçlanan görev sayısı
- Satışa dönüşen aksiyon sayısı
- Ölçülen ek satış ve ek kâr

**Görev listesi**

- Görev başlığı ve türü
- Kaynak uyarı veya analiz
- Müşteri, ürün, satıcı veya ambar
- Sorumlu
- Öncelik
- Oluşturma ve termin tarihi
- Durum
- Beklenen ticari etki
- Gerçekleşen sonuç

**Görev detayı**

- Uyarı ve kanıt kayıtları
- Önerilen aksiyon
- Görüşme veya işlem notları
- İlgili faturalar
- Durum geçmişi
- Kapanış nedeni
- Aksiyon sonrası ölçüm dönemi
- Satış, kâr, marj veya stok etkisi

**Yönetim görünümleri**

- Sorumlu bazında açık ve gecikmiş görevler
- Uyarı türüne göre sonuç oranı
- Görevlerin zamanında tamamlanma oranı
- Yanlış uyarı nedenleri
- Tekrar eden görevler
- Aksiyonların ticari sonuçları

#### 5.2 Veri Merkezi

**Aktarım alanı**

- Stok CSV yükleme
- Hareket CSV yükleme
- Dosya kodlaması ve ayraç seçimi
- Kolon eşleştirme
- Stok görüntü tarihi
- Dönüşüm önizlemesi
- Aktarım onayı

**Veri sağlığı**

- Şema uygunluğu
- Tamlık
- Geçerlilik
- Tutarlılık
- Veri güncelliği
- Ambar kapsamı
- Modül hazırlığı

**Kalite kontrolleri**

- Eksik zorunlu ve isteğe bağlı alanlar
- Tarih ve sayı dönüşümü
- Sıfır maliyet
- Fatura türü
- Birim ve paket içeriği
- Negatif stok
- Fatura türü ve miktar işareti
- Ay ve yıl tutarlılığı
- Tekrar adayı ve önceki aktarımla çakışma

**Aktarım geçmişi**

- Dosya adı ve veri türü
- Yükleme zamanı ve veri dönemi
- Toplam, kabul edilen ve karantinadaki kayıt
- Uyarı ve hata sayısı
- Aktarımı yapan kullanıcı bilgisi ileride eklenebilir
- Ham dosya ve kalite raporu bağlantısı

**Kural ve kapsam yönetimi**

- Fatura türü sözlüğü
- Birim dönüşüm sözlüğü
- Ambar eşleştirmeleri
- Zorunlu alan tanımları
- Uyarı eşikleri
- Kural sürümü ve değişiklik geçmişi
- Hangi modülün hangi veri nedeniyle hazır olmadığı

## Mevcut durum

### Tamamlanan çalışma

- Stok ve hareket CSV dosyalarının içe aktarılması
- Kolon adı ve kolon sırası doğrulaması
- Türkçe karakter, tarih ve ondalık ayracı desteği
- Ham dosyanın korunması
- Hatalı kayıtların karantinaya alınması
- Tekrar yükleme kontrolü
- Şema uygunluğu, tamlık, geçerlilik ve tutarlılık ölçümleri
- Veri güncelliği ve ambar kapsamı kontrolleri
- Modül bazında hazır olma durumu
- Kaynak satır ve hata detayı incelemesi
- Veri kalitesi raporunun CSV olarak dışa aktarılması

### Mevcut veri kaynakları

- Hareket verisi: satış, satış iadesi, satın alma ve satın alma iadesi hareketleri
- Stok verisi: ürün ve ambar bazında anlık stok görüntüsü

### Mevcut veriyle açık kalan kararlar

- Fatura türlerinin işaret kuralları iş örnekleriyle kesinleştirilmeli.
- İndirimin birim fiyat ve net satır tutarına etkisi doğrulanmalı.
- Birim ve paket içeriği dönüşümleri ürün bazında onaylanmalı.
- Yerine koyma maliyetinin birim veya satır toplamı anlamı kesinleştirilmeli.
- Hareket verisindeki üç ambarın stok kaynağında karşılığı bulunmuyor.
- Sıfır maliyet kayıtlarının bedelsiz ürün veya veri hatası olduğu ayrıştırılmalı.

## Tarihsel uygulama aşamaları — kapsam arşivi

> [!WARNING]
> Bu bölüm ilk planın kapsamını veri kaybı olmadan korur; artık geliştirme sırası olarak kullanılmaz. Bağlayıcı sıra **Bölüm III — Güncel aşama sırası** bölümündedir. Aşağıdaki maddeler ilgili güncel aşamaların kapsamına taşınarak uygulanacaktır.

### Aşama 0 — Veri Merkezi

**Durum:** Tamamlandı, kalite kuralları geliştirilmeye devam edebilir.

**Amaç:** Analizlerde kullanılacak verinin kapsamını, sağlığını ve izlenebilirliğini güvenceye almak.

**İlerleme koşulu:** Kullanılacak ticari hesapların gerekli alanları mevcut olmalı ve kritik veri hataları görünür olmalı.

### Aşama 1 — Ortak uygulama iskeleti

**Kapsam:**

- Onaylanan grup yapısıyla ana menü
- Bütün sayfalarda varsayılan `Tüm Zamanlar (2023–2024)` dönem filtresi
- Ortak üst barda ambar ve satıcı filtreleri; diğer filtrelerin sayfaya özel çekmecede yönetilmesi
- Aktif filtre özeti
- Veri kapsamı ve son güncelleme bilgisi
- Tüm sayfalarda ortak boş, yükleniyor ve hesaplanamıyor durumları
- KPI veya grafik üzerinden kaynak kayda detay açılımı

**İlerleme koşulu:** Aynı filtre seçimi bütün sayfalarda aynı kayıt kapsamını üretmeli.

### Aşama 2 — Yönetim Kokpiti

**Kapsam:**

- Net satış
- Satış iadesi
- Satış maliyeti
- Gerçekleşen ticari kâr
- Ağırlıklı marj
- İndirim
- Fatura ve müşteri sayısı
- Stok miktarı ve stok değeri
- Dönemsel satış ve kâr eğilimi
- Ürün, müşteri, satıcı ve kategori katkısı
- Kritik kalite, stok ve ticari uyarılar

**İlerleme koşulu:** Gösterilen satış, iade, maliyet ve kâr toplamları seçilen örnek faturalarla uzlaşmalı.

### Aşama 3 — Satış ve Kârlılık

**Kapsam:**

- Brüt ve net satış
- İade ve indirim etkisi
- Fatura sayısı ve ortalama fatura tutarı
- Fatura başına ürün çeşidi
- Satış miktarı ve dönemsel değişim
- Gerçekleşen kâr ve ağırlıklı marj
- Ürün, müşteri, satıcı ve kategori kırılımları
- Kayıtlı maliyet ile yerine koyma maliyetinin karşılaştırılması
- Düşük marjlı ve zararına satışlar

**İlerleme koşulu:** İndirim, iade ve maliyet kuralları kaynak faturayla doğrulanmalı.

### Aşama 4 — Ürün ve Kategori

**Kapsam:**

- Ürün ve kategori bazında satış, miktar, kâr ve marj
- Dönemsel büyüme ve düşüş
- En çok ve en az katkı sağlayan ürünler
- Müşteri erişimi ve tekrar satın alma
- Fiyat ve marj dağılımı
- Ürün açıklaması ve kategori tutarsızlıkları
- Satışı düşen veya duran ürünler
- Stokla birlikte ürün risk görünümü

**İlerleme koşulu:** Ürün kodları ana anahtar olarak kullanılmalı, birim karşılaştırmaları doğrulanmalı.

### Aşama 5 — Müşteri 360

**Kapsam:**

- Müşteri bazında satış, kâr, marj ve iade
- İlk ve son alışveriş tarihi
- Alışveriş sıklığı ve ortalama sipariş aralığı
- Ortalama fatura ve ürün çeşitliliği
- Satın alınan ürün ve kategori geçmişi
- Yeni, aktif, azalan ve uzun süredir alışveriş yapmayan müşteri grupları
- Bırakılan ürün veya kategori sinyali
- Müşteri fiyat ve indirim profili
- İlgili satıcı ve coğrafi bilgiler

**İlerleme koşulu:** Müşteri kodu tekil anahtar olmalı, satış dışındaki cari roller ayrıştırılmalı.

### Aşama 6 — Stok

**Kapsam:**

- Ürün ve ambar bazında stok miktarı
- Kayıtlı ve yerine koyma stok değeri
- Kullanılabilir stok ile çöp ambarı bakiyesinin ayrılması
- Satış hızına göre stok kapsama görünümü
- Kritik, fazla ve hareketsiz stok adayları
- Ambarlar arası kapsam farkları
- Satış hareketi bulunan ancak stoku bilinmeyen ambarlar
- Ürün bazında stok ve satış ilişkisi

**İlerleme koşulu:** Stok görüntü tarihi ve ambar kapsamı görünür olmalı. Bilinmeyen ambarlar sıfır stok olarak yorumlanmamalı.

### Aşama 7 — Fiyat ve Maliyet

**Kapsam:**

- Gerçekleşen satış fiyatı
- Ürün ve müşteri bazında fiyat farkları
- Kayıtlı maliyet ile yerine koyma maliyeti farkı
- Gerçekleşen ve yerine koyma kârı karşılaştırması
- Düşük marjlı ve zararına satışlar
- İndirimlerin marj üzerindeki etkisi
- Olağandışı fiyat ve maliyet kayıtları

**İlerleme koşulu:** Para birimi, vergi temeli ve maliyet alanlarının birim veya toplam anlamı doğrulanmalı.

### Aşama 8 — Satıcı ve Coğrafya

**Satıcı kapsamı:**

- Satış, kâr, marj ve müşteri sayısı
- Ortalama fatura tutarı
- Portföy yoğunlaşması
- İade ve indirim oranı
- Ürün ve kategori çeşitliliği
- Atanmamış satışlar

**Coğrafya kapsamı:**

- Şehir ve ülke bazında satış, kâr ve marj
- Bölgesel müşteri ve ürün yoğunluğu
- Bölgesel ürün tercihleri
- Fiyat ve performans farkları
- Eksik konum kapsamı

**İlerleme koşulu:** Satıcı ve konum alanlarındaki kapsam kaybı her sonuçla birlikte gösterilmeli.

### Aşama 9 — Satın Alma ve Stok Dengesi

**Kapsam:**

- Ürün bazında net alış ve net satış
- Satın alma maliyeti değişimi
- Alım ve satış eğilimlerinin karşılaştırılması
- Satış olmadığı halde alımı süren ürünler
- Satış hızına göre yüksek alım veya stok riski
- Ambar bazında stok dengesizliği

**İlerleme koşulu:** Satın alma ve satış işlemleri fatura türüyle güvenilir biçimde ayrılmalı. Açık sipariş ve tedarik süresi olmadan kesin sipariş önerisi üretilmemeli.

### Aşama 10 — Uyarılar ve Anomaliler

**Kapsam:**

- Ani satış değişimleri
- Olağandışı fiyat ve maliyet
- Sıfır maliyet veya zararına satış
- Yüksek iade
- Geciken müşteri
- Müşterinin bıraktığı ürün veya kategori
- Kritik ve fazla stok
- Tekrar adayı kayıtlar
- Stokta karşılığı olmayan hareket ambarları

Her uyarı kaynak dönemini, kanıt kayıtlarını, olası açıklamayı ve etkilenen ölçüyü göstermelidir.

**İlerleme koşulu:** Uyarı eşikleri, asgari veri miktarı ve tekrar üretme süresi kayıt altına alınmalı.

### Aşama 11 — Aksiyon Merkezi

**Kapsam:**

- Uyarı veya analizden görev oluşturma
- Sorumlu, termin, öncelik ve durum
- İlgili müşteri, ürün, ambar veya fatura bağlantısı
- Görüşme ve kapanış nedeni
- Tekrar görev kontrolü
- Aksiyon sonrası satış, kâr ve marj değişimi
- Görev tamamlama ve sonuç ölçümü

**İlerleme koşulu:** Her görev kaynak bulguya ve üretildiği kural sürümüne bağlı olmalı.

### Aşama 12 — Sepet ve Çapraz Satış

**Kapsam:**

- Birlikte alınan ürün ve kategoriler
- Destek, güven ve lift ölçümleri
- Tamamlayıcı ürün önerileri
- Müşteri sepetindeki ürün boşlukları
- Geçmiş alıcı ve benzer müşteri fırsatları
- Stok, marj ve müşteri uygunluğu filtresi

**İlerleme koşulu:** Yalnız satış faturaları kullanılmalı. İade ve satın alma hareketleri sepet eğitimine karışmamalı.

### Aşama 13 — Öngörüler

**Kapsam:**

- Haftalık ürün talep tahmini
- Müşterinin sonraki sipariş zamanı
- Satış düşüşü ve müşteri kaybı riski
- Kritik stok ve fazla stok riski
- Tahmin aralıkları
- Basit referans yöntemle model karşılaştırması
- Model hata ve sapma izlemesi

**İlerleme koşulu:** Geçmiş uzunluğu ve düzeni her model için yeterli olmalı. Eğitim ve test dönemleri zaman sırasıyla ayrılmalı. Yeni model basit yönteme göre ölçülebilir fayda göstermeli.

## Mevcut veriyle tamamlanamayacak ileri modüller

Aşağıdaki alanlar ek kaynak gerektirir:

- Tahsilat, vade ve açık bakiye analizi
- Kredi limiti ve finansal risk
- Açık müşteri ve satın alma siparişleri
- Beklenen giriş tarihi ve tedarik süresi
- Güvenlik stoğu ve minimum sipariş miktarı
- Parti ve son kullanma tarihi
- Gerçek dönem fire maliyeti
- Prim tutarı ve prim takvimi
- Teklif, ziyaret ve saha görüşmesi geçmişi
- Ülkeler arası ortak para birimi analizi

Bu veriler gelene kadar ilgili modüller sonuç üretmez veya açık biçimde veri bekleniyor durumunda kalır.

## Geliştirme çalışma biçimi

> [!CRITICAL]
> ### ⚠️ KESİN ÖN KOŞUL KURALI: Sayfa Öncesi Filtreleme Mimarisi Onayı
> **HİÇBİR SAYFA, O SAYFAYA ÖZEL FİLTRELEME YAPISI KULLANICIYLA NETLEŞTİRİLİP ONAYLANMADAN KODLANMAYA BAŞLANAMAZ!**
> Her sayfanın geliştirmesine geçilmeden önce:
> 1. Global filtreler (Tarih, Ambar, Satıcı vb.) dışında, **o sayfaya özel sağdan kayan çekmecede (Slide-over Drawer) hangi bağlamsal filtrelerin yer alacağı** tek tek listelenmeli ve kullanıcıya sunulmalıdır.
> 2. Örneğin **Yönetim Kokpiti** kodlanmadan önce; fatura türü, marj seviyesi, müşteri segmenti gibi çekmece filtrelerinin hangilerinin dahil edileceği karara bağlanmalıdır.
> 3. Kullanıcı bu filtre listesini onaylamadan arayüz veya hesaplama kodlamasına geçilmesi kesinlikle yasaktır.

Her sayfa için şu sıra izlenir:

0. **Sayfaya Özel Filtre Setinin Kararlaştırılması:** Global bar ve sağ çekmeceden gelecek filtreler netleştirilir ve kullanıcı onayı alınır.
1. İş soruları belirlenir.
2. KPI ve hesaplama kuralları onaylanır.
3. Filtreler ve detay açılımları belirlenir.
4. Sayfa taslak görünümü hazırlanır.
5. Kullanıcı tasarımı onaylar.
6. Arayüz ve hesaplama katmanı uygulanır.
7. Sonuçlar kaynak satırlarla doğrulanır.
8. Bir sonraki sayfaya geçilir.

## Teknik yapı

- Arayüz: React ve Next.js
- API katmanı: Next.js üzerinde Node.js
- Veri analizi ve kalite kuralları: Python
- Yerel veri saklama: SQLite ve ham CSV arşivi
- Testler: Python birim testleri ve tarayıcı üzerinden uçtan uca testler

## İlk sıradaki çalışma

Bir sonraki aktif çalışma **Aşama 2 — Etiketleme ve sinyal altyapısıdır**. Önce veri alanı envanteri ve etiket uygunluk matrisi hazırlanacak; ardından ortak metrikler doğrulanacak, kural kataloğu ve etiket motoru kurulacak, son olarak ortak etiket bileşenleri ön yüzde gösterilecektir. Bu aşamanın çıkış ölçütleri sağlanmadan Ürün ve Kategori sayfasına geçilmez.


---

## Onaylanan İleri Analitik Metodolojiler ve İş Kuralları Detayı

Bu bölüm; yönetim kararlarını hızlandırmak ve sektör standartlarında ticari zeka üretmek amacıyla yol haritasına eklenen 4 temel metodolojinin matematiksel modellerini, iş kurallarını ve uygulama esaslarını tanımlar.

### 1. Fiyat Şelalesi (Price Waterfall) Metodolojisi

**Amaç:** Brüt fatura cirosundan nihai brüt kâra ulaşana kadar şirketin nerede, hangi aşamada marj kaybettiğini (kâr sızıntısı) şeffaf bir şelale grafiği ile görselleştirmek ve sızıntı noktalarını yönetilebilir kılmak.

**Şelale Adımları ve Hesaplama:**
1. **Brüt Satış Tutarı (Gross Revenue):** Toplam (Miktar x Liste Birim Fiyatı)
2. **Satır İskontoları (-):** Satır bazında uygulanan doğrudan indirim tutarları.
3. **Fatura Altı İndirimler (-):** Toplam faturaya uygulanan dönemsel veya ciro iskontoları.
4. **İadeler ve Fiyat Düzeltmeleri (-):** İade faturaları ve iskonto farkları.
5. **= Net Satış Hasılatı (Net Revenue):** Şirketin tahakkuk eden net ticari cirosu.
6. **Satılan Malın Maliyeti / COGS (-):** Ürünün ağırlıklı ortalama kayıtlı maliyeti (veya yerine koyma maliyeti).
7. **= Brüt Ticari Kâr (Gross Margin Value):** Net Satış - COGS.
8. **Brüt Kâr Marjı (%):** (Brüt Ticari Kâr / Net Satış) x 100.

**Aksiyon Kuralları:**
- Fatura altı iskontoların net ciroya oranı %10'u aştığında ilgili müşteri veya satıcı için "Aşırı İskonto Sızıntısı" uyarısı üretilir.
- İade oranı %3'ü geçen ürün ve müşterilerde kök neden analizi görevi açılır.

---

### 2. Müşteri Churn Erken Uyarı Skoru (Z-Score Sipariş Sapması)

**Amaç:** B2B müşterilerin sipariş frekansları birbirinden çok farklıdır (Kimi haftalık, kimi aylık, kimi 45 günde bir sipariş verir). Sabit bir gün eşiği (örn. 30 gün) yerine her müşterinin kendi tarihsel sipariş ritmine göre dinamik ve matematiksel bir terk (churn) riski hesaplamak.

**Matematiksel Model:**
1. **Müşteri Sipariş Aralıkları Serisi:** Müşterinin ardışık siparişleri arasındaki gün farkları hesaplanır: Δt1, Δt2, ..., Δtn.
2. **Ortalama Sipariş Aralığı (μ):** Müşterinin iki sipariş arasındaki ortalama gün süresi.
3. **Sipariş Aralığı Standart Sapması (σ):** Müşterinin sipariş verme düzenliliği / oynaklığı.
4. **Son Siparişten Beri Geçen Gün (T_gecen):** Bugünün tarihi ile son fatura tarihi arasındaki fark.
5. **Z-Score Formülü:**
   Z = (T_gecen - μ) / σ

**Risk Seviyeleri ve Otomasyon:**
- **Normal (Z < 1.0):** Müşteri doğal sipariş ritmi içindedir.
- **Takip / Erken Uyarı (1.0 <= Z < 2.0):** Sipariş gecikmeye başlamıştır; sistem satıcıya "Müşteri Arama Hatırlatması" çıkarır.
- **Kritik Churn Riski (Z >= 2.0):** İstatistiki olarak %95 güven aralığının dışına çıkılmıştır. Müşteri kaybedilmek üzeredir. Aksiyon Merkezi'nde doğrudan ticari yöneticiye "Acil Churn Önleme Görevi" atanır.

---

### 3. Fiyat Dağılımı ve Fiyat Koridoru (Price Dispersion & Corridor / Boxplot)

**Amaç:** Aynı ürünün farklı müşterilere çok farklı fiyatlardan satılmasını (fiyat erozyonu ve marj kaybı) engellemek; ürün bazında adil ve kârlı bir "Fiyat Koridoru" oluşturmak.

**Metodoloji:**
1. **Veri Kümesi:** Seçilen dönemde ilgili SKU için gerçekleşen net birim satış fiyatları.
2. **Kutu Grafiği (Boxplot) Metrikleri:**
   - **Taban Fiyat (Q1 - %25 Çeyreklik):** Fiyatların en düşük %25'lik sınır çizgisi.
   - **Medyan Fiyat (Q2 - %50):** Piyasa denge fiyatı.
   - **Tavan Fiyat (Q3 - %75 Çeyreklik):** Yüksek fiyatlandırma sınırı.
   - **Fiyat Koridoru:** [Q1, Q3] aralığı şirketin "İdeal Satış Fiyatı Koridoru"dur.
3. **Fiyat Sızıntısı (Price Leakage):** Satış Fiyatı < Q1 olan tüm satışlar "Fiyat Erozyonu" olarak etiketlenir. Bu satışların toplam cirodaki marj kaybı Euro cinsinden hesaplanır.
4. **Fiyat Gücü (Pricing Power):** Satış Fiyatı >= Q3 olan satışlar, müşterinin fiyat esnekliğinin düşük olduğunu ve kâr marjının maksimize edildiğini gösterir.

**Aksiyon Kuralları:**
- Taban fiyatın (Q1) altında iskonto veren satıcılar ve müşteriler için "Fiyat Koridoru Aşımı" uyarısı açılır.

---

### 4. White-Spot (Portföy Boşluğu) Analizi

**Amaç:** B2C tipi sepette birlikte alma algoritmaları yerine, B2B toptan satışın doğasına uygun olan akran analiziyle (Peer Group Analysis) müşterilerin sepetindeki "Eksik Ürünleri" belirlemek ve ciro artışı sağlamak.

**Metodoloji:**
1. **Akran Kümelerinin Oluşturulması (Peer Clustering):** Müşteriler; sektör, ciro büyüklüğü, coğrafi bölge veya satın alma profiline göre benzer kümelere ayrılır.
2. **Kategori / Ürün Penetrasyon Oranı:** İlgili müşteri kümesindeki firmaların % kaçının X ürününü düzenli olarak satın aldığı hesaplanır (Penetrasyon(X)).
3. **Boşluk (White-Spot) Tespiti:**
   - Eğer bir kümede Penetrasyon(X) >= %70 ise, bu ürün o küme için "Standart Portföy Ürünü" kabul edilir.
   - Hedef müşteri bu kümede olmasına rağmen X ürününü son 6 ayda hiç almamışsa, bu durum **"White-Spot (Portföy Boşluğu)"** olarak işaretlenir.
4. **Kaçırılan Ciro Potansiyeli:** Hedef müşterinin büyüklüğü ile akranların ortalama X ürünü tüketim tutarı çarpılarak "Müşteri Bazlı Kaçırılan Potansiyel Ciro" Euro olarak hesaplanır.

**Aksiyon Kuralları:**
- Satış temsilcilerine ziyaret veya görüşme öncesinde *"Müşterinin Portföy Boşluğu Raporu"* tek tıkla PDF/görev olarak iletilir. Satıcı masaya doğrudan nokta atışı teklifle gider.


---

## Filtre Mimarisi, Yerleşim ve Etkileşim Standartları (UI / UX)

Her analitik sayfada veriyi daraltmak, karşılaştırmak ve kök nedene inmek için kullanılacak filtreleme mekanizması 3 düzeyde ve modern bir kullanıcı deneyimiyle kurgulanmıştır.

### 1. Filtre Seviyeleri ve Taksonomi

#### A. Global Filtreler (Her Sayfada Ortak ve Senkron)
- **Tarih ve Dönem:**
  - **Varsayılan:** Tüm Zamanlar (2023–2024).
  - **Seçenekler:** Tüm Zamanlar, tek ayın bütün yıllardaki toplamı, ay + yıl, yıl ve özel tarih aralığı.
  - **Karşılaştırma Modu (Compare Toggle):** "Önceki Dönem (PoP)" veya "Önceki Yılın Aynı Dönemi (YoY)".
- **Ambar / Depo (Warehouse):** Merkez, Frischlager_Merkez, Cöp vb. (Çoklu veya tekil seçim).
- **Satış Temsilcisi / Satıcı (Sales Rep):** Satıcı bazlı performans filtreleme ve atanmamış satışlar seçeneği.

Ürün kategorisi, ürün, müşteri, coğrafya ve fatura türü global değildir; ilgili modülün bağlamsal çekmecesinde kararlaştırılır.

#### B. Modüle Özel Bağlamsal Filtreler (Contextual Filters)
- **Satış ve Kârlılık:** Fatura Türü (Normal Satış, İade), Marj Durumu (Zararına Satışlar, Düşük Marjlılar <%15, Normal, Yüksek).
- **Müşteri 360:** Müşteri Segmenti (Yeni, Düzenli, Riskli/Churn Adayı, Uyuyan Müşteri).
- **Stok:** Stok Durumu (Kritik Stok <15 gün, Normal, Fazla Stok >60 gün, Hareketsiz/Ölü Stok, Negatif Stok).
- **Fiyat ve Maliyet:** İskonto Seviyesi (>%10, >%20), Fiyat Koridoru Durumu (Koridor Altı Marj Sızıntısı).

#### C. Veri Sağlığı ve Güven Filtresi (Quality Toggle)
- **Karantina / Sıfır Maliyet Anahtarı:** "Sıfır maliyetli ve güven sorunu olan satırları analize dahil et" (Varsayılan: Kapalı / Hariç Tutulur).

---

### 2. Onaylanan Standart: Hibrit Filtreleme Mimarisi (Model 1 + Model 2)

Projede kullanıcı onayıyla **Hibrit Filtreleme Modeli (Kompakt Üst Şerit + Sağdan Kayan Gelişmiş Çekmece)** standart arayüz mimarisi olarak kabul edilmiştir.

> [!IMPORTANT]
> **Sayfa Geliştirme Kuralı:** 
> Her sayfa için kodlamaya başlamadan önce, o sayfanın **sağdan kayan çekmecesinde hangi filtrelerin bulunacağı kullanıcıyla birlikte kesinleştirilecektir.** Bu karar verilmeden hiçbir sayfa implementasyonuna başlanamaz.

#### Bileşen 1: Kompakt Akıllı Alt Şerit (Sticky Sub-Header Bar) — [Her Sayfada Sabit]
- **Konum:** Sayfa başlığının hemen altında yer alan ve kaydırmada üstte yapışan (sticky) 48px yüksekliğinde ince şerit.
- **İçerik:**
  - **İnteraktif Tarih Hapı:** `[ Tüm Zamanlar (2023–2024) ▾ ]` (Tıklandığında dönem seçici ve karşılaştırma seçenekleri açılır).
  - **Hızlı Seçim Hapları:** `[ Ambar: Tümü (5) ▾ ]`, `[ Satıcı: Tümü ▾ ]`.
  - **Sağ Köşe:** `[ ⚙️ Gelişmiş Filtreler (Çekmeceyi Aç) ]` ve `[ ✕ Filtreleri Sıfırla ]`.

#### Bileşen 2: Sağdan Kayan Gelişmiş Filtre Çekmecesi (Slide-Over Drawer) — [Sayfaya Özel]
- **Konum:** Sağ üstteki buton tıklandığında ekranın sağından açılan 380px genişliğinde dikey çekmece.
- **İçerik:** Her sayfanın kendi analitik ihtiyacına göre önceden kararlaştırılan özel filtreler (Örn: Zararına satışlar, Müşteri Churn riski, Fiyat koridoru dışı kayıtlar vb.).

#### Model 1: Kompakt Akıllı Alt Başlık Şeridi (Sticky Sub-Header Bar) — [ÖNERİLEN STANDART]
- **Konum:** Sayfa başlığının hemen altında yer alan ve sayfa kaydırıldığında üstte sabitlenen (sticky) 48px yüksekliğinde ince, zarif bar.
- **Bileşenler:**
  - **Sol:** İnteraktif Tarih Hapı (`[ Tüm Zamanlar (2023–2024) ▾ ]`). Tıklandığında dönem seçici ve karşılaştırma anahtarı açılır.
  - **Orta:** Hızlı Seçim Hapları (`[ Ambar: Tümü (5) ▾ ]`, `[ Satıcı: Tümü ▾ ]`).
  - **Sağ:** `[ ⚙️ Gelişmiş Filtreler (2 Aktif) ]` ve `[ ✕ Temizle ]` butonları.
- **Avantajı:** Görsel grafik alanından çalmaz, kullanıcı her zaman hangi veri evreninde olduğunu net biçimde görür.

#### Model 2: Sağdan Kayan Gelişmiş Filtre Çekmecesi (Slide-Over Drawer)
- **Konum:** Kullanıcı detaylı müşteri, fatura türü veya marj filtrelemesi yapmak istediğinde sağ köşedeki *"Filtreler"* butonuna tıklar; ekranın sağından 380px genişliğinde dikey bir çekmece açılır.
- **Avantajı:** Onlarca filtrenin ana arayüzü boğmasını engeller; profesyonel SaaS görünümü sağlar.

#### Model 3: Başlıkla Bütünleşik Tarih Bağlamı (Hero Date Context) — Kullanılmayan alternatif
- **Not:** Tarih bağlamı başlığa gömülmez; onaylanan ortak üst barda tutulur. Bu alternatif yalnız karar geçmişini korumak amacıyla belgelenmiştir.

#### Model 4: Çapraz Etkileşimli Filtreleme (Cross-Filtering / Click-to-Filter)
- **Konum:** Doğrudan grafiklerin üzeri.
- **Etkileşim:** Kullanıcı aylık satış trendi grafiğinde "Ekim 2024" sütununa veya Kategori grafiğinde "Yumuşak Şeker" çubuğuna tıkladığında, sayfadaki tüm KPI'lar ve tablolar anında o seçime göre yeniden hesaplanır.


---

## Tasarım ve Arayüz Standardı: Profesyonel Vektör (SVG) Kuralı

> [!CRITICAL]
> ### 🎨 KURUMSAL TASARIM VE İKON STANDARDI: Yapay Zeka Emojileri Kesinlikle Yasaktır
> - **Arayüzde (UI), butonlarda, sekmelerde, uyarılarda ve etiketlerde kesinlikle yapay zeka tarafından üretildiği hissi veren renkli emojiler (📅, 🗓️, 🔴, 🟡, 🟢, 🔍, 📊, ⚙️ vb.) KULLANILMAYACAKTIR.**
> - Bunun yerine her zaman **Lucide-React veya modern SVG vektör ikonları** kullanılacaktır.
> - Durum bildirimlerinde (risk, başarı, uyarı) renkli emojiler yerine CSS tabanlı şık durum noktaları (`status-dot`), rozetler (`badge`) veya SVG sembolleri tercih edilecektir.
> - Amaç: B2B kurumsal yazılım standartlarına uygun, sade, minimalist ve profesyonel bir SaaS deneyimi sunmaktır.

---

## Yönetim Kokpiti (Executive Dashboard) — Alınan Kararlar ve Nihai Spesifikasyon

Yönetim Kokpiti sayfası tasarlanırken kullanıcı ile birlikte karara bağlanan tüm ilkeler aşağıda kayıt altına alınmıştır:

### 1. Zaman ve Açılış Kapsamı
- **Varsayılan Görünüm:** Kokpit ilk açıldığında **Tüm Zamanlar (2023–2024)** kümülatif verisi ile yüklenir.
- **Tek Ay Kümülatif Seçimi:** Tarih filtresinde yıl belirtilmeden sadece bir ay (örn. "Mayıs") seçildiğinde, 2023 Mayıs ve 2024 Mayıs verileri kümülatif olarak toplanır (Mevsimsellik analizi).
- **Ay + Yıl Seçimi:** Yıl ve ay birlikte seçildiğinde (örn. "Mayıs 2024") sadece o döneme odaklanır.
- **Özel Aralık Desteği:** Kullanıcı dilediği başlangıç ve bitiş tarihlerini belirleyebilir.

### 2. Fatura Türleri ve Satış vs. Satın Alma Ayrımı
- **Satın Alma Faturaları:** Satın alma ve satın alma iadesi faturaları ciro/satış hesaplarına **asla dahil edilmez**; operasyon ve stok dengesi sayfalarında ayrı işlenir.
- **Satış Faturaları & İadeler:** Yönetim kokpitinde yalnızca Satış Faturaları ve Satış İade Faturaları işlenir.
- **İade Politikası Anahtarı:** Sağ çekmecede yer alan `Satış İadelerini Dahil Et / Düş` seçeneği ile kullanıcı isterse net satış cirosunu (iadeler düşülmüş), isterse brüt fatura büyüklüğünü tek tıkla izleyebilir.

### 3. Karantina Satırları ve Excel Modalı
- Sıfır maliyetli satırlar (162 satış satırı) kârlılık oranlarını bozmaması için karantinada tutulur.
- Bu satırlar gizlenmez; Risk Paneli üzerinden tıklandığında açılan tam ekran **Excel Modalı** içerisinde canlı arama kutusu ve CSV/Excel indirme butonuyla şeffafça sunulur.

### 4. Filtreleme Mimarisi (Onaylanan Hibrit Model)
- **Kompakt Üst Bar:** İnteraktif Tarih Hapı, Ambar Seçici, Satıcı Seçici ve Filtre Sıfırla butonu.
- **Sağdan Kayan Çekmece:** İade politikası anahtarı, Marj durumu (Tümü / Zararına / Düşük / Yüksek), Malzeme Grubu çoklu seçimi, Şehir filtresi ve Sıfır Maliyet Karantina anahtarı.
- **Müşteri Filtresi:** Kokpitten bilinçli olarak çıkarılmıştır; Müşteri 360 sayfasında ele alınacaktır.

### 5. Grafikler ve İnteraktivite
- **Dinamik Zaman Trendi:** Yakınlaştırma (Zoom In / Out / Slider) kontrollerine sahiptir. Grafikte bir aya tıklandığında sayfa otomatik olarak o aya filtrelenir (Cross-filtering).
- **Fiyat Şelalesi (Price Waterfall):** Brüt Satış -> İskonto -> Satış İadesi -> Net Satış -> COGS -> Brüt Kâr adımlarıyla kâr erozyonunu şeffaflaştırır.
- **Detay Tabloları:** Kategori, Müşteri, Satıcı ve Ambar kırılımlarında sekmeli ve aranabilir performans tabloları yer alır.

---

# Bölüm V — Yönetişim, Test ve Değişiklik Yönetimi

## 18. Karar bekleyen konular kayıt şablonu

Yeni bir konu karara bağlanana kadar aşağıdaki biçimde bu bölüme eklenir:

```text
Karar No:
Konu:
Etkilenen modüller:
Mevcut durum:
Seçenekler:
Önerilen seçenek:
Karar sahibi:
Son karar:
Karar tarihi:
Yol haritasında güncellenen bölümler:
```

Karar verilmemiş bir madde uygulamada kesin iş kuralı gibi kullanılmaz.

## 19. Veri uygunluk matrisi şablonu

| Analiz/etiket | Gerekli alanlar | Kaynak | Veri durumu | Güven düzeyi | Eksik karar | Sonuç |
|---|---|---|---|---|---|---|
| Örnek: Düşük marjlı ürün | Ürün, net satış, maliyet, tarih | Hareket | Mevcut | Doğrulama bekliyor | Sıfır maliyet davranışı | Yaklaşık üretilebilir |

Sonuç alanı yalnız şu değerlerden birini alır:

- **Üretilebilir:** Alanlar ve iş anlamı doğrulandı.
- **Yaklaşık üretilebilir:** Sonuç üretilebilir fakat sınırlama açıkça gösterilmelidir.
- **Yeni veri gerektirir:** Kaynak alan bulunmamaktadır.
- **Güvenilmez:** Alan vardır fakat anlamı veya kalitesi karar üretmek için yeterli değildir.

## 20. Test stratejisi

### 20.1 Hesaplama testleri

- Her ortak metrik için bilinen küçük örnek veriyle birim testi
- Satış, iade, satın alma ve satın alma iadesinin doğru ayrıştırılması
- Sıfır maliyet ve karantina davranışı
- Dönem ve saat sınırı testleri
- Euro biçimlendirmesi ve negatif tutarlar
- Ağırlıklı marj ile satır marjı ortalamasının karıştırılmaması

### 20.2 Etiket motoru testleri

- Eşiğin hemen altı, eşitliği ve hemen üstü
- Asgari veri koşulu
- Aynı verinin tekrar işlenmesinde tekrar kayıt oluşmaması
- Kural sürümü değişince geçmişin korunması
- Aktif etiketin sona ermesi ve tekrar açılması
- Çakışan etiketlerin birlikte gösterimi
- Kanıt değerlerinin kaynak hesapla uzlaşması

### 20.3 API ve entegrasyon testleri

- Global filtrelerin bütün modüllerde aynı kapsamı üretmesi
- Sayfa özel filtresinin yalnız ilgili kapsamı değiştirmesi
- Etiket listesinden kaynak detaya iniş
- Uyarı ve aksiyon bağlantılarının kimlik bütünlüğü
- Büyük veri ve sayfalama davranışı

### 20.4 Arayüz testleri

- Masaüstü ve mobil kırılımlar
- Sabit sol menü ve kaydırılabilir ana içerik
- Klavye kullanımı ve görünür odak
- Rengin tek başına bilgi taşımaması
- Boş, yükleniyor, hata, veri yetersiz ve karantina durumları
- Filtre sıfırlama ve sayfalar arası filtre devamlılığı
- Grafik çapraz filtreleme ve geri alma

### 20.5 İş kabul testi

Her modül için seçilmiş örnek ürün, müşteri, fatura veya ambar kayıtları elle hesaplanarak ekran sonucuyla karşılaştırılır. Sayısal uzlaşma belgelendirilmeden modül tamamlandı olarak işaretlenmez.

## 21. Tamamlanmışlık tanımı

Bir aşama ancak aşağıdaki koşulların tamamı sağlandığında tamamlanmıştır:

- Onaylı kapsam uygulanmıştır.
- Hesaplamalar kaynak veriyle doğrulanmıştır.
- İlgili etiketler ve filtreler çalışmaktadır.
- Veri yetersizliği ve kalite sorunları görünürdür.
- Ortak terim ve tasarım standardına uyulmuştur.
- Testler başarılıdır.
- İlgili dokümantasyon günceldir.
- Açık kalan konular karar bekleyenler listesine taşınmıştır.
- Bir sonraki aşamanın giriş bağımlılıkları karşılanmıştır.

## 22. Değişiklik yönetimi kuralları

- Yeni fikir doğrudan aktif geliştirmeye eklenmez; önce ilgili aşama ve bağımlılık belirlenir.
- Kapsam eklemek mevcut aşamanın çıkış ölçütünü değiştiriyorsa kullanıcı onayı gerekir.
- Metrik formülü değişirse etkilenen etiketler, uyarılar, sayfalar ve geçmiş sonuçlar listelenir.
- Kural eşiği değişirse yeni sürüm oluşturulur; eski sürüm geçmiş kayıtlarda korunur.
- Menü sırası değişikliği veri veya iş kuralı kapsamını silmez.
- Uygulanmayacak bir özellik silinmek yerine gerekçesiyle ertelenmiş veya iptal edilmiş olarak kaydedilir.

## 23. Güncel karar özeti

| Konu | Nihai karar |
|---|---|
| Ortak üst bar | Tarih, ambar, satıcı, sıfırla ve sayfa filtreleri düğmesi |
| Varsayılan dönem | Bütün sayfalarda Tüm Zamanlar (2023–2024) |
| Diğer filtreler | Sayfaya özel sağ çekmece; uygulama öncesi kullanıcı onayı |
| Para birimi | Euro (€) |
| Tema | Lacivert/koyu mavi gezinme ve açık içerik yüzeyleri |
| Sonraki aktif çalışma | Etiketleme ve sinyal altyapısı |
| Etiket yaklaşımı | Önce ortak altyapı ve güvenilir ilk katalog; modüle özel kurallar sayfa öncesi tamamlanır |
| Kavram zinciri | Etiket → sinyal → uyarı/anomali → aksiyon |
| İlk uzmanlık modülü | Ürün ve Kategori |
| Satış ve Kârlılık | Temel modüllerden sonra birleşik teşhis katmanı |
| Yönetim Kokpiti | İlk sürüm tamam; daha sonra birleşik sinyal entegrasyonu |
| Makine öğrenmesi | Temel modüller ve doğrulanmış sinyal sistemi sonrasında |
| Fiyat şelalesi | Şimdilik gerçekleşen brüt satıştan başlar; liste fiyatı gelince genişletilir |

## 24. Değişiklik geçmişi

### 21 Eylül 2026 — Yol haritasının ana kılavuza dönüştürülmesi

- Eski yol haritası ve yeni etiketleme odaklı plan veri kaybı olmadan birleştirildi.
- Ortak filtreler tarih, ambar ve satıcıyla sınırlandırıldı; diğer filtreler sayfaya özel çekmeceye taşındı.
- Bütün sayfaların varsayılan dönemi Tüm Zamanlar (2023–2024) olarak kesinleştirildi.
- Etiket, sinyal, uyarı, anomali ve aksiyon kavramları ayrıştırıldı.
- Etiket motoru, kural kataloğu, veri modeli, yaşam döngüsü ve ortak UI standardı eklendi.
- Bağlayıcı geliştirme sırası etiketleme → ürün → stok → müşteri → fiyat/maliyet → satıcı → coğrafya → satın alma/stok dengesi → sepet/çapraz satış → uyarılar/anomaliler → aksiyon merkezi → satış/kârlılık → kokpit entegrasyonu → öngörüler olarak değiştirildi.
- Yönetim Kokpiti ilk sürümü tamamlandı, nihai sinyal entegrasyonu ileriki aşamaya alındı.
- Demo para birimi Euro olarak kesinleştirildi.
- Petrol yeşili yönün yerini lacivert/koyu mavi tasarım sistemi aldı.
- Fiyat şelalesinde mevcut veri ile genişletilmiş liste fiyatı modeli ayrıştırıldı.

## 25. Aktif çalışma kontrol listesi

### Aşama 2 — Etiketleme ve sinyal altyapısı

- [ ] Hareket ve stok alan envanterini çıkar
- [ ] Etiket uygunluk matrisini doldur
- [ ] Açık veri anlamı kararlarını kesinleştir
- [ ] Ortak metrik testlerini yaz
- [ ] Analitik özet tablolarını tasarla
- [ ] Etiket ve kural tablolarını tasarla
- [ ] İlk kural kataloğunu yapılandır
- [ ] Veri kalitesi etiketlerini uygula
- [ ] Güvenilir ürün, stok, müşteri ve satış etiketlerini uygula
- [ ] Önem/sinyal puanlamasını uygula
- [ ] Ortak etiket API sözleşmesini oluştur
- [ ] `TagBadge`, etiket özeti ve kanıt detayını oluştur
- [ ] Etiket, önem ve durum filtrelerini oluştur
- [ ] Kaynak kayıt bağlantısını doğrula
- [ ] Tekrar üretim ve sürüm testlerini çalıştır
- [ ] İş kabul örneklerini belgeleyerek aşamayı kapat

Bu kontrol listesi tamamlandığında bir sonraki iş, **Ürün ve Kategori sayfasının iş soruları, etiketleri ve sağ çekmece filtrelerini kullanıcıyla kararlaştırmaktır.**

## 26. Ürün etiketleme modülü — onaylanan kararlar

- Uygulamada veri tarihinden bağımsız, kullanıcı tarafından seçilebilen global **Analiz Tarihi** bulunur. Varsayılan hareket verisinin son günü olan 30 Aralık 2024'tür.
- Resmî etiketler veri sonu tarihinde kalıcılaştırılır; farklı analiz tarihleri simülasyon olarak hesaplanır ve resmî geçmişi değiştirmez.
- Güncel ve önceki karşılaştırma pencereleri ardışık 90 günlük dönemlerdir.
- Stok tablosu hareket tablosuna ürün koduyla bağlanır. Stok kaynağı bu aşamada ağırlıklı olarak maliyet, yerine koyma maliyeti, paket/koli içeriği ve yardımcı ürün bilgisi sağlar.
- Satış ve satış iadeleri ürün performansına girer; satın alma hareketleri girmez.
- Sıfır maliyetli satırlar ciro, miktar, fatura ve müşteri kapsamına girer; kâr, marj ve maliyet etiketlerinden çıkarılır.
- Ciro payı momentumu, ürünün son 90 gündeki toplam şirket cirosu payı ile önceki 90 gündeki payının farkıdır. İlk %20 hızlanan, orta %60 dengeli, son %20 yavaşlayan kabul edilir.
- Marj sınıfları zararına `<%0`, düşük `%0–15`, normal `%15–30`, yüksek `≥%30` olarak uygulanır. En az 5 yüzde puan değişim güçlenme veya erozyon etiketidir.
- Fiyat ve maliyet değişimleri kategori/portföy içindeki `%20–60–20` dağılımıyla değerlendirilir. Maliyet artışının fiyat artışını en az 5 yüzde puan aşması `Fiyat maliyetin gerisinde` etiketidir.
- Yerine koyma alanı satır toplamıdır. Birim yerine koyma maliyeti `satır toplam yerine koyma maliyeti / mutlak miktar`; yerine koyma kârı `net satış − yerine koyma maliyeti`; yerine koyma marjı `yerine koyma kârı / net satış` olarak yeniden hesaplanır.
- Müşteri erişimi tekil müşteri, yeni/tekrar/bırakan müşteri ve müşteri yoğunlaşmasıyla ölçülür. Tek müşterinin payı `%60` üzerindeyse bağımlılık, ilk üç müşterinin payı `%80` üzerindeyse yoğunlaşma etiketi üretilir.
- İade etiketi için son 90 günde en az dört satış faturası güven eşiğidir. Düşük hacimde oran gösterilir fakat risk etiketi verilmez. Kaybedilen ciro ve brüt kâr ile aynı frekans sürerse gelecek 90 gün etkisi ayrı gösterilir.
- Fiyat koridoru son 180 günde aynı birimde en az sekiz satış satırı ve üç müşteri bulunan ürünlerde Q1–Q3 aralığıyla hesaplanır.
- Ürün listesinde öncelik sırasına göre iki etiket gösterilir; kalanlar `+N` altında açılır. Kanıt detayında dönem, gerçekleşen, referans, değişim, Euro etkisi, güven ve kural sürümü bulunur.
- Sinyal puanı Euro etkisi `%40`, eşikten sapma `%30`, portföy katkısı `%20`, devam süresi `%10` bileşimidir. 40–59 dikkat, 60–79 yüksek, 80–100 kritik düzeyidir.
- Yüksek ve kritik sinyaller Uyarılar ve Anomaliler merkezine aktarılmaya uygundur; otomatik görev Aksiyon Merkezi aşamasına kadar üretilmez.
- Gelecekte ayrı bir İade Analizi sayfası; müşteri, ürün, kategori, ciro ve kâr etkisini birleştirecek şekilde kapsam havuzuna eklenmiştir. Menü konumu ilgili aşamada kararlaştırılacaktır.

## 27. Ürün ve Kategori modülü — uygulanan ilk sürüm

**Durum:** Ürün karar alanı, kategori katkısı, ABC portföyü ve kaynak hareket izine iniş dahil çalışan ürün modülü tamamlandı. Dışa aktarım ve sağ çekmece genişletmesi kullanıcı kabul turuna bırakıldı.

### 27.1 Ana sayfa yapısı

- Global `Analiz Tarihi` üst barda korunur ve ürün hesaplarının tamamını etkiler.
- Türkçe karakter, aksan ve büyük/küçük harf farkından etkilenmeyen ürün kodu/adı araması bulunur.
- Ürünler `En çok satan`, `En çok ciro` ve `En çok kâr` görünümleri arasında sıralanabilir.
- Her ürün satırında ürün kodu, kategori, seçilen ana metrik, tekil müşteri sayısı ve öncelikli iki etiket gösterilir.
- KPI alanı aktif ürün sayısı, 90 günlük net satış, ticari kâr ve yüksek/kritik sinyal sayısını gösterir.
- Sayfaya özel sağ çekmece şimdilik malzeme grubu ve yalnız riskli ürün seçimini içerir. Yeni filtreler sayfa ihtiyacı kesinleşmeden eklenmez.

### 27.2 Ürün detay paneli

- Ürün kimliği ve en önemli üç etiketi
- Son 90 günlük net satış, kâr, marj, müşteri, fatura ve iade etkisi
- Son 180 günün aylık satış fiyatı ve birim maliyet grafiği
- Kayıtlı birim maliyet ile yerine koyma kârı ve marjı
- Aynı birimde en az sekiz pozitif satış satırı ve üç müşteriye dayanan Q1–Q3 fiyat koridoru
- Stok kaynağından miktar, stok değeri, paket/koli içeriği ve ambar kapsamı
- Son 90 gündeki en çok iade eden müşteriler, iade tutarı ve aynı frekans sürerse gelecek 90 gün iade etkisi

### 27.3 Hesap tutarlılığı kararları

- Detay panelindeki iade müşteri listesi ve üst iade KPI'ı aynı son 90 günlük pencereyi kullanır.
- Fiyat koridoruna sıfır tutarlı veya sıfır birim fiyatlı satış satırları girmez.
- Sıfır maliyetli satışlar hacim metriklerinde kalır; kâr, maliyet ve marj hesaplarından ayrıştırılır.
- Ürün detayı farklı analiz tarihi seçildiğinde yeniden hesaplanır; simülasyon sonuçları resmî etiket geçmişini değiştirmez.

### 27.4 Sonraki ürün modülü turu

1. Kategori katkı ve yoğunlaşma görünümü
2. Ürün/kategori ABC sınıflaması ve ciro-kâr payı karşılaştırması
3. Etiket veya ürün detayından kaynak hareket satırlarına iniş
4. Arama, filtre ve liste sonuçlarında CSV/Excel dışa aktarım
5. Kullanıcı kabul turundan sonra sağ çekmece filtrelerinin genişletilmesi

### 27.5 Ürün modülü ikinci tur kararları ve uygulaması

- `Ciro–kâr farkı` sıralaması eklendi. Ham Euro tutarları karşılaştırılmaz; ürünün portföy ciro payı ile pozitif kâr havuzundaki kâr payı arasındaki mutlak yüzde puan farkı kullanılır. İşaret ve metin farkın yönünü açıklar.
- Satış sinyalleri `Hızlanan`, `Yavaşlayan`, `Duran` ve `Yeni hareket` seçimleriyle doğrudan filtrelenebilir.
- Fiyat–maliyet grafiğinde işaretçiyle üzerine gelinen ayın satış fiyatı, birim maliyeti ve marjı gösterilir.
- Ürün ekonomisi aynı ölçü biriminde sunulur: birim satış fiyatı, kayıtlı birim maliyet, yerine koyma birim maliyeti, yerine koyma birim kârı ve yerine koyma marjı.
- Birim maliyetler yalnız geçerli maliyetli satış satırlarının toplam maliyetinin satış miktarına bölünmesiyle hesaplanır. İade etkisi toplam kâr/marj hesabında kalır; satış birim maliyetini bozmaz.
- Ürün detayına son 90 günde ürünü satın alan müşteriler eklendi. Müşteri başına ciro, miktar, fatura sayısı ve ağırlıklı ortalama alış fiyatı hesaplanır.
- Lider ürün kaynak uzlaştırmasında 295 satış satırı ve 1.663 birim üzerinden kayıtlı birim maliyet `17,64 €`, yerine koyma birim maliyeti `18,23 €`, yerine koyma birim kârı `5,50 €` olarak doğrulandı.

### 27.6 Ürün modülü üçüncü tur — kategori, ABC ve veri izi

- Ana ürün alanına `Kategori katkısı` görünümü eklendi. En yüksek ciroyu üreten ilk sekiz kategori için ürün sayısı, net satış payı ve kâr payı yan yana gösterilir. Böylece yüksek hacimli fakat görece düşük kâr üreten kategoriler tek bakışta ayrışır.
- Kategori satırları çapraz filtre görevi görür. Bir kategoriye tıklanınca mevcut arama, satış sinyali ve risk filtreleri korunarak ürün listesi ilgili kategoriye iner; filtre durumu üstte görünür hale gelir.
- ABC sınıflaması ürünlerin 90 günlük net satışına göre azalan sıralanmış kümülatif katkı üzerinden hesaplanır: `A = ilk %80`, `B = sonraki %15`, `C = kalan %5`. Eşik sınırını geçen ürün, sınıfın toplam katkısının eksik kalmaması için başladığı sınıfta tutulur.
- ABC, bir hacim/yoğunlaşma göstergesidir; tek başına ürünün iyi veya kötü olduğunu söylemez. Karar verirken marj, yerine koyma ekonomisi, müşteri erişimi, iade ve satış momentumu sinyalleriyle birlikte okunur.
- Her ürün satırında ABC sınıfı ürün kodu ve kategoriyle beraber gösterilir. Ayrı portföy özeti A, B ve C sınıflarındaki ürün sayısını ve eşiklerin anlamını açıklar.
- Ürün detay paneline `Kaynak satış hareketleri` bölümü eklendi. Seçilen analiz tarihine göre son 90 gündeki satış/iade hareketleri tarih, fatura, müşteri, tür, miktar, birim fiyat, birim maliyet, net tutar ve kaynak dosya satırıyla izlenebilir.
- Performans ve okunabilirlik için hareket tablosu en yeni ilk 100 satırı gösterir; başlıkta toplam hareket sayısı ayrıca korunur. Böylece örneğin lider üründe 295 hareket bulunduğu, görünümün bunların ilk 100'ünü sunduğu açıkça belirtilir.
- Kaynak hareket tablosu varsayılan olarak kapalıdır; yalnız ihtiyaç halinde açılır. Bu karar ürün detayının bir karar özeti olarak kalmasını, kanıt verisinin ise erişilebilir fakat ikincil olmasını sağlar.
- Canlı kabul kontrolünde `10.CEKIRDEK` seçimi ürün listesini 181 üründen 8 ürüne indirmiş; lider ürün detayında 295 hareket ve gerçek kaynak satır numaraları başarıyla gösterilmiştir.
- Teknik kabul: 19 analiz testi ve Next.js üretim derlemesi hatasız tamamlanmıştır.

### 27.7 Ürün modülünde açık kalan kontrollü işler

1. Liste ve kaynak hareketleri için CSV/Excel dışa aktarımı
2. Kullanıcı kabulünden sonra sağ çekmeceye eklenmesi gerçekten gerekli görülen filtreler
3. İade Analizi sayfası geliştirildiğinde ürün detayından ilgili ürünün iade görünümüne geçiş

Bu maddeler ürün modülünün mevcut karar akışını engellemez. Bağlayıcı geliştirme sırasındaki bir sonraki ana aşama **Stok modülüdür**; sayfa uygulanmadan önce stok sayfasına özel sağ çekmece filtreleri ve stok kaynağının karar soruları netleştirilecektir.

## 28. Stok modülü — tüketim hızına bağlı demo stok modeli

### 28.1 Veri kapsamı ve tarih kararı

- `DepoStokDurumu.csv` içindeki miktar, ambar ve parasal toplamlar fiziksel stok olarak kullanılmaz. Kaynak bu modülde yalnız ürünün koli/paket içeriğini eşlemek için kullanılır.
- Bunun nedeni kaynaktaki `Çöp` ve `Merkez` ambarlarının kullanılabilirlik ayrımının belirsiz olması, miktarların kesirli paket eşdeğerleri içermesi ve tüm satış portföyünü kapsamamasıdır.
- Demo stok fotoğrafı ortak analiz tarihinde üretilir. Aynı ürün ve analiz tarihi her çalıştırmada aynı sonucu verir; sayfa yenilendiğinde rastgele değişmez.
- Hareket evrenindeki ürünlerle yalnız stok kataloğunda bulunan ürünlerin birleşimi korunur. Böylece bütün ürünlere bir demo stok adedi atanır.

### 28.2 Hibrit model

- Bütün ürünler `Demo stok` olarak işaretlenir; arayüz hiçbir miktarı gerçek fiziksel sayım gibi sunmaz.
- Satış ve iadeler önce `Miktar × İçerik` ile temel birime çevrilir. Böylece `ST`, `PK`, `KL`, `KG/G` gibi farklı hareket birimleri doğrudan toplanmaz.
- Koli içeriğinde ilk tercih stok tablosundaki ürün eşleşmesidir. Eşleşme yoksa hareketlerdeki baskın `PK` içeriği, o da yoksa baskın hareket içeriği kullanılır. Hiçbiri yoksa tekil birim kabul edilir; kaynak her ürün sonucunda belirtilir.
- Günlük koli tüketimi, son 90 günlük net temel birim tüketiminin önce 90'a, sonra koli içeriğine bölünmesiyle bulunur. Son 90 gün boşsa önceki 90 gün yedek hızdır.
- Ürün kodu ve analiz tarihinden deterministik bir demo hedef kapsama üretilir: `A = 10–42 gün`, `B = 20–60 gün`, `C = 30–90 gün`.
- Demo stok formülü: `tavan(günlük koli tüketimi × hedef kapsama günü)`. Sonuç en az bir ve daima tam koli olur.
- Satış geçmişi olmayan ürünlere ürün kodundan deterministik biçimde 1–12 tam koli atanır ve durum `Hareketsiz` olur.
- Stok değeri ile yerine koyma değeri kaynak stok toplamlarından alınmaz. Son 90 günlük hareket maliyetleri temel birim maliyetine çevrilir ve modellenen temel birim stokla çarpılır.

### 28.3 İşlenme hızı ve stok durumu

- Günlük işlenme hızı hem `koli/gün` hem `temel birim/gün`; 30 günlük tüketim ise koli cinsinden gösterilir.
- Kapsama günü `demo tam koli stoku / günlük koli tüketimi` olarak hesaplanır.
- Durum eşikleri: `<15 gün Kritik`, `15–<30 gün Düşük`, `30–60 gün Dengeli`, `>60 gün Fazla stok`.
- Hesaplanabilir satış hızı olmayan ürün `Hareketsiz` olarak işaretlenir. Bu, seçili 180 günlük hız evreninde kullanılabilir satış geçmişi bulunmadığını ifade eder.

### 28.4 Uygulanan Stok sayfası

- KPI alanı modellenen stok değeri, demo stoklu ürün, koli içeriği stok kaynağından eşleşen ürün, kritik kapsama ve hareketsiz ürün sayılarını gösterir.
- Yöntem notu birim normalizasyonunu, tam koli yuvarlamasını ve ABC hedef gün aralıklarını açıklar.
- Ürün tablosunda tam koli stoku, temel birim karşılığı, koli içeriği, koli ve temel birim tüketim hızları, kapsama, modellenen değer ve durum birlikte gösterilir.
- Stok durumu seçimi, ürün araması ve malzeme grubu çekmece filtresi korunur. Gerçek/tahmini ayrımı kaldırılmıştır çünkü bütün stok adetleri aynı demo modelindedir.
- Ürün detayında hedef ve gerçekleşen kapsama, içerik kaynağı, stok değeri, yerine koyma değeri ve aralarındaki fark açıklanır.
- Eski gerçek/tahmini hibrit hesaplama stok kararında artık kullanılmaz; ileride ayrı bir veri karşılaştırma veya senaryo kalibrasyonu çalışmasında yeniden değerlendirilebilir.

### 28.5 Sonraki stok turu

1. Ambar dağılımı ve ambarlar arası dengesizlik görünümü
2. Kritik ve fazla stokların Euro etkisine göre önceliklendirilmesi
3. Kullanıcı kabulünden sonra tahmin referans günlerinin kategori bazında gözden geçirilmesi
4. Satın Alma ve Stok Dengesi modülüne aktarılacak sipariş/eritme adaylarının hazırlanması

## 29. Uygulama gerçekleşme kaydı — 22 Eylül 2026

Bu bölüm, yukarıdaki bağlayıcı kararların demoda hangi teslimlere dönüştüğünü kaydeder. Ayrıntılı kontrol listesi ve kabul kapıları `UYGULAMA_PROGRAMI.md`, ürün ilkeleri `PRODUCT.md`, görsel sistem `DESIGN.md`, rol bazlı son kontrol adımları `TESLIMAT_KONTROL_LISTESI.md` içindedir.

- Ortak karar motoru; metrik ve fatura semantiği, kararlı sinyal kimliği, etiket → sinyal → uyarı → aksiyon izi ve gerçek kaynak satırı kanıt sözleşmesiyle tamamlandı.
- Müşteri 360; RFM, sipariş ritmi, büyüme/küçülme, gecikme/kayıp riski, ürün ilişkisi ve müşteri ayrıntısıyla tamamlandı.
- Fiyat ve Maliyet ile Satıcı Performansı; birim kayıtlı/yerine koyma ekonomisi, fiyat koridoru, fiyat açığı, müşteri sapması ve koçluk sinyalleriyle tamamlandı.
- Coğrafya, Satın Alma ve Stok Dengesi, Sepet ve Çapraz Satış ile İade Analizi uzman ekranları gerçek veri kapsamına bağlandı.
- Birleşik Uyarılar ve Anomaliler akışı 1.219 gerçek olay üzerinde inceleme, yanlış pozitif, tekrar ve yaşam döngüsü desteğiyle tamamlandı.
- Aksiyon Merkezi; sahiplik, termin, durum, kapanış sonucu, gerçekleşen etki, dönüşüm ve kapanış süresi ölçümüyle tamamlandı.
- Satış ve Kârlılık; uzlaşan fiyat şelalesi, 90 gün eşiğine göre günlük/aylık trend, dört kırılım ve kayıtlı/yerine koyma ekonomi karşılaştırmasıyla tamamlandı.
- Yönetim Kokpiti; ortak filtreler, karar özeti, risk/fırsat/aksiyon bağlantıları ve açıklanabilir fiyat şelalesiyle tamamlandı.
- Öngörüler; ürün/kategori dört haftalık talep, rolling backtest, tahmin aralığı, WAPE/MAE/bias, model yayınlama koruması ve müşteri beklenen sipariş tarihiyle tamamlandı.
- Tema lacivert/mavi sisteme taşındı; sabit masaüstü menüsü, mobil yatay navigasyon, klavye etkileşimi ve modal odak yönetimi kabul katmanına alındı.
- Doğrulama: 19.335 hareket satırı mutabakatı, 55 Python testi, TypeScript kontrolü, Next.js üretim derlemesi ve canlı tarayıcı senaryoları geçti.

Bu tarihten sonra yeni kapsam eklenirken mevcut hesaplama ve terim sözleşmeleri değiştirilmez; değişiklik gerekiyorsa önce karar kaydı açılır ve etkilenen testler güncellenir.
