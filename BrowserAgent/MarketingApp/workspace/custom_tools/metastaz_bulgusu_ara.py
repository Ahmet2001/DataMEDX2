from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import dumps, metastasis_matches


def metastaz_bulgusu_ara(client_id: str = "", sorgu: str = "", limit: int = 20) -> str:
    """Tek hastada veya tüm kohortta metastaz/metastatik hastalık sinyali arar."""
    return dumps(metastasis_matches(query=sorgu, client_id=client_id, limit=limit))
