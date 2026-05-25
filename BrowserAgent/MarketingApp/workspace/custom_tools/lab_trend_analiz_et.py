from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collections import defaultdict
from _saglik_veri_utils import dumps, extract_labs, patient_lookup


def lab_trend_analiz_et(client_id: str, analit: str = "") -> str:
    """Hastanın parse edilebilen lab sonuçlarını analit bazında tarih sırasıyla gruplar."""
    row = patient_lookup(client_id=client_id)
    if not row:
        return dumps({"error": "Hasta kaydı bulunamadı.", "client_id": client_id})
    grouped = defaultdict(list)
    wanted = (analit or "").strip().lower()
    for item in extract_labs(row):
        if wanted and wanted not in item["analyte"].lower():
            continue
        grouped[item["analyte"]].append(item)
    return dumps(dict(grouped))
