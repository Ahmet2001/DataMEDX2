from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import dumps, search_patients


def hasta_ara(sorgu: str, limit: int = 10) -> str:
    """Hasta ID, tanı, ilaç, işlem veya klinik metin içinde arama yapar."""
    return dumps(search_patients(sorgu, limit=limit))
