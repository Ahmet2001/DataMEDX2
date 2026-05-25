from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import dumps, make_report, patient_lookup


def rapor_olustur(client_id: str = "", id: str = "", no: str = "", format: str = "sbar") -> str:
    """Hasta için doktor dostu klinik özet, risk, lab ve SBAR raporu oluşturur."""
    row = patient_lookup(client_id=client_id, record_id=id, no=no)
    if not row:
        return dumps({"error": "Hasta kaydı bulunamadı.", "client_id": client_id, "id": id, "no": no})
    return make_report(row, report_format=format)
