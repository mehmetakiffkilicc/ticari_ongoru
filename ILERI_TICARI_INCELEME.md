# İleri ticari inceleme: uygulama ve sonraki veri ihtiyaçları

## Uygulanan yaklaşım

Karar hattı aynı kalır; uzman inceleme, kararın nedenini araştırma alanıdır. Müşteri sayfası görüşmeye hazırlanmayı, kategori sayfası portföy dengesini, ürün sayfası ekonomik dayanıklılığı ve stok sayfası müdahale önceliğini destekler.

| Alan | Yeni soru | Çalışan yanıt |
|---|---|---|
| Müşteri | Bir sonraki görüşmede ne önermeliyim? | Yenileme, kaybolan ürün, kategori içi çeşitlendirme ve yeni kategori; her önerinin kanıtı ve örneklemi |
| Kategori | Büyüme sağlıklı mı, birkaç ürüne mi bağlı? | 90 günlük katkı, önceki dönem, ağırlıklı marj, yoğunlaşma, zarar ve risk sayıları |
| Ürün | Büyürken müşteri veya marj riski birikiyor mu? | Satış değişimi, ilk üç müşteri payı, fatura ekonomisi; fiyat/maliyet ve kaynaklara geçiş |
| Stok | Tedarik sürem değişirse ne kadar ihtiyaç oluşur? | Tedarik süresi + güvenlik payı, hedef kapsama, tam koli ihtiyacı ve teslimat öncesi açık |
| Coğrafya | Değer hangi ülke ve şehirlerde oluşuyor? | Dünya/ülke haritası, ciro/kâr/marj renkleri, şehir seçimi ve sayısal performans tablosu |

## Öneri kuralları

Yenileme için en az üç ayrı alışveriş gününün medyan aralığı kullanılır. Son alımın üzerinden bu aralığın 0,8–2 katı geçmişse görüşme adayı oluşturulur. Ürün daha önce en az iki ayrı günde alınmış ve 90 günden uzun süredir alınmıyorsa geri kazanım adayıdır.

Portföy önerilerinde aynı ürünü almış en az beş diğer müşteri ve önerilecek ürünü alan en az üç müşteri aranır. Müşterinin daha önce aldığı ürünler yeni ürün önerilmez. Pozitif kâr katkısı olmayan yeni ürünler ve %30 üzeri iade oranlı adaylar bastırılır. Kategori üyeliği ürünün muadil olduğu anlamına gelmez. Öneriler satın alma olasılığı değildir.

“Karara taşı” ürün adını ve gerekçeyi işlem formuna koyar. Kullanıcı başarı ölçütünü belirler; kaynak profil ve tarih korunarak onay bekleyen dosya oluşur. Teklifi müşteriye gönderme veya dış sistemde sipariş oluşturma yapılmaz.

## Mevcut verinin sınırları

Stok miktarları mevcut modelde demo senaryosudur. Tedarik senaryosu, değişmeyen tüketim hızı varsayar. Açık siparişler, gerçek teslim süreleri, tedarikçi minimumları ve mevsimsellik hesaba katılmaz. Bunlar doğrulanmadan sonuç satın alma emri olarak kullanılamaz.

Harita şehir merkezlerine nokta koyar; il sınırlarına göre alan boyamaz. Konum eşleştirmesi ülke ve şehir adıyla yerel Natural Earth / GeoNames sözlüklerinden yapılır. Eşleşmeyen veya birden fazla yere karşılık gelen adlar yanlış konuma atanmaz; tabloda kalır. Harita hizmetine müşteri verisi gönderilmez.

## Sonraki geliştirmeyi en fazla iyileştirecek veriler

1. **Ürün kartı:** marka, boyut, içerik, kullanım amacı, muadil/üst segment ilişkisi. Böylece kategori benzerliğinden gerçek alternatif ürün önerisine geçilebilir.
2. **Stok ve tedarik:** fiziksel stok, açık sipariş, tedarikçi, teslim süresi, minimum alım ve koli çarpanı. Böylece senaryo doğrulanabilir alım planına dönüşür.
3. **Müşteri bağlamı:** iş türü, mağaza büyüklüğü, sözleşmeli ürünler ve ziyaret/teklif sonucu. Böylece benzer portföy grupları daha anlamlı olur.
4. **Coğrafi kimlik:** ISO ülke kodu, posta kodu ve doğrulanmış şehir/il kodu. Böylece yazım kaynaklı eşleşmeyenler azaltılır; il sınırı haritası güvenilir biçimde eklenebilir.
5. **Geri bildirim:** önerildi, ilgilenmedi, teklif istedi, sipariş verdi nedenleri. Önce açıklanabilir kural başarısı ölçülmeli; otomatik öğrenme ancak yeterli sonuç verisiyle değerlendirilmelidir.
