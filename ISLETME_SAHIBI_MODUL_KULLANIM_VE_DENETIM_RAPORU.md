# Ticari Öngörü Platformu — İşletme Sahibi Denetim ve Kullanım Raporu

**Rapor tarihi:** 23 Eylül 2026  
**Varsayılan demo analiz tarihi:** 30 Aralık 2024  
**Para birimi:** Euro (€)  
**Kapsam:** Yönetim, satış, satın alma, fiyatlandırma, müşteri, ürün, stok, iade, fırsat, öngörü, aksiyon ve veri kalitesi modülleri

---

## Güncel kullanım: karar dosyaları

Ana menü artık yedi merkezdir: Karar Özeti, Sinyaller ve İçgörüler, Onay Kuyruğu, Aksiyonlar, Sonuçlar ve Geri Bildirim, Ticari İnceleme, Veri ve Etiketler. Aşağıdaki uzman modül açıklamalarına **Ticari İnceleme** alt gruplarından ulaşılır. Önceki aksiyon kayıtları yeni sistemde salt okunur geçmiş olarak korunur.

Sunum sırası: Karar Özeti'nde dokuz örneği hazırla → Onay Kuyruğu'ndan karar dosyasını aç → veri/etiket/sinyal/içgörü kanıtını incele → öneriyi onayla → aksiyonu başlat ve uygulamayı kaydet → Sonuçlar ve Geri Bildirim'deki hazır örnekle karşılaştırmayı göster. Yeni uygulanan görev için bekleme atlanmaz. Veri yoksa **Ölçülemedi** kullanılır.

Güncel adımlar ve API/test notları için [README](README.md) esas alınmalıdır. Demo örnekleri gerçek sonuç değildir; sıfırlama yalnız bu örnekleri etkiler.

## 1. Yönetici özeti

Platform; işletme sahibinin “Ne oldu?”, “Neden oldu?”, “Nerede risk var?”, “Kimin ilgilenmesi gerekiyor?” ve “Sonuç alındı mı?” sorularını tek bir karar zincirinde cevaplamak üzere tasarlanmıştır. Sistem yalnızca rapor göstermez: ticari bulguyu kaynak kanıtıyla açıklar, kullanıcı tarafından doğrulanmasını sağlar, aksiyona dönüştürür ve kapanış etkisini kaydeder.

Denetim sonunda 15 modülün tamamı canlı arayüzde açılmış, yüklenme/hata durumları kontrol edilmiş, 55 otomatik iş kuralı testi çalıştırılmış, TypeScript tip kontrolü ve üretim derlemesi tamamlanmıştır. Uyarı ekranındaki ham teknik etiket kodları kaldırılmış; geliştirici dili işletme diline çevrilmiş; sol menüdeki faz, harf ve görev aralığı rozetleri kaldırılmış; yoğun uyarı listesi 50 kayıtlık sayfalara bölünmüştür. Bir bulgu üzerinden aksiyon oluşturulmuş ve kaydın Aksiyon Merkezi’nde açık görev olarak göründüğü canlı olarak doğrulanmıştır.

### Platformun doğru kullanım sırası

1. Üst alandaki **Analiz tarihi** kontrol edilir. Demo başlangıcı 30.12.2024’tür; kullanıcı farklı bir tarih seçebilir.
2. **Yönetim Kokpiti** ile genel ticari durum okunur.
3. **Uyarılar ve Fırsatlar** ekranında öncelikli bulgular kanıtlarıyla incelenir.
4. İlgili uzman sayfada ürün, müşteri, satıcı, fiyat, iade veya stok detayı doğrulanır.
5. Karar gerektiren bulgu **Aksiyon Merkezi**’ne gönderilir.
6. Sorumlu, durum, sonuç ve gerçekleşen etki kaydedilir.
7. Veri şüphesi varsa **Veri Merkezi** üzerinden kaynak ve kalite durumu incelenir.

---

## 2. Ortak veri ve hesaplama kuralları

### 2.1 Tarih yaklaşımı

