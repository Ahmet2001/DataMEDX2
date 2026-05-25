from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import dumps, extract_pathology_markers, patient_lookup


def patoloji_marker_cikar(client_id: str = "", metin: str = "") -> str:
    """Patoloji metninden ER, PR, HER2/CERB2 ve Ki-67 gibi marker sinyallerini çıkarır."""
    if client_id:
        row = patient_lookup(client_id=client_id)
        if not row:
            return dumps({"error": "Hasta kaydı bulunamadı.", "client_id": client_id})
        return dumps(extract_pathology_markers(row))
    return dumps(extract_pathology_markers(metin))
