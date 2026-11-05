"""ESP32-CAM /capture adresinden kare çekme (zaman aşımı + yeniden deneme)."""
import time

import cv2
import numpy as np
import requests


def kare_cek(esp_ip: str, zaman_asimi: float = 3.0, deneme: int = 3):
    """Tek JPEG kareyi BGR numpy dizisi olarak döndürür. Başarısızsa None."""
    url = f"http://{esp_ip}/capture"
    for i in range(deneme):
        try:
            r = requests.get(url, timeout=zaman_asimi)
            r.raise_for_status()
            kare = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
            if kare is not None:
                return kare
        except requests.RequestException as e:
            print(f"[kamera] deneme {i + 1}/{deneme} başarısız: {e}")
        time.sleep(0.3)
    return None


def mjpeg_oku(ip: str, yol: str = "/stream", zaman_asimi: float = 5.0, devam=lambda: True):
    """MJPEG akışından ham JPEG baytlarını tek tek üretir. Bağlantı koparsa istisna fırlatır.

    devam: False döndürürse (örn. IP değişti) akış temizçe kapatılır.
    """
    # ESP32-CAM akışı 81. portta (stream_httpd); ip içinde port verilmişse ona dokunma
    url = f"http://{ip}{yol}" if ":" in ip else f"http://{ip}:81{yol}"
    with requests.get(url, stream=True, timeout=zaman_asimi) as r:
        r.raise_for_status()
        tampon = b""
        for parca in r.iter_content(chunk_size=4096):
            if not devam():
                return
            tampon += parca
            while True:
                a = tampon.find(b"\xff\xd8")
                if a < 0:
                    tampon = tampon[-1:]
                    break
                b = tampon.find(b"\xff\xd9", a + 2)
                if b < 0:
                    tampon = tampon[a:]
                    break
                yield tampon[a:b + 2]
                tampon = tampon[b + 2:]
