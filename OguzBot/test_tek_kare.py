"""Aşama 1: tek kare + YOLO + kutulu görüntü kaydı.

Kullanım:
  python test_tek_kare.py --ip 192.168.1.50
  python test_tek_kare.py --dosya ornek.jpg            (kamera olmadan test)
  python test_tek_kare.py --ip 192.168.1.50 --hedef person bottle --guven 0.3
"""
import argparse
import os
import time

import cv2

from kamera import kare_cek
from tespit import Dedektor


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ip", help="ESP32-CAM IP adresi")
    p.add_argument("--dosya", help="Kamera yerine yerel görüntü dosyası")
    p.add_argument("--guven", type=float, default=0.4)
    p.add_argument("--hedef", nargs="*", help="Sadece bu sınıflar (boşsa tümü)")
    p.add_argument("--dondur", type=int, default=0, choices=[0, 90, 180, 270],
                   help="Kareyi saat yönünde döndür (kamera yan duruyorsa)")
    a = p.parse_args()

    if a.dosya:
        kare = cv2.imread(a.dosya)
    elif a.ip:
        kare = kare_cek(a.ip)
    else:
        p.error("--ip veya --dosya gerekli")
    if kare is None:
        raise SystemExit("Kare alınamadı.")

    donus = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}
    if a.dondur:
        kare = cv2.rotate(kare, donus[a.dondur])

    d = Dedektor(guven=a.guven, hedefler=a.hedef)
    t0 = time.time()
    tespitler = d.tespit_et(kare)
    ms = (time.time() - t0) * 1000

    print(f"{len(tespitler)} nesne, {ms:.0f} ms (ilk çağrı yavaş olabilir)")
    for t in tespitler:
        print(f"  {t['sinif']:<15} güven={t['guven']:.2f} merkez=({t['merkez'][0]:.0f},{t['merkez'][1]:.0f})")

    os.makedirs("kayit", exist_ok=True)
    yol = os.path.join("kayit", f"tespit_{int(time.time())}.jpg")
    cv2.imwrite(yol, d.ciz(kare, tespitler))
    print("Kaydedildi:", yol)


if __name__ == "__main__":
    main()
