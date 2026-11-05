# Robotic Project – Desktop Robot

ESP32-CAM (AI Thinker) kamera görüntüsünü, bilgisayarda çalışan bir nesne tanıma modeliyle birleştiren robotik proje.
ESP32 yalnızca görüntüyü yayınlar; yapay zekâ işi PC'de yapılır ve sonuç aynı web arayüzünden tek butonla açılıp kapatılır.

## Özellikler

- ESP32-CAM canlı MJPEG yayını ve kamera ayarları (Espressif CameraWebServer tabanlı)
- Web arayüzünde **Nesne Tespiti** butonu: PC'deki modeli açar, kutulu görüntüyü aynı sayfada gösterir
- **YOLOX-tiny** (ONNX) ile COCO-80 sınıflarında nesne tespiti, Türkçe etiketler
- PC kontrol paneli: güven eşiği, sadece belirli sınıfları gösterme, FPS ve gecikme bilgisi
- Varsayılan kamera ayarları: QVGA (320x240), XCLK 15 MHz, JPEG kalitesi 30

## Nasıl çalışır?

```
ESP32-CAM  ──(MJPEG :81/stream)──▶  PC: OguzBot sunucusu  ──(kutulu MJPEG :8000/video)──▶  Tarayıcı
                                    YOLOX-tiny ile tespit
```

1. ESP32-CAM akışı `http://<esp-ip>:81/stream` adresinde yayınlar.
2. OguzBot sunucusu bu akışı okur, nesneleri bulur ve kutulu görüntüyü `http://<pc-ip>:8000/video` adresinde yayınlar.
3. ESP32 sayfasındaki **Nesne Tespiti** butonuna basınca sayfa kendi akışını bırakır (ESP32 aynı anda tek akışa hizmet verir), PC'ye kameranın IP'sini bildirir ve PC'nin görüntüsünü gösterir. Tekrar basınca PC akışı bırakır ve sayfa kendi akışına döner.

## Klasör yapısı

```
CameraWebServer/        ESP32-CAM Arduino yazılımı
  CameraWebServer.ino   kamera ve WiFi ayarları
  app_httpd.cpp         HTTP sunucusu ve uç noktalar
  camera_index.h        web arayüzü (gzip'li HTML, Nesne Tespiti butonu dahil)
  secrets.h.example     WiFi bilgileri şablonu
OguzBot/                PC tarafı (Python / FastAPI)
  sunucu.py             API ve video yayını
  akis.py               kamera akışı + tespit döngüsü
  tespit.py             YOLOX nesne dedektörü
  static/index.html     PC kontrol paneli
  modeller/             ONNX model dosyaları
```

## Kurulum

### 1. ESP32-CAM
1. `CameraWebServer/secrets.h.example` dosyasını `secrets.h` olarak kopyalayıp WiFi adı ve şifresini yazın (`secrets.h` git'e gönderilmez).
2. Arduino IDE'de **AI Thinker ESP32-CAM** kartını seçin, PSRAM açık olsun, partition scheme olarak `partitions.csv` (en az 3 MB uygulama alanı) kullanın.
3. Yükleyin ve seri monitörde (115200) görünen IP adresini not edin.

Seri programlayıcıyla yüklerken: GPIO0 pinini GND'ye bağlayıp RST'ye basın, yükleme bitince kabloyu çıkarıp tekrar RST'ye basın.

### 2. PC (OguzBot)
```
cd OguzBot
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set ESP_IP=<esp-ip>
py -m uvicorn sunucu:app --host 0.0.0.0 --port 8000
```

### 3. Kullanım
1. Tarayıcıda `http://<esp-ip>` adresini açın.
2. **PC adresi** kutusuna `<pc-ip>:8000` yazın (tarayıcı hatırlar).
3. **Nesne Tespiti** butonuna basın.

PC kontrol paneli: `http://<pc-ip>:8000`

Windows güvenlik duvarı 8000 portu için izin isterse izin verin.

## Daha doğru model
Varsayılan `yolox_tiny.onnx` hızlıdır ama daha az doğrudur. Daha doğru sonuç için [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) `yolox_s.onnx` modelini indirip `OguzBot/modeller/` içine koyun ve şöyle başlatın:

```
set MODEL=modeller\yolox_s.onnx
```

## Sorun giderme

| Belirti | Olası neden / çözüm |
|---|---|
| Görüntü kasıyor | Çözünürlüğü QVGA'da tutun, ortamı aydınlatın (loş ortamda pozlama kare hızını düşürür), güç kaynağını/kablosunu değiştirin (`Brownout` hatası güç sorunudur) |
| Seri monitörde `Camera init failed` | Kamera kablosu veya besleme sorunu |
| Nesne Tespiti butonu bağlanamıyor | PC adresi doğru mu, sunucu çalışıyor mu, güvenlik duvarı 8000 portuna izin veriyor mu |
| PC görüntü alamıyor | ESP32 aynı anda tek akışa hizmet verir; tarayıcıdaki başka bir akış sekmesini kapatın |

## Lisanslar
Üçüncü taraf bileşenler ve lisansları için [`OguzBot/LISANSLAR.md`](OguzBot/LISANSLAR.md) dosyasına bakın.