- Bütün sayfalarda ortak analiz tarihi kullanılır.
- Varsayılan tarih **30.12.2024** olup demo verisinin dönemine uygun karar üretir.
- Tarih değiştirildiğinde gecikme, son 90 gün, önceki 90 gün, müşteri ritmi, sinyal ve öngörü hesapları yeni tarihe göre yeniden değerlendirilir.
- Ekranda görülen analiz tarihi ticari değerlendirme tarihidir. Sistemin bir bulguyu ne zaman hesapladığı ise ayrı denetim zamanıdır.

### 2.2 Satış ve iade kapsamı

- Satış cirosuna yalnızca satış faturaları alınır.
- Satın alma ve satın alma iadesi, satış cirosu/kârlılık hesaplarına karıştırılmaz.
- Satış iadesi net satıştan düşülür; kullanıcı uygun ekranlarda brüt ve net bakışı karşılaştırabilir.
- İade tutarı tek başına değil; kaybedilen ciro, kâr etkisi, müşteri ve ürün yoğunluğu ile birlikte yorumlanır.

### 2.3 Maliyet yaklaşımı

- Kayıtlı maliyet ve yerine koyma maliyeti farklı ekonomik bakışlardır.
- Yerine koyma maliyeti kaynak satırda toplam değer olarak bulunuyorsa miktara bölünerek birim seviyeye normalleştirilir.
- Yerine koyma kârı = net birim satış fiyatı − birim yerine koyma maliyeti.
- Yerine koyma marjı = yerine koyma kârı / net satış.
- Sıfır maliyetli kayıtlar kârlılığı bozmaması için karantinada tutulur ve risk panelinden denetlenebilir.

### 2.4 Demo stok yaklaşımı

- Kaynak stok tablosu güvenilir güncel stok miktarı yerine koli/paket içeriğinin referansı olarak kullanılır.
- Bütün ürünler için stok miktarı satış hızına göre modellenmiş tam koli sayısıdır; kesirli koli gösterilmez.
- Günlük tüketim, gerçek satış hareketlerinden normalize edilir.
- Kapsama günü = modellenen stok / günlük tüketim.
- Bu nedenle Stok sayfası gerçek depo sayımı değil, karar senaryosudur; ekran bunu açık biçimde belirtir.

### 2.5 Etiket, bulgu ve aksiyon ayrımı

- **Etiket:** Ürün veya müşterinin hesaplanan ticari niteliğidir; örneğin “Satışı hızlanan”, “Yüksek iade oranı”.
- **Bulgu:** Belirli analiz tarihinde dikkate alınması gereken, puanlanmış ve kanıtlanabilir durumdur.
- **Aksiyon:** Bir bulgunun sorumlusu, durumu, termini ve sonucu izlenen iş kaydıdır.
- Aynı kavram bütün sayfalarda aynı adla kullanılır; kullanıcıya ham sistem kodu gösterilmez.

---

## 3. Rol bazlı kullanım

### İşletme sahibi / genel müdür

Her gün Kokpit → Uyarılar → Aksiyon Merkezi sırasını izlemelidir. Ciro büyürken marjın gerileyip gerilemediğini, iadelerin etkisini, kritik müşteri/ürün yoğunlaşmalarını ve açık aksiyonların kapanış hızını takip eder.

### Satış yöneticisi

Müşteri 360, Satıcı Performansı, Coğrafi Analiz, Sepet ve Çapraz Satış ile müşteri kaybı, ürün eksilmesi, satıcı portföyü ve büyüme fırsatlarını inceler. Müşteri görüşmelerini aksiyona dönüştürür.

### Satın almacı

Stok, Fiyat ve Maliyet, Satın Alma ve Stok Dengesi ve Öngörüler sayfalarını birlikte kullanır. Amaç yalnız stok bulundurmak değil; doğru miktarı, doğru maliyetle ve doğru zamanda yerine koymaktır.

### Fiyatlandırma sorumlusu

Kayıtlı maliyet, yerine koyma maliyeti, fiyat koridoru, müşteri fiyat sapması ve marj erozyonunu inceler. Zararına satış veya hedef marj altı bulgularını fiyat aksiyonuna dönüştürür.

### Veri sorumlusu

Veri Merkezi’nde yükleme, alan eşleme, kalite kontrolü, karantina ve hata raporlarını yönetir. Ticari kullanıcıların gördüğü sonuçların kaynak satırlarına kadar izlenebilir olmasını sağlar.

---

