from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saglik_veri_utils import clean_text


def klinik_metin_temizle(metin: str, max_karakter: int = 4000) -> str:
    """Excel satır sonu izleri ve fazla boşlukları temizleyerek klinik metni okunabilir hale getirir."""
    return clean_text(metin, max_karakter)
