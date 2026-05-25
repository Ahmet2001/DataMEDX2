from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import dumps, patient_lookup, treatment_summary


def ilac_tedavi_ozeti_cikar(client_id: str = "", id: str = "", no: str = "") -> str:
    """Hastanın ilaç, order, kemoterapi ve sistemik tedavi sinyallerini özetler."""
    row = patient_lookup(client_id=client_id, record_id=id, no=no)
    if not row:
        return dumps({"error": "Hasta kaydı bulunamadı.", "client_id": client_id, "id": id, "no": no})
    return dumps(treatment_summary(row))
