"""YOLOX (Apache-2.0) ile genel nesne tespiti — yalnızca OpenCV (cv2.dnn), AGPL bağımlılığı yok.

Model dosyası değiştirilerek geliştirilebilir (yolox_tiny/s/m/l/x ONNX). Girdi boyutunu
modele göre ayarlayın: s/m/l/x -> 640, tiny/nano -> 416.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from etiketler import TR, ingilizce, turkce

MODEL_YOLU = os.path.join("modeller", "yolox_tiny.onnx")
COCO_SINIFLAR = list(TR.keys())          # COCO-80, standart sıra

_FONT_ADAYLARI = ["arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"]


def _font_yukle(boyut: int = 16):
    for ad in _FONT_ADAYLARI:
        try:
            return ImageFont.truetype(ad, boyut)
        except OSError:
            continue
    return ImageFont.load_default()


def _izgara(boyut: int):
    """YOLOX çıkışını çözmek için ızgara ve adım (stride) tabloları."""
    izgaralar, adimlar = [], []
    for s in (8, 16, 32):
        n = boyut // s
        xv, yv = np.meshgrid(np.arange(n), np.arange(n))
        izgaralar.append(np.stack((xv, yv), 2).reshape(-1, 2))
        adimlar.append(np.full((n * n, 1), s))
    return np.concatenate(izgaralar, 0).astype(np.float32), np.concatenate(adimlar, 0).astype(np.float32)


class Dedektor:
    def __init__(self, model_yolu: str = MODEL_YOLU, guven: float = 0.4, hedefler=None,
                 girdi_boyutu: int | None = None, nms_esigi: float = 0.45):
        if not os.path.exists(model_yolu):
            raise FileNotFoundError(f"Model bulunamadı: {model_yolu}")
        if girdi_boyutu is None:
            ad = os.path.basename(model_yolu).lower()
            girdi_boyutu = 416 if ("tiny" in ad or "nano" in ad) else 640
        self.net = cv2.dnn.readNetFromONNX(model_yolu)
        self.boyut = girdi_boyutu
        self.nms_esigi = nms_esigi
        self.siniflar = COCO_SINIFLAR
        self.guven = guven
        self.hedefler = {ingilizce(h) for h in hedefler} if hedefler else None
        self._izgara, self._adim = _izgara(girdi_boyutu)
        self._font = _font_yukle()

    def _on_isle(self, kare):
        """Oranı koruyarak 114 gri dolgu ile kare boyuta yerleştirir (letterbox)."""
        h, w = kare.shape[:2]
        oran = min(self.boyut / h, self.boyut / w)
        yw, yh = int(w * oran), int(h * oran)
        tuval = np.full((self.boyut, self.boyut, 3), 114, np.uint8)
        tuval[:yh, :yw] = cv2.resize(kare, (yw, yh), interpolation=cv2.INTER_LINEAR)
        blob = tuval.astype(np.float32).transpose(2, 0, 1)[None]   # BGR, 0-255, normalizasyon yok
        return blob, oran

    def tespit_et(self, kare):
        """Liste döndürür: {sinif, etiket, guven, kutu:(x1,y1,x2,y2), merkez:(cx,cy)}"""
        blob, oran = self._on_isle(kare)
        self.net.setInput(blob)
        cikis = self.net.forward().reshape(-1, 85)

        xy = (cikis[:, :2] + self._izgara) * self._adim
        wh = np.exp(cikis[:, 2:4]) * self._adim
        skorlar = cikis[:, 4:5] * cikis[:, 5:]
        sinif_id = skorlar.argmax(1)
        skor = skorlar[np.arange(len(skorlar)), sinif_id]

        secim = skor >= self.guven
        if not secim.any():
            return []
        xy, wh, skor, sinif_id = xy[secim], wh[secim], skor[secim], sinif_id[secim]
        kutular = np.concatenate([xy - wh / 2, wh], 1) / oran       # x, y, w, h (orijinal piksel)

        idx = cv2.dnn.NMSBoxes(kutular.tolist(), skor.tolist(), self.guven, self.nms_esigi)
        H, W = kare.shape[:2]
        cikti = []
        for i in np.array(idx).flatten():
            ad = self.siniflar[int(sinif_id[i])]
            if self.hedefler and ad not in self.hedefler:
                continue
            x, y, w, h = kutular[i]
            x1, y1 = float(max(x, 0)), float(max(y, 0))
            x2, y2 = float(min(x + w, W)), float(min(y + h, H))
            cikti.append({
                "sinif": ad,
                "etiket": turkce(ad),
                "guven": float(skor[i]),
                "kutu": (x1, y1, x2, y2),
                "merkez": ((x1 + x2) / 2, (y1 + y2) / 2),
            })
        return cikti

    def ciz(self, kare, tespitler):
        """Kutu ve Türkçe etiketleri çizer (Pillow: ç, ğ, ı, ö, ş, ü desteklenir)."""
        resim = Image.fromarray(np.ascontiguousarray(kare[:, :, ::-1]))
        cizer = ImageDraw.Draw(resim)
        for t in tespitler:
            x1, y1, x2, y2 = map(int, t["kutu"])
            renk = tuple(t.get("renk", (0, 255, 0)))
            cizer.rectangle((x1, y1, x2, y2), outline=renk, width=2)
            yazi = f"{t.get('etiket', t['sinif'])} %{t['guven'] * 100:.0f}"
            sol, ust, sag, alt = cizer.textbbox((0, 0), yazi, font=self._font)
            gen, yuk = sag - sol + 8, alt - ust + 6
            y0 = max(y1 - yuk, 0)
            cizer.rectangle((x1, y0, x1 + gen, y0 + yuk), fill=renk)
            cizer.text((x1 + 4, y0 + 2 - ust), yazi, font=self._font, fill=(0, 0, 0))
        return np.asarray(resim)[:, :, ::-1].copy()
