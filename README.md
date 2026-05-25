# DataMEDX2

Bu depo, onkoloji veri analizi, klinik karar destek ve yapay zeka tabanlı veri işleme araçlarını barındıran kapsamlı bir çalışma alanıdır. Proje iki ana bölümden oluşmaktadır: klinik veri analitiği dosyaları ve bağımsız olarak çalışan yapay zeka otomasyon paneli (`BrowserAgent`).

---

## 📂 Proje Yapısı

```text
DataMEDX2/
├── BrowserAgent/              # Yapay zeka otomasyonu ve Ajan Stüdyosu paneli (Bağımsız Proje)
├── hackathon_veri.csv         # [Yerele Özel] 114MB boyutunda 1.000 hastaya ait ham klinik veri seti (.gitignore altında)
├── okunabilir_onizleme.csv    # Veriyi hızlıca incelemek için ilk 30 satırdan oluşturulmuş önizleme dosyası
├── veri_okuma_rehberi.md      # Klinik verinin yapısı, kolonları ve anlamlarına dair detaylı açıklama rehberi
├── .gitignore                 # GitHub dosya boyutu limitleri ve hassas veriler için yapılandırma
└── README.md                  # Proje ana dökümantasyonu
```

---

## 📊 Klinik Veri Analitiği

Proje kök dizininde ham hastane ve klinik epikriz kayıtlarından derlenmiş onkoloji ağırlıklı bir veri seti bulunmaktadır.

* **`hackathon_veri.csv`**: 1.000 hastanın tüm klinik seyrini (laboratuvar sonuçları, ilaç reçeteleri, patoloji özetleri, muayene notları ve genetik testler) içeren detaylı bir veri setidir. *GitHub'ın 100 MB dosya boyutu limiti nedeniyle bu dosya repoda takip edilmez, sadece yerel çalışma alanınızda barındırılır.*
* **`okunabilir_onizleme.csv`**: Büyük veri setini yüklemeden hızlıca şema yapısını ve veri formatını anlamanız için oluşturulmuş 30 satırlık hafifletilmiş önizleme dosyasıdır.
* **`veri_okuma_rehberi.md`**: Klinik verideki kolon gruplarını (kimlik/demografi, klinik zamanlar, yaşam durumu, reçete ve order ilaçları, laboratuvar/genetik sonuçlar) açıklayan ve veriyi NLP/Yapay Zeka modelleriyle işlerken dikkat edilmesi gereken noktaları listeleyen rehberdir.

---

## 🤖 BrowserAgent (Ajan Stüdyosu & Kontrol Paneli)

`BrowserAgent` klasörü, LLM'ler ve çeşitli alt modeller (SubModels) yardımıyla çalışan, web otomasyonu, klinik veri analizi, içerik üretimi ve çoklu ajan yönetimi gerçekleştiren bağımsız bir uygulamadır.

### Özellikleri
* **Sağlık Verisi Araçları (Health AI):** Klinik metinleri temizleme, kohort filtreleme, laboratuvar trend analizi, ilaç özetleri çıkarma, metastaz bulgusu arama gibi onkoloji verilerine özel geliştirilmiş özel fonksiyonlar.
* **Ajan Stüdyosu (Agent Studio):** Ajanları görsel bir arayüzden yönetmenizi, yapılandırmanızı ve yeni ajan paketleri üretmenizi sağlayan kontrol paneli.
* **Sosyal Medya ve İçerik Otomasyonu:** X (Twitter), Instagram ve YouTube için otomatik içerik planlama ve yayınlama mekanizmaları.
* **Doktor Paneli (Doctor UI):** `qt_doctor_panel.py` ve web arayüzü (`doctor.html`) üzerinden klinik veriler üzerinde sorgulama, zaman çizelgesi oluşturma ve raporlama yapabilen arayüz.

### Çalıştırma Adımları

`BrowserAgent` altındaki projeyi yerelde çalıştırmak için aşağıdaki adımları uygulayabilirsiniz:

1. **Gereksinimleri Kurun:**
   ```bash
   cd BrowserAgent
   chmod +x run.sh
   ./run.sh
   ```
   *Bu betik otomatik olarak sanal ortamı (`.venv`) kuracak, gerekli Python paketlerini yükleyecek ve uygulamayı başlatacaktır.*

2. **Paneli Açın:**
   Uygulama başladıktan sonra tarayıcınızdan şu adrese giderek Ajan Kontrol Odasına ve Stüdyosuna erişebilirsiniz:
   * **http://127.0.0.1:8001/panel**

3. **Doktor Panelini Başlatmak İçin:**
   Klinik veri analizi arayüzünü (Qt tabanlı) açmak isterseniz:
   ```bash
   chmod +x run_qt_doctor.sh
   ./run_qt_doctor.sh
   ```

---

## ⚠️ Önemli Uyarılar

1. **Hassas Bilgiler:** `BrowserAgent` altındaki `.env` veya `.env.secrets` gibi dosyalar API anahtarları (Gemini, Telegram vb.) içerebilir. Bu depo **kamuya açık (public)** bir depo olduğu için, güvenlik amacıyla gizli anahtar içeren bu tür dosyalar `.gitignore` kuralları ile engellenmiştir. Yerel çalışmalarınızda `.env.example` dosyasını çoğaltarak kendi anahtarlarınızı eklemelisiniz.
2. **Kişisel Sağlık Verileri:** Klinik veri setinde bulunan serbest metin alanları hassas hasta bilgileri içerebileceğinden, veri işleme ve model eğitimi süreçlerinde yasal uyumluluklara ve anonimleştirme kurallarına dikkat edilmelidir.
