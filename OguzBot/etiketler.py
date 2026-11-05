"""COCO (80 sınıf) İngilizce -> Türkçe etiket sözlüğü.

Farklı bir model kullanılırsa sözlükte olmayan sınıflar İngilizce adıyla gösterilir.
"""

TR = {
    "person": "insan", "bicycle": "bisiklet", "car": "araba", "motorcycle": "motosiklet",
    "airplane": "uçak", "bus": "otobüs", "train": "tren", "truck": "kamyon", "boat": "tekne",
    "traffic light": "trafik ışığı", "fire hydrant": "yangın musluğu", "stop sign": "dur tabelası",
    "parking meter": "parkmetre", "bench": "bank", "bird": "kuş", "cat": "kedi", "dog": "köpek",
    "horse": "at", "sheep": "koyun", "cow": "inek", "elephant": "fil", "bear": "ayı",
    "zebra": "zebra", "giraffe": "zürafa", "backpack": "sırt çantası", "umbrella": "şemsiye",
    "handbag": "el çantası", "tie": "kravat", "suitcase": "bavul", "frisbee": "frizbi",
    "skis": "kayak", "snowboard": "snowboard", "sports ball": "top", "kite": "uçurtma",
    "baseball bat": "beyzbol sopası", "baseball glove": "beyzbol eldiveni", "skateboard": "kaykay",
    "surfboard": "sörf tahtası", "tennis racket": "tenis raketi", "bottle": "şişe",
    "wine glass": "şarap kadehi", "cup": "bardak", "fork": "çatal", "knife": "bıçak",
    "spoon": "kaşık", "bowl": "kase", "banana": "muz", "apple": "elma", "sandwich": "sandviç",
    "orange": "portakal", "broccoli": "brokoli", "carrot": "havuç", "hot dog": "sosisli",
    "pizza": "pizza", "donut": "donut", "cake": "pasta", "chair": "sandalye", "couch": "koltuk",
    "potted plant": "saksı bitkisi", "bed": "yatak", "dining table": "yemek masası",
    "toilet": "tuvalet", "tv": "televizyon", "laptop": "dizüstü bilgisayar", "mouse": "fare",
    "remote": "kumanda", "keyboard": "klavye", "cell phone": "cep telefonu",
    "microwave": "mikrodalga", "oven": "fırın", "toaster": "ekmek kızartma makinesi",
    "sink": "lavabo", "refrigerator": "buzdolabı", "book": "kitap", "clock": "saat",
    "vase": "vazo", "scissors": "makas", "teddy bear": "oyuncak ayı", "hair drier": "saç kurutma makinesi",
    "toothbrush": "diş fırçası",
}

EN = {v: k for k, v in TR.items()}


def turkce(ad: str) -> str:
    return TR.get(ad, ad)


def ingilizce(ad: str) -> str:
    """Kullanıcı Türkçe ya da İngilizce yazmış olabilir; İngilizce model adını döndürür."""
    a = ad.strip().lower()
    return EN.get(a, a)
