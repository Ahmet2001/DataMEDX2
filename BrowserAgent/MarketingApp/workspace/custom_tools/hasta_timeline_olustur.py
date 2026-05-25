from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import build_timeline, dumps, patient_lookup


def hasta_timeline_olustur(client_id: str = "", id: str = "", no: str = "", limit: int = 120) -> str:
    """Hastanın işlem, reçete, order ve test olaylarından kronolojik zaman çizelgesi oluşturur."""
    row = patient_lookup(client_id=client_id, record_id=id, no=no)
    if not row:
        return dumps({"error": "Hasta kaydı bulunamadı.", "client_id": client_id, "id": id, "no": no})
    return dumps(build_timeline(row, limit=limit))
