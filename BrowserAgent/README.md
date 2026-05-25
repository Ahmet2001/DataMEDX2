# DataMedX2 Agent

DataMedX2 Agent, hackathon demosu için hazırlanmış klinik orkestrasyon ve doktor paneli uygulamasıdır. Doktor serbest prompt yazar; sistem hasta kaydını bulur, klinik alt agent'ları çalıştırır ve kanıtlı özet, risk kartları, timeline ve rapor çıktısı üretir.

## Öne Çıkanlar

- Serbest doktor prompt'u: `ADN_10016905`, `L1_ADN_10016905`, `No 501`, `501 nolu hasta` gibi hasta kodlarını otomatik normalize eder.
- Klinik agent ağı: hasta bulucu, klinik özet, lab, tedavi/ilaç, onkoloji durum, risk triage, timeline, rapor ve güvenlik denetçisi.
- Doktor paneli: kanıt/snippet paneli, kırmızı/sarı/yeşil risk kartları, hasta yolculuğu timeline'ı, Markdown/PDF rapor.
- Veri kalite kartı: uç lab değerlerini karar olarak değil, hekim doğrulaması gereken veri sinyali olarak işaretler.
- Jüri demo metrikleri: kanıt sayısı, risk sayısı, timeline olay sayısı ve tek tık rapor etkisi.

## Hızlı Başlangıç

```bash
git clone https://github.com/ethosoftai/DataMedX2-Agent.git
cd DataMedX2-Agent
cp .env.example .env
```

`.env` içine kendi model/API anahtarlarını yazdıktan sonra:

```bash
chmod +x run.sh
./run.sh
```

Panel adresleri:

```text
http://127.0.0.1:8001/doctor
http://127.0.0.1:8001/panel
```

## Qt Doktor Paneli

Old Windows styled masaüstü doktor paneli için backend'i ayrı terminalde açık tut:

```bash
./run.sh
```

İkinci terminalde Qt paneli başlat:

```bash
chmod +x run_qt_doctor.sh
./run_qt_doctor.sh
```

Backend farklı adresteyse:

```bash
DATAMEDX_API_BASE=http://127.0.0.1:8001 ./run_qt_doctor.sh
```

Qt panelde Klinik İstek kartındaki hasta box'ı ve slider ile CSV'deki hastalar arasında gezebilir, seçilen hastayı prompt'a otomatik ekleyebilirsin.

Üst menüdeki `Orchestration > Open Command Center`, web komuta merkezini ayrı bir Qt penceresinde açar. Buradan agent/tool toggle, env, workspace, heartbeat, logs ve paneldeki diğer kontroller kullanılabilir.

Linux/X11 üzerinde Qt `xcb` hatası verirse sistem paketi eksiktir:

```bash
sudo apt update
sudo apt install -y libxcb-cursor0
```

## Veri Dosyası

Varsayılan veri yolu:

```text
/home/rifat/Masaüstü/DataMedX2/hackathon_veri.csv
```

Farklı bir CSV kullanmak için `.env` içine şunu ekleyebilirsin:

```bash
HEALTH_DATA_CSV=/path/to/hackathon_veri.csv
```

## Güvenlik Notu

Runtime tek gerçek ayar dosyası olarak `.env` okur. `.env` repoya eklenmez; API key, token ve yerel ayarlar burada tutulur. GitHub'da sadece secretsız `.env.example` şablonu bulunur.

## Demo Prompt

```text
No 501 hastasını kısa özetle; kritik riskleri, kanıtları ve timeline'ı göster.
```
