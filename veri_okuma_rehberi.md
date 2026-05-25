# hackathon_veri.csv Okuma Rehberi

Bu dosya ham hastane/klinik kayıtlarından oluşturulmuş, hasta bazlı bir onkoloji veri seti gibi görünüyor. CSV dosyası ilk bakışta 365.498 fiziksel satır içeriyor gibi görünür; ancak klinik not alanlarının içinde satır sonları olduğu için gerçek CSV kaydı sayısı 1.000'dir.

## Kısa Özet

- Dosya: `hackathon_veri.csv`
- Format: UTF-8 CSV
- Gerçek kayıt sayısı: 1.000
- Sütun sayısı: 31
- Tekil `client_id`: 979
- Cinsiyet dağılımı: 640 erkek, 359 kadın, 1 diğer
- Ölüm tarihi bulunan kayıt: 128
- Veri ağırlıklı olarak onkoloji, laboratuvar, işlem, ilaç, patoloji, başvuru ve klinik not bilgisinden oluşuyor.

## Bu Veri Ne İçin Oluşturulmuş Olabilir?

Bu veri büyük olasılıkla bir hackathon, klinik yapay zeka projesi veya sağlık analitiği çalışması için hazırlanmış. İçerik ve kolon yapısına bakınca amaç şu başlıklardan biri veya birkaçıdır:

1. Hastanın klinik yolculuğunu modellemek  
   Başvuru, muayene, yatış, kemoterapi, radyoloji, laboratuvar, ilaç ve patoloji bilgileri aynı kayıtta toplanmış. Bu, hastanın zaman içindeki tedavi sürecini analiz etmek için uygun.

2. Onkoloji karar destek sistemi geliştirmek  
   Medikal onkoloji, radyasyon onkolojisi, kemoterapi, patoloji, genetik test ve laboratuvar sonuçları birlikte bulunuyor. Bu yapı tedavi önerisi, risk tahmini, progresyon takibi veya hasta gruplama için kullanılabilir.

3. Klinik metinlerden bilgi çıkarımı yapmak  
   `epikriz`, `hikaye`, `bulgu`, `not`, `patoloji rapor özet` gibi serbest metin alanları var. Bu alanlar NLP ile tanı, metastaz, evre, tedavi yanıtı, yan etki veya önemli klinik olay çıkarımı için hazırlanmış olabilir.

4. Zaman serisi ve olay sıralaması analizi yapmak  
   `işlem tarihi`, `reçete tarihi`, `order tarih`, `başvuru açılma tarihi`, `başvuru kapanma tarihi`, `genetic test tarih` gibi çok sayıda tarih alanı var. Bu, olayların hangi sırayla gerçekleştiğini incelemek için kullanılabilir.

5. Tahmin modeli eğitmek  
   Ölüm tarihi, laboratuvar sonuçları, ilaçlar, başvuru tipi, işlem geçmişi ve klinik notlar bir arada olduğu için sağkalım, yoğun bakım/yatış ihtimali, tedavi yanıtı veya komplikasyon riski gibi hedefler üretilebilir.

## Kolon Grupları

### Kimlik ve demografi

- `No`: Sıra veya kaynak sistem numarası.
- `id`: Kayıt kimliği.
- `client_id`: Hasta/kişi kimliği gibi duruyor.
- `cinsiyet`: Cinsiyet bilgisi.
- `doğum tarihi`: Doğum tarihi.

### Klinik birim ve zaman

- `department`: Hastanın görüldüğü bölüm veya bölümler.
- `oluşturma tarihi`: Kaydın oluşturulma zamanı.
- `başvuru açılma tarihi`: Başvurunun başlangıç zamanı.
- `başvuru kapanma tarihi`: Başvurunun kapanış zamanı.

### Yaşam durumu

- `ölüm durumu`: Bu örnekte boş görünüyor.
- `ölüm tarihi`: Ölüm tarihi varsa dolu.

### Klinik metinler

- `epikriz`: Klinik özet, tedavi süreci veya epikriz metni.
- `hikaye`: Hastanın öyküsü.
- `bulgu`: Fizik muayene ve klinik bulgular.
- `not`: Tedavi notu veya kontrol notu.
- `patoloji rapor özet`: Patoloji raporundan özet bilgiler.

### İlaç ve order bilgileri

- `ilac`: Reçetelenen ilaçlar.
- `reçete tarihi`: Reçete tarihleri.
- `order ilaç`: Hastane içi ilaç orderları.
- `order atc`: İlaçların ATC kodları.
- `order tarih`: Order zamanları.

### İşlem ve başvuru bilgileri

- `işlem adı`: Yapılan işlem, tetkik veya muayene adı.
- `işlem tipi`: İşlemin türü; örneğin laboratuvar, muayene, radyoloji, yatış.
- `işlem tarihi`: İşlem zamanı.
- `yatış tipi`: Ameliyat, medikal tedavi, yoğun bakım gibi yatış türleri.
- `başvuru tipi`: Genel muayene, kemoterapi, acil muayene vb.
- `geliş tipi`: Ayakta, günübirlik, yatarak vb.

### Genetik test ve laboratuvar

- `genetic test`: Test adı gibi görünüyor.
- `genetic test bilgi`: Bu kolon ismine rağmen çoğunlukla laboratuvar/test sonuç değerleri içeriyor gibi duruyor.
- `genetic test tarih`: Test/sonuç tarihleri gibi duruyor.
- `lab_sonuclari`: Laboratuvar sonuçlarının okunabilir metin hali.

## En Sık Görülen Değerler

### Departman

- Medikal onkoloji: 18.230 tekrar
- Radyasyon onkolojisi: 598 tekrar

### İşlem Tipi

- Laboratuar: 152.357
- Diğer: 71.326
- Yatış: 17.826
- Muayene: 14.016
- Radyoloji: 9.697
- Kontrol muayenesi: 3.544
- Patoloji: 2.085
- Yoğun bakım: 1.927
- Ameliyat: 1.610

### Başvuru Tipi

- Genel muayene: 28.140
- Medikal tedavi: 6.962
- Kemoterapi: 5.049
- Kontrol muayenesi: 2.788
- Acil muayene: 2.500

### Geliş Tipi

- Ayakta: 34.239
- Günübirlik: 10.283
- Yatarak: 3.092

### En Sık İşlemler

- Tam kan sayımı / hemogram
- Kreatinin
- Potasyum
- Sodyum
- ALT / AST
- Kalsiyum
- CRP
- Glukoz
- Tıbbi onkoloji muayenesi

## Okurken Dikkat Edilecek Noktalar

- Bir hücre içinde birden fazla değer var. Örneğin `işlem adı`, `işlem tarihi` ve `işlem tipi` kolonları köşeli parantezli listeler halinde tutulmuş.
- Aynı satır genellikle tek bir hastanın çok sayıda başvurusunu/işlemini birleştiriyor.
- Bazı kolon adları içerikle tam uyumlu olmayabilir. Özellikle `genetic test bilgi` ve `genetic test tarih` alanları laboratuvar sonuçlarıyla karışmış görünüyor.
- Serbest metinlerde yazım farklılıkları, büyük/küçük harf karışıklığı ve `_x000D_` gibi Excel kaynaklı satır sonu izleri var.
- Bu veri kişisel sağlık verisi niteliğinde görünüyor; paylaşım, model eğitimi ve raporlama sırasında anonimleştirme ve erişim kontrolü gerekir.

## Oluşturulan Yardımcı Dosya

- `okunabilir_onizleme.csv`: İlk 30 kayıttan seçilmiş kolonlarla hazırlanmış, uzun metinleri kısaltılmış okunabilir önizleme.