## 4. Sayfa bazında ayrıntılı kullanım kılavuzu

## 4.1 Yönetim Kokpiti

**Cevapladığı soru:** İşletmenin genel ticari sağlığı nasıl; büyüme kârlı mı ve en acil riskler neler?

**Ekranda görülenler:** Net/brüt satış, brüt kâr, marj, fatura, müşteri ve sepet KPI’ları; zaman trendi; fiyat şelalesi; kategori/müşteri/satıcı/ambar katkı tablosu; risk paneli; sıfır maliyet karantinası.

**Kullanım:**

1. Tarih kapsamını kontrol edin. Tüm dönem görünümü uzun vadeli resmi verir.
2. Üst KPI’larda ciro ile kârın aynı yönde ilerleyip ilerlemediğine bakın.
3. Zaman grafiğinde 90 günden kısa kapsam seçilirse günlük, daha uzun kapsamda aylık kırılım kullanılır.
4. Grafikte bir döneme tıklayarak çapraz filtre uygulayın.
5. Fiyat şelalesini soldan sağa okuyun: brüt satış → indirim → iade → net satış → maliyet → brüt kâr.
6. Katkı tablosunda kategori, müşteri, satıcı ve ambar sekmelerini karşılaştırın.
7. Risk panelindeki sıfır maliyet kaydını açarak kaynak satırı ve açıklamayı kontrol edin; gerekirse CSV indirin.

**Yönetim yorumu:** Ciro artışı tek başına başarı değildir. Net satış büyürken yerine koyma marjı düşüyorsa gelecekteki kârlılık baskı altındadır. Fiyat şelalesi, kârın indirim mi, iade mi, maliyet mi nedeniyle eridiğini ayırır.

**Denetim sonucu:** Açılış, KPI, grafik, kırılım ve karantina yapısı çalışır durumda. Para birimi Euro’dur; satın almalar satış toplamına karışmaz.

## 4.2 Uyarılar ve Fırsatlar

**Cevapladığı soru:** Bugün hangi ticari durumlar yönetici incelemesi gerektiriyor?

**Ekranda görülenler:** Aktif, inceleme bekleyen, doğrulanan ve gerekçeyle kapatılan bulgu sayıları; arama; modül/önem/inceleme filtreleri; öncelik puanı; ticari etki; güven; tekrarlanma; inceleme durumu.

**Kullanım:**

1. Önce “Kritik” ve “Yüksek” önem seviyelerini süzün.
2. Ürün, müşteri, fiyat veya satıcı modülünü seçerek sorumlu ekibin iş listesini daraltın.
3. İlk 50 kaydı inceleyin; Sonraki/Önceki kontrolleriyle sayfalar arasında ilerleyin.
4. Satıra tıklayın. Sağ panelde gözlenen değer, eşik/referans, tahmini etki, veri güveni ve kaynak faturalar görünür.
5. Bulgu doğruysa “Doğrula”; geçersizse gerekçe girerek “Geçersiz olarak kapat” seçin.
6. İş gerektiriyorsa “Aksiyon oluştur” ile Aksiyon Merkezi’ne gönderin.

**Profesyonellik kuralı:** Kullanıcıya `PRODUCT_...` gibi ham kodlar gösterilmez. Kaynak satırları yalnız kanıt amacıyla, fatura/tarih/tutar bağlamında sunulur.

**Denetim sonucu:** 1.219 aktif bulgu 50 kayıtlık sayfalara ayrıldı. Ham etiket kodları kaldırıldı. Canlı testte ilk ürün bulgusu açıldı, 81 kaynak satırı görüntülendi ve aksiyon başarıyla oluşturuldu.

## 4.3 Satış ve Kârlılık

**Cevapladığı soru:** Satış hacmi gerçek ve geleceğe taşınabilir kâra dönüşüyor mu?

**Ekranda görülenler:** Net satış, kayıtlı kâr/marj, yerine koyma kârı/marjı, ekonomi farkı, iade, fatura ve ürün sayısı; kategori, müşteri, satıcı ve ambar kırılımları.

**Kullanım:** Kayıtlı marj ile yerine koyma marjını birlikte okuyun. Fark büyüdükçe geçmiş maliyet kârlılığı olduğundan iyi gösteriyor olabilir. Müşteri veya satıcı satırına tıklayarak ilgili uzman sayfaya geçin. Arama ile belirli bir varlığı bulun.

