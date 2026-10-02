# Ticari Öngörü Merkezi tasarım sistemi

## Görsel yön

Arayüz, yoğun ticari veriyi sakin ve güven veren bir biçimde sunar. Sol gezinmede koyu lacivert, ana çalışma alanında açık nötr yüzeyler ve etkileşimlerde mavi tonları kullanılır. Eski yeşil vurgu ürün dilinden çıkarılmıştır; yeşil yalnızca olumlu durum anlamı taşıdığında semantik renk olarak kullanılabilir.

## Temel token yaklaşımı

- **Gezinme zemini:** çok koyu lacivert; sayfa kaydırmasından bağımsız ve tam ekran yüksekliğinde sabit kalır.
- **Aktif menü ve hover:** ana lacivertten ayrışan mavi tonları; yalnız renge güvenmeden belirgin işaret ve metin ağırlığı.
- **Birincil işlem:** erişilebilir kontrasta sahip koyu mavi dolgu.
- **Ana yüzey:** düşük kromalı açık gri-mavi arka plan; beyaz kartlar ve ince mavi-gri ayırıcılar.
- **Semantik durumlar:** olumlu yeşil, dikkat amber, kritik kırmızı, bilgi mavi; her zaman ikon veya metin etiketiyle birlikte.
- **Tipografi:** Manrope ve sistem sans yedeği; sayısal değerlerde hizalı, kolay taranan yapı.

Kesin renk değerlerinin tek kaynağı uygulamadaki CSS tokenlarıdır. Bileşenler doğrudan renk kodu kullanmak yerine bu tokenları tüketir.

## Karar deneyimi

- Karar Özeti iş gündemidir: bekleyen onaylar, zamanı gelen takipler, geciken görevler ve üç ticari hikâye. Analiz tabloları bu ekranda tekrar edilmez.
- Karar dosyası tam sayfadır. Yedi aşamalı erişilebilir gezinme, odaklanmış çalışma bölümü, karar özeti ve tarihli geçmiş birlikte görünür.
- Sinyaller kanıt tablosu, onaylar kapsam incelemesi, aksiyonlar sorumlu/termin tablosu, sonuçlar önce–sonra karşılaştırması kullanır.
- Demo ve yüklenmiş veri alanları daima görünür bir seçimle ayrılır. Kanıt tarihi, görev değerlendirme tarihi ve gerçek kayıt zamanı farklı anlamlarla sunulur.
- Mobilde yan menü üstte yatay kaydırılabilir gezinmeye dönüşür. Karar dosyası tek sütundur; yalnız aşama şeridi ve veri tabloları kendi içinde yatay kayar.
- Yeni görünüm stilleri `app/decision-hub.css` içinde kapsamlı `.case-*` sınıflarıyla mevcut lacivert/mavi kimliği sürdürür.

## Yerleşim ve navigasyon

- Sol menü masaüstünde sabittir; yalnız ana içerik kayar. Uzun sayfalarda menünün altında beyaz boşluk oluşmaz.
- Üst başlık ortak tarih, ambar ve satıcı filtrelerini; sıfırlama ve gelişmiş filtre erişimini taşır.
- Sağ çekmece sayfaya özgü filtreleri barındırır ve etkin filtreleri görünür biçimde özetler.
- KPI kartları özet verir; kart veya ilişkili aksiyon kullanıcıyı kanıta ve ayrıntıya götürür.
- Modaller yalnız ayrıntı ve odaklanmış karar akışları içindir; kapatma, geri dönüş, odak tuzağı ve Escape davranışları tutarlıdır.
- İlişkili varlıklar tıklanabilir olmalıdır: ürün, müşteri, satıcı ve sinyal bağlamı uygun ayrıntı görünümüne geçer.

## Veri görselleştirme

- Trend varsayılan olarak aylıktır; seçilen aralık 90 gün veya daha kısaysa günlük kırılıma döner.
- Grafiklerde tooltip, birim, dönem ve serinin anlamı açıkça görünür.
- Fiyat Şelalesi; Brüt Satış → İndirimler → İadeler → Net Satış → COGS → Brüt Kâr akışını kısa açıklama ve yardımcı bilgiyle anlatır.
- Renk tek başına veri taşımaz; etiket, desen, ikon veya değerle desteklenir.
- Büyük tablolar arama, sıralama, makul sayfalama ve boş durum sunar.

## Etkileşim ve durumlar

- Yüklenme, boş sonuç, hata, yetersiz geçmiş ve tahmini veri durumları birbirinden ayrılır.
- Hover geri bildirimi ölçülüdür; hareket işlevi açıklar, dekorasyon için kullanılmaz.
- Filtre değişiklikleri sonuç kapsamını görünür biçimde günceller; sıfırlama tüm ortak filtreleri başlangıç durumuna getirir.
- Sinyal kartları önem, güven, ticari etki, açıklama ve önerilen aksiyonu aynı hiyerarşiyle gösterir.

## Erişilebilirlik ve duyarlılık

- Bütün kontroller klavyeyle erişilebilir, görünür odaklı ve anlamlı erişilebilir ada sahip olmalıdır.
- Kontrast en az WCAG AA hedefini karşılar; durumlar yalnız renkle anlatılmaz.
- `prefers-reduced-motion` desteklenir.
- Mobilde gezinme uygun bir üst/çekmece yapısına dönüşür; tablolar kontrollü yatay kayar, ana aksiyonlar kaybolmaz.
- Native dialog veya eşdeğer erişilebilir modal deseni; açılışta odak yönetimi ve kapanışta tetikleyiciye dönüş sağlar.

## Kalite kapısı

Detaylı inceleme için açıklamalı analiz dizini ve tam sayfa varlık profilleri kullanılır. Profil başlığı, bölüm bağlantıları, açık dönem bilgisi ve sakin ayırıcı çizgiler içeriği düzenler. Müşteri/ürün detayları dar çekmeceye veya iç içe dikey kaydırma alanına sıkıştırılmaz. Veri tabloları gerektiğinde kendi alanında yatay kayar. Profil açılışında odak başlığa taşınır, kapanışta önceki tetikleyiciye döner. Profil sonundaki karar formu öneriyi ve başarı ölçütünü toplar; onay ayrı karar dosyasında verilir.

Her modül; görsel tutarlılık, hesaplama doğruluğu, filtre davranışı, klavye erişimi, responsive görünüm ve yönetici/satış/satın alma senaryolarıyla doğrulanmadan tamamlanmış sayılmaz.

## Harita ve ileri inceleme

Dünya haritasında mavi tonları pozitif ölçütün büyüklüğünü, kiremit kırmızısı negatif değeri, gri ise veri bulunmamasını anlatır. Sayısal karşılığı şehir seçimi ve tabloda her zaman vardır. Renk ölçeği dünya görünümünde ülke toplamlarına, seçilen ülkede şehir değerlerine göre değişir; lejant bunu belirtir. Harita sürükleme, +/− düğmeleri ve klavyeyle kullanılabilir. Şehir merkezi noktaları il alanı gibi sunulmaz.

Müşteri önerileri tekrarlanan KPI kartları yerine gerekçe / ürün / kanıt / sonraki işlem sütunlu satırlardır. Kategori incelemesi karşılaştırma tablosu ve yerinde açılan ürün kırılımıdır. Stok senaryosunda varsayım girişleri hesap sonucundan önce gelir; sonuçlar canlı bölgeyle bildirilir.
