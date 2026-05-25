from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import dumps, extract_clinical_entities, patient_lookup


def klinik_varlik_cikar(client_id: str = "", metin: str = "") -> str:
    """Klinik metinden olası tanı, ECOG, boy/kilo, metastaz sahası ve semptom sinyallerini çıkarır."""
    if client_id:
        row = patient_lookup(client_id=client_id)
        if not row:
            return dumps({"error": "Hasta kaydı bulunamadı.", "client_id": client_id})
        return dumps(extract_clinical_entities(row))
    return dumps(extract_clinical_entities(metin))