**Karar örnekleri:** Yerine koyma marjı düşükse fiyat gözden geçirilir; yüksek ciro/düşük kâr varsa indirim ve ürün karması incelenir; iadeli müşteri için İade Analizi’ne geçilir.

**Denetim sonucu:** Satış iadeleri netleştirilir, satın alma faturaları hariç tutulur, bütün kırılımlar aynı ekonomik toplamla uzlaşır.

## 4.4 İade Analizi

**Cevapladığı soru:** İadeler nerede yoğunlaşıyor ve devam ederse ne kadar ticari kayıp yaratır?

**Ekranda görülenler:** İade tutarı/oranı, kaybedilen ciro ve kâr etkisi; en çok iade edilen ürünler; en çok iade yapan müşteriler; dönemsel trend ve devam senaryosu.

**Kullanım:** Önce parasal etkiye, sonra orana bakın. Küçük hacimli üründe yüksek oran ile büyük hacimli üründe orta oran farklı önceliktedir. Ürün ve müşteri liderlerini birlikte inceleyerek kalite, yanlış fiyat, yanlış ürün seçimi veya operasyon kaynaklı nedeni ayırın.

**Karar örnekleri:** Kalite kontrolü, müşteri görüşmesi, ürün paketleme değişikliği, satıcı eğitimi, fiyat/iade koşulu düzenlemesi.

**Denetim sonucu:** İade satıştan düşülür; ürün/müşteri liderleri ve kayıp senaryosu aynı satış kapsamına bağlıdır.

## 4.5 Ürün ve Kategori

**Cevapladığı soru:** Hangi ürünler ciro, kâr, müşteri erişimi ve satış hızı bakımından önceliklidir?

**Ekranda görülenler:** Türkçe karakter ve büyük/küçük harfe duyarsız ürün araması; en çok satan, ciro getiren, kâr ettiren ve ciro-kâr farkı yüksek ürün listeleri; müşteri sayısı; hız etiketleri; ABC portföyü; ürün ayrıntı paneli.

**Kullanım:**

1. Ürün adı veya koduyla arayın ya da lider listelerden seçim yapın.
2. Ciro ve kâr listelerinin aynı olup olmadığını kontrol edin; fark sekmesi yüksek ciroya rağmen zayıf kâr üreten ürünleri ortaya çıkarır.
3. Hızlanan, yavaşlayan, duran ve yeni hareket filtrelerini kullanın.
4. ABC sınıfına tıklayarak A/B/C ürün listesini ve ürün bilgilerini modalda açın.
5. Ürüne tıklayın; fiyat, maliyet, marj, yerine koyma ekonomisi, satış hızı, müşteri erişimi ve iade etkisini okuyun.
6. Müşteri sekmesinde ürünü alan müşteri ve gerçekleşen fiyatı inceleyin.

**ABC yorumu:** A sınıfı ilk %80 ciroyu, B sonraki %15’i, C kalan %5’i oluşturur. A “iyi”, C “kötü” değildir; tedarik ve yönetim önceliğini gösterir.

**Satış hızı:** Son 90 gündeki ürün ciro payı, önceki 90 günün payıyla karşılaştırılır. Yeterli geçmiş yoksa “Yetersiz geçmiş” gösterilir.

**Denetim sonucu:** Birim satış, kayıtlı birim maliyet ve birim yerine koyma maliyeti ayrıdır; ürün detayına geçişler ve ABC modalları çalışır durumdadır.

## 4.6 Müşteri 360

**Cevapladığı soru:** Müşterinin değeri, alışveriş ritmi, ürün ilişkisi ve kayıp riski nedir?

**Ekranda görülenler:** Arama; müşteri değeri; son sipariş; sipariş sıklığı; RFM/lifecycle etiketleri; ürün yoğunlaşması; iade; satıcı; zaman çizelgesi; ürün ve fatura ayrıntıları.

**Kullanım:** Müşteriyi ad, kod, şehir veya satıcıyla bulun. Son 90 gün ile önceki 90 gün değişimini kontrol edin. Gecikme etiketini müşterinin kendi medyan sipariş ritmiyle birlikte okuyun. Ürün kaybı veya tek ürüne bağımlılık varsa sepet geliştirme önerisi hazırlayın. Fatura zaman çizelgesiyle satışın gerçekten durup durmadığını doğrulayın.

