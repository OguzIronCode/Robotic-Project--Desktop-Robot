"""Arka planda ESP32-CAM'den sürekli kare alan, tespit yapan ve son kareyi tutan sınıf.

Hız için: kareler MJPEG akışından (/stream) okunur, görüntü tam hızda yayınlanır; kutular en son
tespit sonucuyla çizilir. Tespit ayrı bir iş parçacığında çalışır ve akışı yavaşlatmaz.
Akış açılamazsa /capture ile tek tek kare çekmeye döner.
"""
import threading
import time

import cv2
import numpy as np

from kamera import kare_cek, mjpeg_oku


class KameraAkisi:
    def __init__(self, ip: str, bekleme: float = 0.0, dedektor=None, akis_yolu: str = "/stream"):
        self.ip = ip
        self.bekleme = bekleme          # yedek modda kareler arası ek bekleme (sn)
        self.akis_yolu = akis_yolu
        self.dedektor = dedektor        # tespit_et(kare) ve ciz(kare, tespitler) sunan nesne
        self.mod = "-"                  # "akış" | "capture"
        self.tespit_aktif = True
        self.akis_acik = True           # False: ESP32 akışını bırak (tarayıcı kendi akışını açabilsin)
        self.tespit_fps = 0.0
        self.tespit_ms = 0.0
        self._tespitler = []
        self._kare = None               # son ham kare (BGR)
        self._jpeg = None               # yayınlanan JPEG (tespit açıksa kutulu)
        self._no = 0                    # kare sayacı
        self.fps = 0.0
        self.bagli = False
        self._kilit = threading.Lock()
        self._olay = threading.Condition(self._kilit)
        self._calisiyor = False

    # ---- yaşam döngüsü ----
    def baslat(self):
        if self._calisiyor:
            return
        self._calisiyor = True
        threading.Thread(target=self._dongu, daemon=True).start()
        if self.dedektor is not None:
            threading.Thread(target=self._tespit_dongu, daemon=True).start()

    def durdur(self):
        self._calisiyor = False

    def ip_degistir(self, ip: str):
        self.ip = ip   # akış döngüsü IP değişimini fark edip yeniden bağlanır

    # ---- kare alma ----
    def _kare_isle(self, jpeg_ham: bytes | None, kare, son: float):
        """Yeni kareyi yayına hazırlar: tespit açıksa son sonuçları üzerine çizer."""
        if kare is None:
            kare = cv2.imdecode(np.frombuffer(jpeg_ham, np.uint8), cv2.IMREAD_COLOR)
            if kare is None:
                return son
        yayin = jpeg_ham
        if self.dedektor is not None and self.tespit_aktif and self._tespitler:
            cizili = self.dedektor.ciz(kare, self._tespitler)
            ok, buf = cv2.imencode(".jpg", cizili, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yayin = buf.tobytes() if ok else jpeg_ham
        elif yayin is None:
            ok, buf = cv2.imencode(".jpg", kare, [cv2.IMWRITE_JPEG_QUALITY, 85])
            yayin = buf.tobytes() if ok else None
        simdi = time.perf_counter()
        with self._olay:
            self._kare = kare
            self._jpeg = yayin
            self._no += 1
            self.bagli = True
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / max(simdi - son, 1e-6))
            self._olay.notify_all()
        return simdi

    def _dongu(self):
        while self._calisiyor:
            if not self.akis_acik:
                self.bagli = False
                self.mod = "bekle"
                time.sleep(0.3)
                continue
            ip = self.ip
            son = time.perf_counter()
            try:
                self.mod = "akış"
                for jpeg in mjpeg_oku(ip, self.akis_yolu, devam=lambda: self._calisiyor and self.ip == ip and self.akis_acik):
                    son = self._kare_isle(jpeg, None, son)
                if self.ip != ip:
                    continue        # IP değişti, yeniden bağlan
            except Exception as e:
                print(f"[akış] kesildi: {e.__class__.__name__}: {e}")
            if not self._calisiyor:
                break
            self.bagli = False
            # Yedek: akış açılamadıysa birkaç kez /capture dene, sonra akışı yeniden dene
            self.mod = "capture"
            for _ in range(5):
                if not self._calisiyor or self.ip != ip or not self.akis_acik:
                    break
                kare = kare_cek(self.ip, zaman_asimi=3.0, deneme=1)
                if kare is None:
                    time.sleep(1.0)
                    continue
                ok, buf = cv2.imencode(".jpg", kare, [cv2.IMWRITE_JPEG_QUALITY, 85])
                son = self._kare_isle(buf.tobytes() if ok else None, kare, son)
                if self.bekleme:
                    time.sleep(self.bekleme)
            time.sleep(0.5)

    # ---- tespit ----
    def _tespit_dongu(self):
        """En güncel kareyi alır, tespit eder. Yavaşsa ara kareleri atlar."""
        son_no = -1
        while self._calisiyor:
            kare, no = self.son_kare()
            if kare is None or no == son_no or not self.tespit_aktif:
                time.sleep(0.01)
                continue
            son_no = no
            t0 = time.perf_counter()
            try:
                tespitler = self.dedektor.tespit_et(kare)
            except Exception as e:
                print(f"[tespit] hata: {e}")
                time.sleep(1.0)
                continue
            dt = time.perf_counter() - t0
            with self._olay:
                self._tespitler = tespitler
                self.tespit_ms = dt * 1000
                self.tespit_fps = 0.8 * self.tespit_fps + 0.2 * (1.0 / max(dt, 1e-6))

    def tespitler(self):
        with self._kilit:
            return list(self._tespitler)

    # ---- okuma ----
    def son_kare(self):
        with self._kilit:
            return self._kare, self._no

    def son_jpeg(self):
        with self._kilit:
            return self._jpeg

    def yeni_jpeg_bekle(self, son_no: int, zaman_asimi: float = 5.0):
        """Yeni kare gelene kadar bekler. (jpeg, no) döndürür."""
        with self._olay:
            self._olay.wait_for(lambda: self._no != son_no, timeout=zaman_asimi)
            return self._jpeg, self._no
