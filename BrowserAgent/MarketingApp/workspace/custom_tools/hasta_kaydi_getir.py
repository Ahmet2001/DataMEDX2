from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import dumps, patient_lookup, patient_payload


def hasta_kaydi_getir(client_id: str = "", id: str = "", no: str = "", max_text_chars: int = 5000) -> str:
    """client_id, id veya No ile tek hastanın özetlenmiş ham klinik kaydını getirir."""
    row = patient_lookup(client_id=client_id, record_id=id, no=no)
    if not row:
        return dumps({"error": "Hasta kaydı bulunamadı.", "client_id": client_id, "id": id, "no": no})
    return dumps(patient_payload(row, max_text_chars=max_text_chars))