**Karar örnekleri:** Geri kazanım görüşmesi, yeni ürün önerisi, fiyat tutarlılığı kontrolü, satıcı ziyareti, iade kök neden görüşmesi.

**Denetim sonucu:** Satın alma hareketleri müşteri satış değerine katılmaz; 90 günlük karşılaştırmalar ve müşteri detay kanıtları testlidir.

## 4.7 Satıcı Performansı

**Cevapladığı soru:** Hangi satıcı sürdürülebilir ciro ve kâr üretiyor; hangi portföy koçluk gerektiriyor?

**Ekranda görülenler:** Ciro/pay, kâr/marj, yerine koyma marjı, sepet, müşteri/ürün sayısı, iade, prim kapsamı ve portföy kalitesi.

**Kullanım:** Ciro, kâr, yerine koyma marjı, müşteri sayısı veya iade oranına göre sıralayın. Satıcı satırını açarak müşteri ve ürün portföyünü inceleyin. Atanmamış satıcıyı otomatik olarak hata kabul etmeyin; satın alma belgelerinde satıcı bulunmaması normaldir ve “Bilinmiyor/Atanmamış” olarak korunur.

**Karar örnekleri:** Marj koçluğu, çapraz satış hedefi, müşteri geri kazanım listesi, yüksek iade neden analizi, prim kapsamının yeniden değerlendirilmesi.

**Denetim sonucu:** Satıcı ekonomisi satış kapsamına bağlıdır; atanamayan kayıtlar yanlış kişiye yazılmaz.

## 4.8 Coğrafi Analiz

**Cevapladığı soru:** Ciro, kâr, müşteri ve iade hangi şehir/ülke bölgelerinde yoğunlaşıyor?

**Ekranda görülenler:** Net satış, şehir/ülke sayısı, eksik konum satırı, şehir-ülke-posta alanı, ciro payı, kâr/marj, müşteri ve iade.

**Kullanım:** Bölgeyi ciro payına göre sıralı okuyun; marj ve iade ile dengeleyin. Aynı şehrin farklı yazımları veri kalitesi konusu olabilir. Sistem boşlukları temizler fakat bilinmeyen konumu tahmin etmez.

**Karar örnekleri:** Bölgesel satış planı, rota/ziyaret yoğunluğu, dağıtım odağı, yüksek iadeli bölge incelemesi.

**Denetim sonucu:** Satın almalar hariç, iadeler düşülmüş net coğrafi satış görünümü kullanılır; eksik konum açıkça sayılır.

## 4.9 Stok

**Cevapladığı soru:** Demo senaryosunda hangi ürünün tahmini stoğu kritik, dengeli veya fazladır?

**Ekranda görülenler:** Tam koli stok, temel birim karşılığı, koli içeriği, günlük koli/birim tüketimi, kapsama günü, stok değeri ve durum.

**Kullanım:** Durum filtresinden Kritik/Düşük/Dengeli/Fazla stok/Hareketsiz/Yetersiz geçmiş seçin. Ürünü açarak satış hızı ve stok varsayımını inceleyin. Kapsama gününü öngörü ve satın alma sayfasıyla birlikte yorumlayın.

**Önemli sınır:** Buradaki stok gerçek depo sayımı değildir. Kaynak tablo paket/koli içeriğini sağlar; miktarlar gerçek satış hızına göre modellenir. Operasyonel siparişten önce fiziksel/ERP stoğu doğrulanmalıdır.

**Denetim sonucu:** Bütün ürünlerde tam koli üretilir; kesirli koli ve stok değeri=yerine koyma değeri türü önceki anlam sorunları giderilmiştir.

## 4.10 Fiyat ve Maliyet

**Cevapladığı soru:** Güncel fiyatlar maliyet ve hedef marjı koruyor mu; hangi müşteri fiyatı portföyden sapıyor?

**Ekranda görülenler:** Ürün fiyatları, kayıtlı ve yerine koyma maliyeti, hedef fiyat koridoru, marj, müşteri sapmaları ve fiyat bulguları.

