"""FastAPI sunucusu: ESP32-CAM görüntüsünü tarayıcıya aktarır.

Çalıştırma:
  python -m uvicorn sunucu:app --host 0.0.0.0 --port 8000
  (kamera IP'sini değiştirmek için: set ESP_IP=10.25.66.134)
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel

from akis import KameraAkisi
from etiketler import ingilizce, turkce
from tespit import Dedektor, MODEL_YOLU

ESP_IP = os.environ.get("ESP_IP", "10.25.66.134")
MODEL = os.environ.get("MODEL", MODEL_YOLU)   # örn: modeller/yolox_s.onnx
KLASOR = os.path.dirname(os.path.abspath(__file__))

dedektor = Dedektor(MODEL)
akis = KameraAkisi(ESP_IP, dedektor=dedektor)


@asynccontextmanager
async def omur(app: FastAPI):
    akis.baslat()
    yield
    akis.durdur()


app = FastAPI(title="OguzBot Sunucu", lifespan=omur)
# ESP32-CAM sayfasındaki "Nesne Tespiti" butonu bu sunucuyu başka kökenden (http://<esp-ip>) çağırır
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class IpGirdi(BaseModel):
    ip: str


class TespitAyar(BaseModel):
    aktif: bool | None = None
    guven: float | None = None
    hedefler: list[str] | None = None   # boş liste = tüm sınıflar
    akis: bool | None = None            # False = ESP32 akışını bırak


@app.get("/")
def anasayfa():
    return FileResponse(os.path.join(KLASOR, "static", "index.html"))


@app.get("/api/durum")
def durum():
    return {"ip": akis.ip, "bagli": akis.bagli, "fps": round(akis.fps, 1),
            "tespit_fps": round(akis.tespit_fps, 1), "tespit_ms": round(akis.tespit_ms),
            "tespit_aktif": akis.tespit_aktif, "model": os.path.basename(MODEL),
            "guven": dedektor.guven, "hedefler": sorted(turkce(h) for h in (dedektor.hedefler or []))}


@app.get("/api/tespit")
def tespit():
    return {"tespitler": akis.tespitler()}


@app.get("/api/siniflar")
def siniflar():
    return {"siniflar": [turkce(a) for a in dedektor.siniflar]}


@app.post("/api/tespit-ayar")
def tespit_ayar(g: TespitAyar):
    if g.aktif is not None:
        akis.tespit_aktif = g.aktif
    if g.akis is not None:
        akis.akis_acik = g.akis
    if g.guven is not None:
        dedektor.guven = min(max(g.guven, 0.05), 0.95)
    if g.hedefler is not None:
        dedektor.hedefler = {ingilizce(h) for h in g.hedefler if h.strip()} or None
    return durum()


@app.post("/api/ip")
def ip_ayarla(g: IpGirdi):
    ip = g.ip.strip()
    if not ip:
        raise HTTPException(400, "IP boş olamaz")
    akis.ip_degistir(ip)
    return {"ip": akis.ip}


@app.get("/api/kare")
def kare():
    jpeg = akis.son_jpeg()
    if jpeg is None:
        raise HTTPException(503, "Henüz kare yok")
    return Response(jpeg, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


def _mjpeg():
    no = -1
    while True:
        jpeg, no = akis.yeni_jpeg_bekle(no)
        if jpeg is None:
            continue
        yield (b"--kare\r\nContent-Type: image/jpeg\r\nContent-Length: "
               + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n")


@app.get("/video")
def video():
    return StreamingResponse(_mjpeg(), media_type="multipart/x-mixed-replace; boundary=kare")
