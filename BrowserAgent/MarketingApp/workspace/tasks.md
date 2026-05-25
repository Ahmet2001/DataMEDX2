# Görev Planı: DataMedX Sağlık Yönetim Sistemi

## Ana Akış
- [x] Sağlık veri seti için klinik ajan mimarisi belirlendi.
- [x] Eski sosyal medya/content/browser agent akışı runtime listesinden çıkarıldı.
- [x] Hasta arama, klinik özet, zaman çizelgesi, lab, tedavi, onkoloji, risk, rapor ve güvenlik agent'ları tanımlandı.
- [x] `hackathon_veri.csv` üzerinde çalışan custom tool seti eklendi.

## Demo Senaryoları
- [ ] `ADN_10016905 hastasını SBAR formatında özetle`
- [ ] `Meme kanseri ve karaciğer metastaz sinyali olan ilk 10 hastayı bul`
- [ ] `ADN_10016905 için zaman çizelgesi çıkar`
- [ ] `ADN_10016905 için lab uyarılarını ve tedavi geçmişini özetle`
- [ ] `Bu raporu anonimleştir ve güvenlik açısından kontrol et`

## Klinik Güvenlik
- [ ] Yanıtlar kesin tanı/tedavi emri içermemeli
- [ ] Veri dışı çıkarımlar açıkça belirsiz olarak işaretlenmeli
- [ ] Ham hasta kimlikleri demo çıktılarında gerekirse maskelenmeli
- [ ] Son cevapta klinik karar destek notu bulunmalı