**Kullanım:** Önce “Yalnız riskliler” ile zararına/hedef altı ürünleri bulun. Fiyat koridorunu gerçekleşen müşteri fiyatlarıyla karşılaştırın. Tek bir ucuz faturayı genellemeden önce adet, müşteri anlaşması ve tarihsel dağılımı kontrol edin.

**Karar örnekleri:** Liste fiyat güncellemesi, minimum satış fiyatı, müşteri özel fiyat gözden geçirme, maliyet doğrulama, satıcı uyarısı.

**Denetim sonucu:** Birim maliyet ve yerine koyma maliyeti ayrıştırılmış; satın alma satırları satış cirosuna eklenmeden maliyet referansı olarak kullanılmıştır.

## 4.11 Satın Alma ve Stok Dengesi

**Cevapladığı soru:** Hangi ürün ne zaman ve hangi maliyet baskısıyla yerine konmalıdır?

**Ekranda görülenler:** Alış fiyatı değişimi, son/önceki dönem maliyet karşılaştırması, tüketim ve kapsama, sipariş önceliği ve önerilen yaklaşım.

**Kullanım:** Kritik kapsama ile yükselen alış maliyetini birlikte değerlendirin. Sadece ucuz diye fazla stok üretmeyin; sadece kritik stok diye marjı yok eden alım yapmayın. Ürün detayına geçerek satış hızı ve fiyat kapasitesini doğrulayın.

**Karar örnekleri:** Sipariş zamanı/miktarı, tedarikçi görüşmesi, alternatif ürün, fiyat güncellemesi, fazla stok eritme.

**Denetim sonucu:** Alış fiyat pencereleri ve demo stok önerileri otomatik testlerle doğrulanmıştır.

## 4.12 Sepet ve Çapraz Satış

**Cevapladığı soru:** Hangi ürünler birlikte satılıyor ve hangi müşteriye hangi ek ürün önerilebilir?

**Ekranda görülenler:** Birlikte alınan ürün çiftleri, destek/güven benzeri yön göstergeleri, müşteri veya ürün fırsatları ve örneklem yeterliliği.

**Kullanım:** Yalnız yüksek adetli birlikteliğe değil, örneklem büyüklüğüne ve yönüne bakın. Ürün A’yı alanların B’yi alma eğilimi, ters yönde aynı olmayabilir. Fırsatı müşteri 360’ta müşterinin mevcut sepetiyle doğrulayın.

**Karar örnekleri:** Satıcı öneri listesi, paket teklif, raf/ürün eşlemesi, kampanya.

**Denetim sonucu:** Örneklem güvenlik sınırları ve yön hesabı testlidir; satın almalar sepet satış analizine katılmaz.

## 4.13 Öngörüler

**Cevapladığı soru:** Önümüzdeki dört haftada ürün/kategori talebi ne olabilir; hangi müşterinin siparişi gecikmiş olabilir?

**Ekranda görülenler:** Ürün, kategori ve müşteri sekmeleri; dört haftalık öngörü; olası aralık; hata ölçüsü; seçilen yöntem; veri kapsamı; müşteri beklenen sipariş tarihi ve güven seviyesi.

**Kullanım:** Ürün/kategori öngörüsünde nokta tahminini tek kesin sayı kabul etmeyin; alt-üst aralıkla okuyun. Düşük hata daha iyi tarihsel performansı gösterir. Müşteri sekmesinde beklenen tarih, son siparişe müşterinin medyan ritmi eklenerek hesaplanır. Yetersiz geçmiş olan kayıt için sistem zorla tahmin üretmez.

**Karar örnekleri:** Satın alma hazırlığı, satış hedefi, müşteri arama listesi, kampanya kapasitesi.

**Denetim sonucu:** Ürün/kategori/müşteri geçişindeki eski veri yarışı hatası giderilmiştir. Yöntemler gelecek verisini geçmiş teste sızdırmadan karşılaştırılır; 30.12.2024 tarihinde gecikmeli müşteri görünümü canlı doğrulanmıştır.

## 4.14 Aksiyon Merkezi

**Cevapladığı soru:** Hangi bulgu kimin sorumluluğunda, gecikti mi, nasıl sonuçlandı ve ne kadar etki yarattı?

