from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import cohort_stats, dumps


def kohort_istatistik_uret() -> str:
    """Tüm veri seti için demografi, ölüm tarihi, metastaz sinyali, bölüm, işlem ve ilaç istatistikleri üretir."""
    return dumps(cohort_stats())
