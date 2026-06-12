# 🚀 Twiez Optimizer Changelog

Twiez Optimizer'ın gelişim sürecini ve yeniliklerini buradan takip edebilirsiniz! Projemiz her geçen gün daha kararlı, hızlı ve kullanıcı dostu olmaya devam ediyor. 

---

## [v1.3.0] - Dev Ağ, Güvenlik ve i18n Güncellemesi 🧽🌐🌍
*Twiez Optimizer artık sadece bir temizleyici değil; sisteminizi derinlemesine arındıran, ağınızı/gizliliğinizi koruyan ve %100 dil desteğine sahip devasa bir modül paketi haline geldi.*

### ✨ Yeni Modüller ve Özellikler
- **🧽 Sistem Arındırıcı (Windows Debloater):** 
  - Arka planda kaynak tüketen, zorla yüklenmiş Windows uygulamalarını (Candy Crush, Xbox, Cortana vb.) tek tıkla sistemden kazıyın.
  - Microsoft'un arka planda çalışan Telemetri (izleme/tanılama) servislerini kapatarak sistem performansınızı ve gizliliğinizi en üst düzeye çıkarın.
- **🌐 Ağ ve DNS Optimizatörü:**
  - İnternetteki en hızlı ve güvenli DNS sunucularına (Cloudflare, Google, Quad9) tek tıkla geçiş yapın; rekabetçi oyunlarda pinginizi düşürün.
  - **Hızlı Araçlar:** Sayfaların yüklenmemesi veya ağ kopmaları durumunda *DNS Önbelleği Temizleme (Flush DNS)* ve *Ağ Sıfırlama (Winsock)* butonları.
- **🛡️ Sistem Geri Yükleme (Restore Point) Altyapısı:** 
  - Derin sistem optimizasyonları uygulanmadan saniyeler önce otomatik olarak bir Sistem Geri Yükleme Noktası oluşturulur. Sisteminiz her zaman güvende kalır.
- **🌍 Tam Kapsamlı Dil Desteği (i18n):**
  - Uygulamanın tüm arayüzü, bildirimleri ve hata mesajları %100 İngilizce ve Türkçe olarak baştan kodlandı. Uygulama dili anında ve sorunsuz bir şekilde değiştirilebiliyor.
- **💾 Akıllı Ayar Kalıcılığı (Settings Persistence):**
  - "Windows Ayarları", "Optimizasyon" ve "Temizlik" sekmelerinde yaptığınız tüm geçiş (toggle) seçimleri artık uygulamanın belleğine `settings.json` ile kaydediliyor.
  - Uygulamayı kapatıp açtığınızda tüm ayarlar bıraktığınız gibi sizi karşılıyor!

### 🐛 Hata Düzeltmeleri (Bug Fixes)
- **Dil Değiştirme Çökmeleri:** Dil değiştirme işlemi sırasında meydana gelen ölümcül çökmeler ve `NameError` hataları kökten çözüldü.
- **Sistem Temizleyici (Cleaner):** Temizlik esnasında alt barda beliren sayacın yanlış gösterilmesi engellendi. Artık saniye saniye kaç dosya silindiğini canlı görebilirsiniz.
- **DarkMessageBox Şeffaflık Sorunu:** Uyarı kutucuklarının arkasının transparan gözükmesine neden olan grafik hatası onarıldı.

### 💄 Arayüz ve Tasarım Geliştirmeleri (UI/UX)
- Çok yer kaplayan açıklama yazıları kaldırılıp yerlerine modern ve şık **`?` (InfoButton)** ikonları eklendi.
- Hata mesajları ve başarı bildirimleri yeniden tasarlandı. Tam ekran uyarılar yerine, sağ alt köşeden zarifçe beliren `CustomNotification` pop-up'ları kullanılıyor.
- Bildirim pencerelerindeki (DarkMessageBox) Windows emojilerinden kaynaklanan boyut ve kırpılma (yarım çıkma) sorunları tamamen giderildi.

---

## [v1.2.0] - Güvenlik ve Ağ Modülleri 🛡️ (Önceki Sürüm)
- Güvenlik Merkezi paneli tamamen yenilendi.
- Windows Defender ve Güvenlik Duvarı yönetim sistemleri entegre edildi.
- Arayüz renklerinde ve buton tasarımlarında minik revizeler yapıldı.
- `ToggleSwitch` bileşenlerine animasyonlu geçiş eklendi.

---