**Ekranda görülenler:** Açık/devam, geciken, dönüşüm, gerçekleşen etki, ortalama kapanış; Aksiyonlar ve Aksiyona dönüştürülmemiş sekmeleri; durum filtreleri; sorumlu, termin, olay geçmişi ve kapanış alanları.

**Kullanım:**

1. “Aksiyona dönüştürülmemiş” sekmesinden yüksek etkili bulguyu seçin veya Uyarılar ekranından doğrudan oluşturun.
2. Açık aksiyonu “Devam ediyor” durumuna alın.
3. Kapanıştan önce sonuç türünü seçin.
4. Ölçülebilir kapanışta gerçekleşen Euro etkisini girin; açıklayıcı kapanış notu ekleyin.
5. Tamamlandı veya Reddedildi durumuna geçirin.
6. Geciken ve kapanan aksiyonları filtrelerle denetleyin.

**Kontroller:** Sonuç seçilmeden kapanışa izin verilmez. Ölçülebilir sonuçta gerçekleşen etki zorunludur. Durum değişiklikleri ve olay geçmişi kaydedilir.

**Denetim sonucu:** Canlı testte “Zararına satılan” ürün bulgusundan kritik öncelikli açık aksiyon oluşturuldu; Aksiyon Merkezi’nde 1 açık kayıt, sorumlu ve durum kontrolüyle görüntülendi.

## 4.15 Veri Merkezi

**Cevapladığı soru:** Analizlerin beslendiği veri yeterli, temiz, izlenebilir ve kullanıma hazır mı?

**Ekranda görülenler:** CSV ekleme, kaynak türü seçimi, şablon indirme, ön kontrol, alan/hata grupları, kaynak satırı inceleme, kalite raporu ve veri kapsamı.

**Kullanım:** Önce uygun şablonu indirin. Hareket veya ürün/stok kaynağını doğru türle yükleyin. Ön kontrol tamamlanmadan resmi içe aktarma yapılmaz. Hata gruplarını alan ve kaynak satırıyla inceleyin. Sıfır maliyet gibi ticari hesaplamayı bozan kayıtları karantinada tutun. Raporu CSV olarak indirin.

**Kalite ilkesi:** Boş değer sıfır kabul edilmez; bozuk tarih/sayı analize zorla sokulmaz; tekrar eden kayıt otomatik silinmez, aday olarak işaretlenir; satış/satın alma belge semantiği korunur.

**Denetim sonucu:** Yükleme, şema, karantina, tekrar ve güvenli hata sözleşmeleri otomatik testlerle doğrulanmıştır. Son kullanıcıya teknik altyapı adı yerine veri güvenliği ve kalite dili gösterilir.

---

## 5. Uçtan uca örnek iş akışları

### 5.1 Patronun sabah kontrolü

1. Kokpitte net satış, kâr ve yerine koyma marjını karşılaştırır.
2. İade veya fiyat şelalesindeki olağandışı erozyonu görür.
3. Uyarılar sayfasında yüksek önem filtresi uygular.
4. Kaynak faturaları açarak bulguyu doğrular.
5. Aksiyon oluşturur.
6. Gün sonunda Aksiyon Merkezi’nde sorumlu/durum; hafta sonunda gerçekleşen etkiyi kontrol eder.

### 5.2 Satış yöneticisinin müşteri geri kazanımı

1. Öngörüler > Müşteri sekmesinde geciken müşterileri inceler.
2. Müşteri 360’ta sipariş ritmi, son ürünler ve ciro değişimini doğrular.
3. Satıcı Performansı’nda sorumlu portföyü açar.
4. Geri kazanım görüşmesini aksiyon olarak atar.
5. Sonucu “Siparişe dönüştü” veya uygun kapanış türüyle kaydeder.

### 5.3 Satın almacının kritik ürün kararı

1. Stok sayfasında kritik/düşük kapsama filtresini seçer.
2. Öngörülerde dört haftalık talep ve aralığı inceler.
3. Satın Alma ve Stok Dengesi’nde alış maliyeti değişimini kontrol eder.
4. Fiyat ve Maliyet’te yeni maliyetin hedef marja etkisini görür.
5. Sipariş ve/veya fiyat aksiyonu oluşturur.

### 5.4 İade kök neden çalışması

