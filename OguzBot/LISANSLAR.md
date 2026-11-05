# Üçüncü taraf bileşenler ve lisansları

Bu liste mühendislik takibi içindir, hukuki tavsiye değildir. Ürünü yayınlamadan önce her bileşenin
resmi lisans metnini doğrulayın ve gerekirse hukuk danışmanına gösterin.

## Modeller

| Bileşen | Kullanım | Lisans | Kaynak |
|---|---|---|---|
| YOLOX (`modeller/yolox_s.onnx`) | Nesne tespiti | Apache-2.0 | Megvii-BaseDetection/YOLOX |

## Kütüphaneler

| Bileşen | Lisans |
|---|---|
| OpenCV | Apache-2.0 |
| NumPy | BSD-3-Clause |
| Pillow | MIT-CMU (HPND) |
| requests | Apache-2.0 |
| FastAPI | MIT |
| Uvicorn | BSD-3-Clause |

## Dikkat edilecek noktalar

- **Ultralytics / YOLOv8 / YOLO11 kullanılmıyor.** Bunlar AGPL-3.0 lisanslıdır ve ticari kapalı kaynak
  üründe ücretli lisans gerektirir. Projeye geri eklenmemelidir.
- **Gizlilik:** Kamera görüntüsünde kişiler görünebilir. Görüntüleri diske kaydetmeyin ve
  repoya kişi içeren örnek görüntü eklemeyin.
- **Font:** Çizimde sistem fontu (Arial vb.) kullanılır. Ürünle birlikte dağıtmayacaksanız sorun
  yoktur, dağıtacaksanız açık lisanslı bir font (örn. DejaVu Sans) paketleyin.
