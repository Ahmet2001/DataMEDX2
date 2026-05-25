from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import anonymize_text


def anonimlestir(metin: str) -> str:
    """Hasta kimliklerini ve belirgin tarihleri rapor paylaşımı için maskeleyen basit anonimleştirme aracı."""
    return anonymize_text(metin)