1. İade Analizi’nde en yüksek parasal etkili ürünü seçer.
2. Ürün detayında iadeyi yapan müşterileri ve satış fiyatlarını inceler.
3. Müşteri 360 ve satıcı sayfasından yoğunlaşmayı kontrol eder.
4. Kalite, fiyat, satış veya operasyon nedenini kanıtlar.
5. Düzeltici aksiyonu atar ve sonraki dönemde iade etkisini ölçer.

---

## 6. Denetim ve test sonuçları

| Denetim alanı | Sonuç | Kanıt |
|---|---:|---|
| İş kuralı testleri | Başarılı | 55/55 test geçti |
| TypeScript tip kontrolü | Başarılı | Hatasız tamamlandı |
| Üretim derlemesi | Başarılı | Next.js üretim derlemesi tamamlandı |
| 15 modül açılışı | Başarılı | Her modül canlı tarayıcıda tek tek açıldı |
| Sol menü profesyonellik | Başarılı | Faz/harf/sayı/görev rozetleri kaldırıldı |
| Uyarı dili | Başarılı | Ham etiket kodları kaldırıldı; işletme dili kullanıldı |
| Uyarı liste performansı | Başarılı | 50 kayıtlık sayfalama eklendi |
| Bulgu kanıt paneli | Başarılı | Fatura, tarih, tutar ve kaynak satırı görüntülendi |
| Bulgu → aksiyon | Başarılı | Başarı mesajı alındı ve açık aksiyon görüldü |
| Analiz tarihi | Başarılı | 30.12.2024 varsayılan ve seçilebilir |
| Öngörü sekme geçişi | Başarılı | Eski veri yarışı engellendi |
| Stok tam koli modeli | Başarılı | Kesirli stok üretilmiyor |

### Canlı modül dolaşım sonucu

Yönetim Kokpiti, Uyarılar ve Fırsatlar, Satış ve Kârlılık, İade Analizi, Ürün ve Kategori, Müşteri 360, Satıcı Performansı, Coğrafi Analiz, Stok, Fiyat ve Maliyet, Satın Alma ve Stok Dengesi, Sepet ve Çapraz Satış, Öngörüler, Aksiyon Merkezi ve Veri Merkezi sayfalarının tamamı hata ekranı oluşturmadan yüklendi.

---

## 7. Bilinmesi gereken sınırlar

1. **Stok senaryodur.** Gerçek sipariş öncesinde fiziksel/ERP stok doğrulanmalıdır.
2. **Öngörü karar desteğidir.** Kesin gelecek taahhüdü değildir; hata aralığı ve veri kapsamıyla okunmalıdır.
3. **Sinyal hacmi karar değildir.** 1.219 bulgunun tamamına aynı öncelik verilmez; önem, etki ve güven filtreleri kullanılmalıdır.
4. **Sıfır maliyet kârlılık dışıdır.** Kaynak düzeltilene kadar karantinadadır.
5. **Bilinmeyen değer tahmin edilmez.** Konum veya satıcı yoksa “Bilinmiyor/Atanmamış” korunur.
6. **Demo analiz tarihi ile sistem çalışma tarihi farklıdır.** 30.12.2024 ticari değerlendirme tarihidir; denetim zaman damgası sistemin bulguyu hesapladığı gerçek zamandır.

---

## 8. Teslim kabul ölçütü

Demo; yönetici sunumuna hazır kabul edilir çünkü bütün ana ticari modüller aynı veri ve terminoloji kurallarıyla çalışmakta, uzman sayfalara geçiş sağlanmakta, bulgular kaynak kanıtıyla açıklanmakta, kararlar aksiyona çevrilebilmekte ve aksiyon sonucu ölçülebilmektedir. Operasyonel üretim kullanımına geçmeden önce gerçek ERP stok bağlantısı, kullanıcı/rol yetkilendirmesi, kurumsal kimlik doğrulama, yedekleme ve üretim izleme katmanları ayrıca planlanmalıdır.

Bu belge, uygulamayı A’dan Z’ye kullanmak; yönetim toplantısı yürütmek; satış, satın alma ve fiyat ekiplerine görev vermek; veri sınırlarını doğru anlatmak ve demo kabul kontrolü yapmak için ana kılavuzdur.
