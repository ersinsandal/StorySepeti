# ⚡ StorySepeti

<div align="center">

![StorySepeti Banner](assets/icon.ico)

# StorySepeti — En Yüksek Kalitede Instagram Story & Highlight İndirici
**Instagram story ve highlight'larını (öne çıkanlarını) hiçbir kalite kaybı olmadan, tam orijinal çözünürlüğünde (1080p+, orijinal fotoğraf boyutları, 60fps MP4/MKV) arşivleyin.**

[![Python Sürümü](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Lisans](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011%20(x64)-0078D6.svg)]()
[![Kalite](https://img.shields.io/badge/kalite-Ger%C3%A7ek%201080p%2B%20%7C%20Orijinal%20HQ-purple.svg)]()
[![Sürüm](https://img.shields.io/badge/s%C3%BCr%C3%BCm-v1.0.0-orange.svg)](https://github.com/ersinsandal/StorySepeti/releases)

[🇬🇧 **Click here for English Documentation (README.md)**](README.md) • [🇹🇷 **Türkçe Dokümantasyon**](#genel-bakış)

</div>

---

## 📑 İçindekiler
1. [Genel Bakış](#genel-bakış)
2. [Neden StorySepeti? (720p Sınırı Nasıl Aşıldı?)](#neden-storysepeti-720p-sınırı-nasıl-aşıldı)
3. [Öne Çıkan Özellikler](#öne-çıkan-özellikler)
4. [Mimari & İşlem Hattı](#mimari--işlem-hattı)
5. [Kalite Motoru Teknik Detayları](#kalite-motoru-teknik-detayları)
6. [Güvenlik ve Gizlilik](#güvenlik-ve-gizlilik)
7. [Başlangıç & Kurulum](#başlangıç--kurulum)
   - [Yöntem 1: Bağımsız Windows EXE (Tavsiye Edilen)](#yöntem-1-bağımsız-windows-exe-tavsiye-edilen)
   - [Yöntem 2: Kaynak Koddan Çalıştırma](#yöntem-2-kaynak-koddan-çalıştırma)
   - [Yöntem 3: Kendi EXE Dosyanızı Derleme](#yöntem-3-kendi-exe-dosyanızı-derleme)
8. [Oturum & Çerez Yönetimi](#oturum--çerez-yönetimi)
9. [Proje Dizin Yapısı](#proje-dizin-yapısı)
10. [Sıkça Sorulan Sorular (SSS) & Sorun Giderme](#sıkça-sorulan-sorular-sss--sorun-giderme)
11. [Yasal Uyarı & Lisans](#yasal-uyarı--lisans)

---

<a name="genel-bakış"></a>
## 💡 Genel Bakış

**StorySepeti**; Instagram profil highlight (öne çıkanlar) albümlerini ve 24 saatlik geçici story'leri mümkün olan en yüksek görüntü ve ses kalitesinde arşivlemek için geliştirilmiş, modern ve son kullanıcı dostu bir Windows masaüstü uygulamasıdır.

İnternetteki klasik indirme siteleri ya da basit scraper araçları çoğu zaman oturumsuz çalıştığı için kullanıcılara Instagram'ın düşük çözünürlüklü (480p/720p) önizleme akışlarını sunar. StorySepeti ise bu kısıtlamaları aşmak için:
- **Doğrudan Instagram Web API'si:** `curl_cffi` ile Chrome 124 TLS parmak izi taklidi yaparak yüksek hızda doğrudan CDN akışlarını çeker.
- **Çok Aşamalı Yedek Motor (Fallback):** `yt-dlp` ve `gallery-dl` entegrasyonuyla API değişikliklerine karşı kesintisiz yedekleme sağlar.
- **DASH Kayıpsız Akış Birleştirme:** Ayrık 1080p video ve ana ses akışlarını kalite kaybı olmadan MKV/MP4 formatında birleştirir.
- **FFprobe Fiziksel Doğrulama:** İndirilen her videonun codec, genişlik, yükseklik ve bitrate değerlerini arka planda denetler.
- **Kurumsal Düzeyde Güvenlik:** Çerezleri asla düz metin (plaintext) olarak saklamaz; `Windows DPAPI` ve `AES-256-GCM` şifrelemesi kullanır.

---

<a name="neden-storysepeti-720p-sınırı-nasıl-aşıldı"></a>
## 🔬 Neden StorySepeti? (720p Sınırı Nasıl Aşıldı?)

Piyasadaki hemen her çevrim içi Instagram indirici **"720p Tavanı"** sorunundan muzdariptir:

| Özellik | Standart Web Araçları / Basit İndiriciler | StorySepeti |
| :--- | :--- | :--- |
| **Oturum Doğrulaması** | Yok (Anonim veya spam engeline takılan ortak proxy'ler) | Gerçek oturum çerezleri (`X-IG-App-ID` + DPAPI kasası) |
| **Sorgulanan Uç Nokta** | Eski `reels_media` uç noktası veya ham HTML | Modern Web API'si + tam DASH akış manifest çözümlemesi |
| **Maksimum Video Kalitesi** | Sunucu kotası için sıkıştırılmış **720x1280 (Progressive MP4)** | **Gerçek 1080p+ (DASH ayrık video + en iyi ses kayıpsız birleşik)** |
| **Fotoğraf Kalitesi** | Kırpılmış 640x640 veya 1080x1080 küçük resimler | Orijinal ham tuval boyutu (ör. **1206x2144**) |
| **Doğrulama** | Yok (eksik dosya veya ses/görüntü kayması fark edilmez) | **FFprobe** ile otomatik fiziksel akış denetimi |
| **Veri Gizliliği** | Çerezlerin 3. taraf web sitelerine düz metin gönderilmesi | **%100 Yerel işleme**; telemetri yok; Windows DPAPI ile şifreli |

### Teknik Neden:
Instagram, 1080p kalitesindeki videoları sunucu bant genişliğini optimize etmek amacıyla görüntü ve sesi birbirinden ayırarak (DASH akışları şeklinde) dağıtır. Basit araçlar bu iki akışı indirip senkronize birleştirecek donanıma sahip olmadıklarından, tarayıcılar için hazırlanan düşük kaliteli 720p önizleme MP4 dosyasına mecbur kalırlar. StorySepeti, manifestteki tüm temsilcileri tarar, en yüksek bitrate'e sahip 1080p video ve en net ses akışını kayıpsız olarak birleştirir.

---

<a name="öne-çıkan-özellikler"></a>
## ✨ Öne Çıkan Özellikler

### 1. 🎯 4 Özel İndirme Modu
- **Tek Aktif Story:** Herhangi bir aktif story bağlantısını (ör. `https://www.instagram.com/stories/kullanici/123456789/`) yapıştırarak o medyayı anında kaydedin.
- **Tüm Aktif Story'ler:** Bir profil kullanıcı adı veya story linki girerek kullanıcının son 24 saatteki tüm aktif story'lerini tarihli klasöre topluca arşivleyin.
- **Tek Highlight:** Doğrudan link veya `/s/` base64 kısa linkiyle seçtiğiniz öne çıkan albümünün tamamını indirin.
- **Tüm Profil Highlight'ları:** Bir profilin tüm öne çıkanlarını kapak fotoğrafları, başlıkları ve adetleriyle listeyin; istediklerinizi seçerek indirin.

### 2. 📁 Dahili İndirilenler (Downloads) Yöneticisi
- İndirdiğiniz tüm medyaları uygulama içinden listeleyen zengin panel.
- Filtreleme seçenekleri: **Tümü**, **Story'ler**, **Highlight'lar**, **Videolar** ve **Fotoğraflar**.
- Medya kartları üzerinde çözünürlük, dosya boyutu, oluşturulma tarihi ve dosya yolu bilgisi.
- Tek tıkla: **Varsayılan Oynatıcıda Aç**, **Dosya Gezgini'nde Göster** veya **Sil**.

### 3. ⚡ Dahili İndirme Motoru Güncelleyicisi
- Instagram API'si değiştiğinde veya yeni geliştirmeler çıktığında terminal açmanıza gerek yoktur.
- Uygulama başlangıcında otomatik GitHub sürüm kontrolü yapılır.
- **[Şimdi Güncelle]** butonuyla en güncel `yt-dlp` motoru uygulama içinden otomatik indirilir ve hemen devreye girer.

### 4. 🔒 3 Farklı Giriş Sihirbazı Seçeneği
- **Canlı Etkileşimli Tarayıcı Girişi:** Güvenli bir Chrome/Edge penceresi açılır; siz Instagram'a normal şekilde giriş yaptığınız anda oturumu otomatik algılayıp şifreler.
- **Tek Tıkla Tarayıcıdan Aktarma:** Chrome, Edge, Firefox, Brave veya Opera'da açık olan Instagram oturumunuzu tek tıkla içeri çeker.
- **Manuel Çerez Dosyası İçe Aktarma:** Standart Netscape / cookies.txt dosyalarını doğrular ve şifreli kasaya depolar.

### 5. 🖥️ Windows Entegrasyonu & Ergonomi
- **Sistem Tepsisi (System Tray):** Görev çubuğuna gizlenebilme ve sağ tık tepsisi menüsü.
- **Windows Masaüstü Bildirimleri:** İndirme tamamlandığında veya hata oluştuğunda sistem baloncuğu ile bilgilendirme.
- **Akıllı Pano ve Otomatik Yapıştırma:** Panoya kopyalanan Instagram linklerini algılama desteği.
- **Karanlık ve Aydınlık Tema:** CustomTkinter ile tasarlanmış modern arayüz ve eksiksiz Türkçe/İngilizce dil desteği.

---

<a name="mimari--işlem-hattı"></a>
## 🏗️ Mimari & İşlem Hattı

```
  ┌────────────────────────────────────────────────────────┐
  │                   StorySepeti UI                        │
  │     (CustomTkinter Modern Windows GUI / Tray)          │
  └──────────────────────────┬─────────────────────────────┘
                             │
                     [URL / Kullanıcı Adı]
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │                 URL & Niyet Ayrıştırıcı                │
  │     (Story, Highlight, Kısa Link Tespiti)              │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │                   Çerez Yöneticisi                     │
  │    (Windows DPAPI AES-256-GCM Bellek İçi Oturum)       │
  └──────────────────────────┬─────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│     Birincil Hızlı Motor      │ │       İkincil Yedek Motor     │
│   Instagram Web API (Yerel)   │ │    yt-dlp + gallery-dl Motoru │
│   - curl_cffi Chrome 124 TLS  │ │    - Çok parçalı DASH mux     │
│   - Ham JSON Manifest Analizi │ │    - res,br akış sıralama     │
│   - En Yüksek Çözünürlük CDN  │ │    - Yedek albüm tarayıcı     │
└───────────────┬───────────────┘ └───────────────┬───────────────┘
                │                                 │
                └────────────────┬────────────────┘
                                 │
                                 ▼
  ┌────────────────────────────────────────────────────────┐
  │             Fiziksel Doğrulayıcı (FFprobe)             │
  │   Kontrol: Codec (h264/hevc), Çözünürlük, Akış Sağlığı │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │            Kayıt Arşivi & İndirilenler Paneli          │
  │   - Windows Uyumlu Yol Düzenleme (Türkçe Harf Haritası)│
  │   - Düzenli Dizin: /kullanici/stories/YYYYAAGG/...     │
  └────────────────────────────────────────────────────────┘
```

---

<a name="kalite-motoru-teknik-detayları"></a>
## 📊 Kalite Motoru Teknik Detayları

### Video Seçim Stratejisi
1. **Kısa Kenar Kuralı (`min(width, height) >= 1080`):** Instagram story'leri dikey ($1080 \times 1920$) formattadır. Kalite motoru genişliğe değil, kısa kenara bakar.
2. **DASH Akış Birleştirme:** Instagram videoyu ve sesi ayrı akışlar halinde sunduğunda, StorySepeti her iki akışı hiçbir yeniden kodlama (transcode) kaybı olmadan **MKV** veya **MP4** kapsayıcısında birleştirir.
3. **Maksimum Bitrate (`-S res,br`):** Eşit çözünürlükler arasında her zaman en yüksek bitrate değerine sahip (en az sıkıştırılmış) akış tercih edilir.
4. **FFprobe Denetimi:** Her video dosyası diske yazıldıktan sonra `ffprobe` ile taranır. Bozuk veya sıfır baytlık dosyalar anında tespit edilir.

### Fotoğraf Seçim Stratejisi
1. Instagram API'sindeki `image_versions2.candidates` dizisi taranır.
2. Tüm adayların piksel alanı ($genişlik \times yükseklik$) hesaplanır.
3. 0 numaralı aday olan orijinal sıkıştırmasız görsel (örneğin $1206 \times 2144$) doğrudan Facebook CDN sunucularından indirilir.

---

<a name="güvenlik-ve-gizlilik"></a>
## 🔐 Güvenlik ve Gizlilik

StorySepeti, **Sıfır Güven (Zero-Trust) ve Sıfır Telemetri** felsefesiyle tasarlanmıştır:

- **Windows DPAPI Koruması:** Instagram çerezleriniz asla diske açık metin (plaintext) olarak kaydedilmez. Windows hesabınızın güvenlik anahtarına bağlı `CryptProtectData` (DPAPI) ile şifrelenir ve `session.enc` dosyasında tutulur. Dosya başka bir bilgisayara kopyalansa dahi çözülemez.
- **Harici Sunucu Yok:** Uygulama üçüncü taraf hiçbir sunucuya veri göndermez. Tüm iletişim doğrudan sizin bilgisayarınız ile resmi Instagram/Facebook sunucuları arasında gerçekleşir.
- **Güvenlik Duvarı Engeli Yok:** Uygulama dinleme portu (socket bind) açmaz. Yalnızca giden HTTPS (port 443) istekleri kullandığından Windows Güvenlik Duvarı uyarısı vermez.
- **Gömülü Manifest:** Standart kullanıcı haklarıyla (`asInvoker`) çalışacak şekilde derlenmiştir; gereksiz yönetici izni talep etmez.

---

<a name="başlangıç--kurulum"></a>
## 🚀 Başlangıç & Kurulum

### Yöntem 1: Bağımsız Windows EXE (Tavsiye Edilen)

Python veya komut satırı bilmenize gerek yoktur:
1. En son sürümü [Releases](https://github.com/ersinsandal/StorySepeti/releases) sayfasından indirin (veya projedeki `dist/StorySepeti/` klasörüne gidin).
2. **`StorySepeti.exe`** dosyasına çift tıklayarak çalıştırın.
3. **Giriş Sihirbazı** üzerinden Instagram hesabınıza giriş yapın.
4. Linkinizi yapıştırıp **İndir** butonuna tıklayın!

---

### Yöntem 2: Kaynak Koddan Çalıştırma

#### Gereksinimler:
- Windows 10 veya 11 (64-bit)
- Python 3.10, 3.11, 3.12 veya 3.13
- FFmpeg (sistem `PATH` değişkeninde bulunması tavsiye edilir)

#### Kurulum Adımları:
```powershell
# 1. Depoyu klonlayın
git clone https://github.com/ersinsandal/StorySepeti.git
cd StorySepeti

# 2. Sanal ortam oluşturun ve aktif edin
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. StorySepeti'u başlatın
python StorySepetiPro.py
```

---

### Yöntem 3: Kendi EXE Dosyanızı Derleme

Proje içerisinde yer alan PyInstaller betiği ile tek tıkla kendi bağımsız EXE paketinizi oluşturabilirsiniz:

```cmd
build.bat
```

Derleme bittiğinde tıkla-çalıştır paketiniz `dist\StorySepeti\StorySepeti.exe` konumunda hazır olacaktır.

---

<a name="oturum--çerez-yönetimi"></a>
## 🔑 Oturum & Çerez Yönetimi

Instagram aktif story'leri ve highlight'ları görüntülemek için oturum zorunluluğu uygular. StorySepeti size 3 güvenli yöntem sunar:

1. **Seçenek A: Canlı Etkileşimli Tarayıcı Girişi (En Kolayı)**
   - `Giriş Sihirbazı`nı açın.
   - `[🌐 Tarayıcıda Instagram'ı Aç]` butonuna basın.
   - Açılan pencerede normal şekilde hesabınıza girin; StorySepeti oturumu otomatik olarak algılayıp şifreler.
2. **Seçenek B: Tarayıcıdan Tek Tıkla Aktarma**
   - Bilgisayarınızdaki Chrome, Edge, Firefox, Brave veya Opera'da Instagram açıksa `[⚡ Oturumu Aktar]` butonuna basın.
3. **Seçenek C: cookies.txt Dosyası Yükleme**
   - Tarayıcınızdan aldığınız Netscape formatındaki çerez dosyasını `[📄 TXT Dosyası Seç]` ile içe aktarın.

---

<a name="proje-dizin-yapısı"></a>
## 📁 Proje Dizin Yapısı

```
StorySepeti/
├── StorySepetiPro.py              # Uygulama ana giriş noktası
├── build.bat                     # Windows PyInstaller otomatik derleme betiği
├── storysepeti.manifest           # Windows güvenlik ve DPI uyumluluk manifesti
├── version_info.txt              # EXE sürüm ve telif metaverileri
├── requirements.txt              # Python kütüphane bağımlılıkları
├── assets/                       # İkon ve tema dosyaları
│   └── icon.ico
├── storysepeti/                   # Ana uygulama paketi
│   ├── app.py                    # Uygulama ana denetleyicisi
│   ├── config/                   # Ayarlar motoru (JSON tabanlı)
│   ├── cookies/                  # Güvenlik ve çerez katmanı (DPAPI)
│   ├── core/                     # İndirme ve kalite motoru (Native + yt-dlp)
│   ├── gui/                      # CustomTkinter arayüz bileşenleri
│   ├── i18n/                     # Türkçe ve İngilizce dil çevirileri
│   └── utils/                    # Yardımcı modüller (Dosya adlandırma, Pano, Bildirim)
└── tests/                        # Otomatik birim testleri
    └── test_storysepeti.py
```

---

<a name="sıkça-sorulan-sorular-sss--sorun-giderme"></a>
## ❓ Sıkça Sorulan Sorular (SSS) & Sorun Giderme

#### S: Gizli hesapların story veya highlight'larını indirebilir miyim?
**C:** Evet! Giriş yaptığınız Instagram hesabı o gizli hesabı takip ediyorsa, StorySepeti izinli olduğunuz tüm içerikleri en yüksek kalitede indirebilir.

#### S: "Çerezler geçersiz veya süresi dolmuş" uyarısı alırsam ne yapmalıyım?
**C:** Tarayıcınızdan çıkış yaptığınızda Instagram eski çerezleri geçersiz kılar. **Giriş Sihirbazı**'nı açıp oturumunuzu tek tıkla yenilemeniz yeterlidir.

#### S: Instagram şifrem herhangi bir yere kaydediliyor mu?
**C:** **Kesinlikle hayır.** StorySepeti şifrenizi asla istemez, görmez ve kaydetmez. Yalnızca tarayıcınızın açık oturumunu koruyan şifreli `sessionid` çerezini yerel Windows kasasında tutar.

#### S: Bilgisayarımdan üçüncü taraf sunuculara veri aktarılıyor mu?
**C:** **Sıfır veri transferi.** Uygulama tamamen çevrim dışı güvenlik modelindedir; telemetri, izleme veya harici veri tabanı içermez. Tüm iletişim doğrudan sizin bilgisayarınız ile Instagram sunucuları arasındadır.

---

<a name="yasal-uyarı--lisans"></a>
## ⚖️ Yasal Uyarı & Lisans

### Yasal Uyarı
Bu yazılım yalnızca **kişisel arşivleme ve adil kullanım** amacıyla geliştirilmiştir. Kullanıcılar, Instagram'ın Hizmet Şartları'na uymak ve içerik üreticilerinin telif/kişisel gizlilik haklarına saygı göstermekle kendileri yükümlüdür. Geliştirici, yazılımın amacı dışında kullanımından sorumlu tutulamaz.

### Lisans
Bu proje **MIT Lisansı** ile lisanslanmıştır. Detaylar için [`LICENSE`](LICENSE) dosyasını inceleyebilirsiniz.

---

<div align="center">
Geliştirici: <b><a href="https://github.com/ersinsandal">Ersin Sandal</a></b>
</div>
