from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import dumps, safety_check


def cevap_guvenlik_kontrolu(cevap: str) -> str:
    """Klinik cevabı kesin tanı/tedavi iddiası, mahremiyet ve doktor doğrulaması açısından kontrol eder."""
    return dumps(safety_check(cevap))
