from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import dumps, schema_summary


def csv_schema_oku() -> str:
    """Hackathon sağlık CSV dosyasının kolonlarını, kayıt sayısını ve temel dağılımlarını döndürür."""
    return dumps(schema_summary())
