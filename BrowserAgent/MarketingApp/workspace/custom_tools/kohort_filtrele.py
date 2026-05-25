from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import dumps, filter_cohort


def kohort_filtrele(tani: str = "", cinsiyet: str = "", metastaz: str = "", ilac: str = "", islem: str = "", limit: int = 20) -> str:
    """Tanı, cinsiyet, metastaz sahası, ilaç veya işlem adına göre hasta kohortu filtreler."""
    return dumps(filter_cohort(tani=tani, cinsiyet=cinsiyet, metastaz=metastaz, ilac=ilac, islem=islem, limit=limit))
