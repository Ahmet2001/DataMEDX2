from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import dumps, extract_labs, latest_labs, patient_lookup


def lab_sonuclari_parse_et(client_id: str = "", metin: str = "") -> str:
    """Lab metinlerini WBC, HGB, PLT, kreatinin, AST/ALT, CRP ve elektrolitler için parse eder."""
    if client_id:
        row = patient_lookup(client_id=client_id)
        if not row:
            return dumps({"error": "Hasta kaydı bulunamadı.", "client_id": client_id})
        return dumps(latest_labs(row))
    return dumps({"parsed": extract_labs(metin)})
