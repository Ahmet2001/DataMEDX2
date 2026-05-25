from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


TEXT_COLUMNS = [
    "epikriz",
    "hikaye",
    "bulgu",
    "not",
    "patoloji rapor özet",
    "lab_sonuclari",
    "genetic test bilgi",
]

LIST_COLUMNS = [
    "department",
    "ilac",
    "reçete tarihi",
    "işlem adı",
    "işlem tipi",
    "işlem tarihi",
    "başvuru açılma tarihi",
    "başvuru kapanma tarihi",
    "yatış tipi",
    "başvuru tipi",
    "geliş tipi",
    "order ilaç",
    "order atc",
    "order tarih",
    "genetic test",
    "genetic test tarih",
]

METASTASIS_SITES = {
    "karaciğer": ["karaciğer", "karaciger", "hepatik"],
    "akciğer": ["akciğer", "akciger", "pulmoner", "toraks"],
    "kemik": ["kemik", "osseoz", "vertebra", "kostal"],
    "beyin": ["beyin", "kranial", "serebral"],
    "lenf nodu": ["lenf", "nod", "lap"],
    "periton": ["periton", "peritoneal"],
    "plevra": ["plevra", "plevral"],
}

LAB_RULES = {
    "WBC": {"aliases": ["wbc", "lökosit", "lokosit"], "low": 4.0, "high": 11.0, "unit": "K/uL"},
    "NEUT#": {"aliases": ["neut#", "neu#", "nötrofil#", "notrofil#"], "low": 1.5, "high": 7.5, "unit": "K/uL"},
    "HGB": {"aliases": ["hgb", "hemoglobin"], "low": 12.0, "high": 17.5, "unit": "g/dL"},
    "PLT": {"aliases": ["plt", "trombosit"], "low": 150.0, "high": 450.0, "unit": "K/uL"},
    "Kreatinin": {"aliases": ["kreatinin", "creatinine"], "low": None, "high": 1.3, "unit": "mg/dL"},
    "AST": {"aliases": ["ast", "sgot"], "low": None, "high": 40.0, "unit": "U/L"},
    "ALT": {"aliases": ["alt", "sgpt"], "low": None, "high": 40.0, "unit": "U/L"},
    "CRP": {"aliases": ["crp", "c reaktif"], "low": None, "high": 5.0, "unit": "mg/L"},
    "Sodyum": {"aliases": ["sodyum", "sodium"], "low": 135.0, "high": 145.0, "unit": "mmol/L"},
    "Potasyum": {"aliases": ["potasyum", "potassium"], "low": 3.5, "high": 5.1, "unit": "mmol/L"},
    "Kalsiyum": {"aliases": ["kalsiyum", "calcium"], "low": 8.5, "high": 10.5, "unit": "mg/dL"},
    "Albümin": {"aliases": ["albümin", "albumin"], "low": 3.5, "high": None, "unit": "g/dL"},
    "Glukoz": {"aliases": ["glukoz", "glucose", "kan şekeri", "kan sekeri"], "low": 70.0, "high": 180.0, "unit": "mg/dL"},
}


def _data_path() -> Path:
    env_path = os.getenv("HEALTH_DATA_CSV")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return Path(__file__).resolve().parents[4] / "hackathon_veri.csv"


def _fold(text: str) -> str:
    table = str.maketrans(
        "ÇĞİIÖŞÜçğıöşüÂâÎîÛû",
        "CGIIOSUcgiosuAaIiUu",
    )
    return (text or "").translate(table).lower()


def clean_text(text: Any, max_chars: int | None = None) -> str:
    value = "" if text is None else str(text)
    value = value.replace("_x000D_", "\n").replace("\r", "\n").replace("\xa0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    value = value.strip()
    if max_chars and len(value) > max_chars:
        return value[: max(0, max_chars - 3)].rstrip() + "..."
    return value


def split_listish(value: Any, max_items: int | None = None) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    parts = [clean_text(part) for part in re.findall(r"\[([^\[\]]*?)\]", text, flags=re.S)]
    if not parts:
        parts = [clean_text(part) for part in re.split(r"\s*[;|]\s*", text) if clean_text(part)]
    parts = [part for part in parts if part]
    if max_items:
        return parts[:max_items]
    return parts


def _parse_datetime(value: Any) -> tuple[datetime | None, str]:
    text = clean_text(value)
    if not text:
        return None, ""
    candidates = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y",
        "%d/%m/%Y",
    ]
    for fmt in candidates:
        try:
            dt = datetime.strptime(text[:19], fmt)
            return dt, dt.isoformat(sep=" ")
        except ValueError:
            continue
    match = re.search(r"(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}:\d{2}))?", text)
    if match:
        raw = match.group(1) + (f" {match.group(2)}" if match.group(2) else "")
        return _parse_datetime(raw)
    match = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", text)
    if match:
        raw = f"{match.group(1).zfill(2)}.{match.group(2).zfill(2)}.{match.group(3)}"
        return _parse_datetime(raw)
    return None, text


def _safe_float(value: str) -> float | None:
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return None


def dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


@lru_cache(maxsize=1)
def load_records() -> tuple[dict[str, str], ...]:
    path = _data_path()
    if not path.exists():
        raise FileNotFoundError(f"Veri dosyasi bulunamadi: {path}")
    records: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            normalized = {str(k or "").strip(): str(v or "") for k, v in row.items()}
            records.append(normalized)
    return tuple(records)


def all_records() -> list[dict[str, str]]:
    return list(load_records())


def schema_summary() -> dict[str, Any]:
    records = all_records()
    columns = list(records[0].keys()) if records else []
    unique_clients = {row.get("client_id", "") for row in records if row.get("client_id")}
    gender_counts = Counter(clean_text(row.get("cinsiyet")) or "boş" for row in records)
    death_count = sum(1 for row in records if clean_text(row.get("ölüm tarihi")))
    return {
        "data_path": str(_data_path()),
        "record_count": len(records),
        "column_count": len(columns),
        "columns": columns,
        "unique_client_id": len(unique_clients),
        "gender_counts": dict(gender_counts),
        "death_date_present": death_count,
        "text_columns": TEXT_COLUMNS,
        "list_columns": LIST_COLUMNS,
    }


def _combined_text(row: dict[str, str], max_chars: int | None = None) -> str:
    parts = []
    for col in TEXT_COLUMNS:
        value = clean_text(row.get(col))
        if value:
            parts.append(f"{col}: {value}")
    combined = "\n\n".join(parts)
    return clean_text(combined, max_chars)


def _haystack(row: dict[str, str]) -> str:
    fields = [
        "No",
        "id",
        "client_id",
        "cinsiyet",
        "doğum tarihi",
        *TEXT_COLUMNS,
        *LIST_COLUMNS,
    ]
    return "\n".join(clean_text(row.get(col)) for col in fields if clean_text(row.get(col)))


def _snippet(text: str, query: str, radius: int = 180) -> str:
    folded_text = _fold(text)
    folded_query = _fold(query)
    pos = folded_text.find(folded_query)
    if pos < 0:
        return clean_text(text, radius * 2)
    start = max(0, pos - radius)
    end = min(len(text), pos + len(query) + radius)
    prefix = "..." if start else ""
    suffix = "..." if end < len(text) else ""
    return prefix + clean_text(text[start:end]) + suffix


def patient_identifier_variants(value: Any) -> set[str]:
    text = clean_text(value)
    if not text:
        return set()

    variants = {text}
    compact = re.sub(r"[\s\-]+", "_", text.upper()).strip("_")
    compact = re.sub(r"_+", "_", compact)
    if compact:
        variants.add(compact)

    for match in re.finditer(r"\b(?:L1[\s_-]*)?ADN[\s_-]*(\d{3,})\b", text, flags=re.I):
        digits = match.group(1)
        variants.add(f"ADN_{digits}")
        variants.add(f"L1_ADN_{digits}")
        variants.add(digits)

    if re.fullmatch(r"\d{6,}", text):
        variants.add(f"ADN_{text}")
        variants.add(f"L1_ADN_{text}")
    if re.fullmatch(r"\d{1,8}", text):
        variants.add(text)
    return {item for item in variants if item}


def extract_patient_identifier_candidates(text: Any) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []

    candidates: list[str] = []

    def add(value: str) -> None:
        value = clean_text(value)
        if value and value not in candidates:
            candidates.append(value)

    for match in re.finditer(r"\b(?:L1[\s_-]*)?ADN[\s_-]*\d{3,}\b", cleaned, flags=re.I):
        add(match.group(0))

    labeled_number = (
        r"\b(?:hasta|hasta\s*kodu|hasta\s*no|hasta\s*numara(?:s[ıi])?|"
        r"kay[ıi]t\s*no|record\s*id|no)\s*[:#=]?\s*(\d{1,8})\b"
    )
    for match in re.finditer(labeled_number, cleaned, flags=re.I):
        add(match.group(1))

    for match in re.finditer(r"\b(\d{1,8})\s*(?:nolu|no'?lu|numaral[ıi])\s+hasta\b", cleaned, flags=re.I):
        add(match.group(1))

    for match in re.finditer(r"\b\d{6,}\b", cleaned):
        add(match.group(0))

    stripped = cleaned.strip()
    if re.fullmatch(r"\d{1,8}", stripped):
        add(stripped)
    return candidates


def patient_lookup(client_id: str = "", record_id: str = "", no: str = "") -> dict[str, str] | None:
    candidates: set[str] = set()
    for value in (client_id, record_id, no):
        candidates.update(patient_identifier_variants(value))
    for row in all_records():
        row_identifiers: set[str] = set()
        row_identifiers.update(patient_identifier_variants(row.get("client_id")))
        row_identifiers.update(patient_identifier_variants(row.get("id")))
        row_identifiers.update(patient_identifier_variants(row.get("No")))
        if any(
            candidate in row_identifiers
            for candidate in candidates
        ):
            return row
    return None


def patient_brief(row: dict[str, str]) -> dict[str, Any]:
    departments = split_listish(row.get("department"), 5)
    diagnosis_terms = extract_clinical_entities(row).get("olasi_tanilar", [])[:5]
    gender = split_listish(row.get("cinsiyet"), 1)
    birth_date = split_listish(row.get("doğum tarihi"), 1)
    death_date = split_listish(row.get("ölüm tarihi"), 1)
    return {
        "No": row.get("No", ""),
        "id": row.get("id", ""),
        "client_id": row.get("client_id", ""),
        "cinsiyet": gender[0] if gender else clean_text(row.get("cinsiyet")),
        "doğum tarihi": birth_date[0] if birth_date else clean_text(row.get("doğum tarihi")),
        "ölüm tarihi": death_date[0] if death_date else clean_text(row.get("ölüm tarihi")),
        "department_sample": departments,
        "olasi_tanilar": diagnosis_terms,
    }


def search_patients(query: str, limit: int = 10) -> list[dict[str, Any]]:
    q = clean_text(query)
    if not q:
        return []
    folded_q = _fold(q)
    results = []
    for row in all_records():
        haystack = _haystack(row)
        folded_haystack = _fold(haystack)
        if folded_q in folded_haystack:
            results.append(
                {
                    **patient_brief(row),
                    "snippet": _snippet(haystack, q),
                }
            )
        if len(results) >= limit:
            break
    return results


def patient_payload(row: dict[str, str], max_text_chars: int = 5000) -> dict[str, Any]:
    payload = patient_brief(row)
    payload.update(
        {
            "başvuru tipi": split_listish(row.get("başvuru tipi"), 20),
            "geliş tipi": split_listish(row.get("geliş tipi"), 20),
            "yatış tipi": split_listish(row.get("yatış tipi"), 20),
            "işlem adı_sample": split_listish(row.get("işlem adı"), 40),
            "işlem tipi_sample": split_listish(row.get("işlem tipi"), 40),
            "ilac_sample": split_listish(row.get("ilac"), 40),
            "order_ilaç_sample": split_listish(row.get("order ilaç"), 40),
            "klinik_metin": _combined_text(row, max_text_chars),
        }
    )
    return payload


def build_timeline(row: dict[str, str], limit: int = 120) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    names = split_listish(row.get("işlem adı"))
    types = split_listish(row.get("işlem tipi"))
    dates = split_listish(row.get("işlem tarihi"))
    for idx, name in enumerate(names):
        raw_date = dates[idx] if idx < len(dates) else ""
        dt, iso = _parse_datetime(raw_date)
        events.append(
            {
                "date": iso,
                "_dt": dt,
                "category": types[idx] if idx < len(types) else "işlem",
                "title": name,
                "source": "işlem",
            }
        )

    meds = split_listish(row.get("ilac"))
    med_dates = split_listish(row.get("reçete tarihi"))
    for idx, med in enumerate(meds):
        raw_date = med_dates[idx] if idx < len(med_dates) else ""
        dt, iso = _parse_datetime(raw_date)
        events.append({"date": iso, "_dt": dt, "category": "reçete", "title": med, "source": "ilac"})

    orders = split_listish(row.get("order ilaç"))
    order_dates = split_listish(row.get("order tarih"))
    atcs = split_listish(row.get("order atc"))
    for idx, order in enumerate(orders):
        raw_date = order_dates[idx] if idx < len(order_dates) else ""
        dt, iso = _parse_datetime(raw_date)
        atc = f" | ATC: {atcs[idx]}" if idx < len(atcs) and atcs[idx] else ""
        events.append({"date": iso, "_dt": dt, "category": "order", "title": order + atc, "source": "order"})

    tests = split_listish(row.get("genetic test"))
    test_dates = split_listish(row.get("genetic test tarih"))
    for idx, test in enumerate(tests):
        raw_date = test_dates[idx] if idx < len(test_dates) else ""
        dt, iso = _parse_datetime(raw_date)
        events.append({"date": iso, "_dt": dt, "category": "test", "title": test, "source": "genetic/lab"})

    events.sort(key=lambda item: (item["_dt"] is None, item["_dt"] or datetime.max, item["source"]))
    cleaned = [{k: v for k, v in item.items() if k != "_dt"} for item in events]
    return cleaned[: max(1, min(limit, 500))]


def extract_clinical_entities(row_or_text: dict[str, str] | str) -> dict[str, Any]:
    if isinstance(row_or_text, dict):
        text = _combined_text(row_or_text)
    else:
        text = clean_text(row_or_text)
    folded = _fold(text)

    diagnosis_patterns = [
        r"(meme|akci[ğg]er|kolon|rektum|prostat|over|pankreas|mide|serviks|tiroid|beyin|karaci[ğg]er)[^\n,.]{0,45}(karsinom|kanser|malign|neoplazm)",
        r"(karsinom|kanser|malign neoplazm)[^\n,.]{0,45}(meme|akci[ğg]er|kolon|rektum|prostat|over|pankreas|mide|serviks|tiroid)",
    ]
    diagnoses = []
    for pattern in diagnosis_patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            value = clean_text(match.group(0), 140)
            if value and value not in diagnoses:
                diagnoses.append(value)

    ecog = sorted(set(re.findall(r"\bECOG\s*(?:PS)?\s*[:=]?\s*([0-4])", text, flags=re.I)))
    height = sorted(set(re.findall(r"\bBoy\s*[:=]?\s*(\d{2,3})\s*cm\b", text, flags=re.I)))
    weight = sorted(set(re.findall(r"\bKilo\s*[:=]?\s*(\d{2,3})\s*kg\b", text, flags=re.I)))

    metastasis_sites = []
    has_met_word = any(token in folded for token in ["metastaz", "metastatik", " met ", " met?"])
    for site, aliases in METASTASIS_SITES.items():
        if any(_fold(alias) in folded for alias in aliases) and has_met_word:
            metastasis_sites.append(site)

    symptoms = []
    symptom_terms = ["ağrı", "oksuruk", "öksürük", "nefes", "bulantı", "ateş", "göğüs ağrısı", "halsizlik"]
    for term in symptom_terms:
        if _fold(term) in folded:
            symptoms.append(term)

    return {
        "olasi_tanilar": diagnoses[:12],
        "ecog": ecog,
        "boy_cm": height[-1:] if height else [],
        "kilo_kg": weight[-1:] if weight else [],
        "metastaz_sahaları": metastasis_sites,
        "semptom_sinyalleri": sorted(set(symptoms)),
    }


def extract_pathology_markers(row_or_text: dict[str, str] | str) -> dict[str, Any]:
    text = _combined_text(row_or_text) if isinstance(row_or_text, dict) else clean_text(row_or_text)
    marker_patterns = {
        "ER": r"\bER\b\s*[:=]\s*([^\n,;]{1,90})",
        "PR": r"\bPR\b\s*[:=]\s*([^\n,;]{1,90})",
        "CERB2/HER2": r"\b(?:CERB2|HER2|C-ERB-B2)\b\s*[:=]\s*([^\n,;]{1,90})",
        "Ki-67": r"\bKI\s*-?\s*67\b\s*[:=]\s*([^\n,;]{1,90})",
    }
    markers: dict[str, list[str]] = {}
    next_marker_re = re.compile(r"\b(?:ER|PR|CERB2|HER2|C-ERB-B2|KI\s*-?\s*67)\b\s*[:=]", flags=re.I)
    for name, pattern in marker_patterns.items():
        values = []
        for match in re.finditer(pattern, text, flags=re.I):
            value = clean_text(match.group(1), 60)
            value = next_marker_re.split(value)[0].strip()
            value = re.split(r"[\n,;.]", value)[0].strip()
            if value and value not in values:
                values.append(value)
        if values:
            markers[name] = values[:5]
    pathology_text = clean_text((row_or_text.get("patoloji rapor özet", "") if isinstance(row_or_text, dict) else text), 1500)
    return {"markerlar": markers, "patoloji_ozet": pathology_text}


def extract_labs(row_or_text: dict[str, str] | str) -> list[dict[str, Any]]:
    if isinstance(row_or_text, dict):
        text = "\n".join(
            [
                clean_text(row_or_text.get("lab_sonuclari")),
                clean_text(row_or_text.get("genetic test bilgi")),
                clean_text(row_or_text.get("not")),
            ]
        )
    else:
        text = clean_text(row_or_text)
    if not text:
        return []

    labs: list[dict[str, Any]] = []
    current_date = ""
    tokens = re.split(r"[,;\n]+", text)
    for token in tokens:
        cleaned = clean_text(token)
        if not cleaned:
            continue
        date_match = re.search(r"(\d{1,2}[./]\d{1,2}[./]\d{4}|\d{4}-\d{2}-\d{2})", cleaned)
        if date_match:
            _, current_date = _parse_datetime(date_match.group(1))
        folded = _fold(cleaned)
        for canonical, rule in LAB_RULES.items():
            alias_match = None
            for alias in rule["aliases"]:
                folded_alias = _fold(alias).strip()
                if not folded_alias:
                    continue
                pattern = rf"(?<![a-z0-9]){re.escape(folded_alias)}(?![a-z0-9])"
                alias_match = re.search(pattern, folded)
                if alias_match:
                    break
            if not alias_match:
                continue

            tail = cleaned[alias_match.end() : alias_match.end() + 90]
            value_tail = re.sub(r"\(?\b\d{4}-\d{2}-\d{2}\b[^)\]]*", "", tail)
            value_tail = re.sub(r"\(?\b\d{1,2}[./]\d{1,2}[./]\d{4}\b[^)\]]*", "", value_tail)
            value_tail = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\b", "", value_tail)
            value_match = re.search(r"[:=]\s*([-+]?\d+(?:[,.]\d+)?)", value_tail)
            if not value_match:
                value_match = re.search(r"\b([-+]?\d+(?:[,.]\d+)?)\b", value_tail)
            if not value_match:
                continue
            value = _safe_float(value_match.group(1))
            if value is None:
                continue
            flag = "normal"
            if rule.get("low") is not None and value < float(rule["low"]):
                flag = "low"
            if rule.get("high") is not None and value > float(rule["high"]):
                flag = "high"
            labs.append(
                {
                    "date": current_date,
                    "analyte": canonical,
                    "value": value,
                    "unit_hint": rule.get("unit", ""),
                    "flag": flag,
                    "raw": cleaned[:180],
                }
            )
    return labs


def latest_labs(row: dict[str, str]) -> dict[str, Any]:
    labs = extract_labs(row)
    latest: dict[str, dict[str, Any]] = {}
    for item in labs:
        latest[item["analyte"]] = item
    alerts = [
        item
        for item in latest.values()
        if item.get("flag") in {"low", "high"}
    ]
    return {"latest": latest, "alerts": alerts, "parsed_count": len(labs)}


def treatment_summary(row: dict[str, str]) -> dict[str, Any]:
    meds = split_listish(row.get("ilac"))
    orders = split_listish(row.get("order ilaç"))
    procedures = split_listish(row.get("işlem adı"))
    chemo_terms = [item for item in meds + orders + procedures if "kemoterapi" in _fold(item)]
    drug_counter = Counter(clean_text(item).lower() for item in meds + orders if clean_text(item))
    systemic_keywords = ["paklitaksel", "carboplatin", "karboplatin", "dosetaksel", "capecitabine", "trastuzumab", "arimidex", "tamoksifen", "prednol"]
    systemic = []
    for item in meds + orders + procedures + split_listish(row.get("not")):
        folded = _fold(item)
        if any(keyword in folded for keyword in systemic_keywords):
            systemic.append(clean_text(item, 180))
    return {
        "ilac_sayisi": len(meds),
        "order_ilac_sayisi": len(orders),
        "en_sik_ilac_order": drug_counter.most_common(20),
        "kemoterapi_sinyalleri": chemo_terms[:20],
        "sistemik_tedavi_sinyalleri": list(dict.fromkeys(systemic))[:30],
    }


def metastasis_matches(query: str = "", client_id: str = "", limit: int = 20) -> list[dict[str, Any]]:
    q = clean_text(query)
    rows = [patient_lookup(client_id=client_id)] if client_id else all_records()
    rows = [row for row in rows if row]
    results = []
    terms = ["metastaz", "metastatik", " met ", " met?"]
    if q:
        terms.append(q)
    for row in rows:
        text = _combined_text(row)
        folded = _fold(text)
        if not any(_fold(term) in folded for term in terms):
            continue
        entities = extract_clinical_entities(row)
        results.append(
            {
                **patient_brief(row),
                "metastaz_sahaları": entities.get("metastaz_sahaları", []),
                "snippet": _snippet(text, q or "met"),
            }
        )
        if len(results) >= limit:
            break
    return results


def filter_cohort(tani: str = "", cinsiyet: str = "", metastaz: str = "", ilac: str = "", islem: str = "", limit: int = 20) -> list[dict[str, Any]]:
    filters = {
        "tani": _fold(tani),
        "cinsiyet": _fold(cinsiyet),
        "metastaz": _fold(metastaz),
        "ilac": _fold(ilac),
        "islem": _fold(islem),
    }
    results = []
    for row in all_records():
        haystack = _fold(_haystack(row))
        if filters["tani"] and filters["tani"] not in haystack:
            continue
        if filters["cinsiyet"] and filters["cinsiyet"] not in _fold(row.get("cinsiyet", "")):
            continue
        if filters["metastaz"]:
            entities = extract_clinical_entities(row)
            sites = _fold(" ".join(entities.get("metastaz_sahaları", [])))
            if filters["metastaz"] not in sites and "metastaz" not in haystack:
                continue
        if filters["ilac"] and filters["ilac"] not in _fold(row.get("ilac", "") + " " + row.get("order ilaç", "")):
            continue
        if filters["islem"] and filters["islem"] not in _fold(row.get("işlem adı", "") + " " + row.get("işlem tipi", "")):
            continue
        results.append(patient_brief(row))
        if len(results) >= limit:
            break
    return results


def cohort_stats() -> dict[str, Any]:
    records = all_records()
    departments = Counter()
    procedure_types = Counter()
    visit_types = Counter()
    procedures = Counter()
    drugs = Counter()
    death_count = 0
    metastatic_count = 0
    for row in records:
        death_count += bool(clean_text(row.get("ölüm tarihi")))
        metastatic_count += bool(extract_clinical_entities(row).get("metastaz_sahaları"))
        departments.update(split_listish(row.get("department")))
        procedure_types.update(split_listish(row.get("işlem tipi")))
        visit_types.update(split_listish(row.get("başvuru tipi")))
        procedures.update(split_listish(row.get("işlem adı")))
        drugs.update(split_listish(row.get("order ilaç")) + split_listish(row.get("ilac")))
    return {
        "record_count": len(records),
        "unique_client_id": len({row.get("client_id", "") for row in records if row.get("client_id")}),
        "death_date_present": death_count,
        "metastasis_signal_count": metastatic_count,
        "gender_counts": dict(Counter(clean_text(row.get("cinsiyet")) or "boş" for row in records)),
        "top_departments": departments.most_common(10),
        "top_procedure_types": procedure_types.most_common(10),
        "top_visit_types": visit_types.most_common(10),
        "top_procedures": procedures.most_common(15),
        "top_drugs": drugs.most_common(15),
    }


def assess_risks(row: dict[str, str]) -> list[dict[str, str]]:
    risks: list[dict[str, str]] = []
    if clean_text(row.get("ölüm tarihi")):
        risks.append({"level": "critical", "signal": "Kayıtta ölüm tarihi var.", "evidence": clean_text(row.get("ölüm tarihi"))})

    entities = extract_clinical_entities(row)
    if entities.get("metastaz_sahaları"):
        risks.append(
            {
                "level": "high",
                "signal": "Metastaz sinyali var.",
                "evidence": ", ".join(entities["metastaz_sahaları"]),
            }
        )

    procedure_type_text = _fold(row.get("işlem tipi", "") + " " + row.get("yatış tipi", "") + " " + row.get("başvuru tipi", ""))
    if "yoğun bakım" in procedure_type_text or "yogun bakim" in procedure_type_text:
        risks.append({"level": "high", "signal": "Yoğun bakım ilişkili kayıt var.", "evidence": "işlem/yatış tipi"})
    if "yatış" in procedure_type_text or "yatis" in procedure_type_text:
        risks.append({"level": "medium", "signal": "Yatış ilişkili kayıt var.", "evidence": "işlem/yatış tipi"})

    lab_alerts = latest_labs(row).get("alerts", [])
    for alert in lab_alerts[:8]:
        level = "medium"
        if alert["analyte"] in {"HGB", "WBC", "NEUT#", "PLT", "Kreatinin", "Potasyum", "Sodyum"}:
            level = "high"
        risks.append(
            {
                "level": level,
                "signal": f"{alert['analyte']} {alert['flag']}",
                "evidence": f"{alert['value']} {alert.get('unit_hint', '')} {alert.get('date', '')}".strip(),
            }
        )

    text = _fold(_combined_text(row))
    for keyword in ["şiddetli", "siddetli", "nefes darlığı", "nefes darligi", "ağrı", "agri"]:
        if keyword in text:
            risks.append({"level": "medium", "signal": f"Klinik metinde '{keyword}' sinyali var.", "evidence": _snippet(_combined_text(row), keyword, 120)})
            break
    return risks[:15]


def anonymize_text(text: str) -> str:
    cleaned = clean_text(text)

    def repl_client(match: re.Match[str]) -> str:
        raw = match.group(0)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]
        return f"HASTA_{digest}"

    cleaned = re.sub(r"\b(?:ADN|L1_ADN)_\d+\b", repl_client, cleaned)
    cleaned = re.sub(r"\b\d{11}\b", "TCKN_MASKELI", cleaned)
    cleaned = re.sub(r"\b(\d{4})-\d{2}-\d{2}\b", r"\1-XX-XX", cleaned)
    cleaned = re.sub(r"\b\d{1,2}[./]\d{1,2}[./](\d{4})\b", r"XX.XX.\1", cleaned)
    return cleaned


def safety_check(answer: str) -> dict[str, Any]:
    text = clean_text(answer)
    folded = _fold(text)
    warnings = []
    risky_phrases = [
        "kesin tanı",
        "kesin tani",
        "bu tedaviyi başla",
        "bu tedaviyi basla",
        "ilaç başla",
        "ilac basla",
        "dozu artır",
        "dozu artir",
        "doktor onayı gerekmez",
        "doktor onayi gerekmez",
    ]
    for phrase in risky_phrases:
        if phrase in folded:
            warnings.append(f"Kesin/uygulayıcı klinik ifade riski: '{phrase}'")
    if not any(token in folded for token in ["veriye göre", "kayda göre", "doktor", "klinik"]):
        warnings.append("Yanıtta veri kaynağı veya klinik doğrulama çerçevesi zayıf.")
    if re.search(r"\b(?:ADN|L1_ADN)_\d+\b", text):
        warnings.append("Yanıtta ham hasta kimliği var; anonimleştirme düşünülmeli.")
    return {
        "safe": not warnings,
        "warnings": warnings,
        "suggested_footer": "Bu çıktı klinik karar destek amaçlıdır; tanı/tedavi kararı sorumlu hekim tarafından doğrulanmalıdır.",
    }


def make_report(row: dict[str, str], report_format: str = "sbar") -> str:
    brief = patient_brief(row)
    entities = extract_clinical_entities(row)
    markers = extract_pathology_markers(row)
    labs = latest_labs(row)
    treatment = treatment_summary(row)
    risks = assess_risks(row)
    timeline = build_timeline(row, limit=12)

    lines = [
        f"# Klinik Özet - {brief.get('client_id')}",
        "",
        "## Hasta",
        f"- Cinsiyet: {brief.get('cinsiyet') or 'belirsiz'}",
        f"- Doğum tarihi: {brief.get('doğum tarihi') or 'belirsiz'}",
        f"- Bölüm örneği: {', '.join(brief.get('department_sample') or []) or 'belirsiz'}",
        f"- Ölüm tarihi: {brief.get('ölüm tarihi') or 'yok/boş'}",
        "",
        "## Klinik Durum",
        f"- Olası tanılar: {', '.join(entities.get('olasi_tanilar') or []) or 'çıkarılamadı'}",
        f"- Metastaz sahası sinyalleri: {', '.join(entities.get('metastaz_sahaları') or []) or 'yok/çıkarılamadı'}",
        f"- ECOG: {', '.join(entities.get('ecog') or []) or 'belirtilmemiş'}",
        f"- Boy/Kilo: {', '.join(entities.get('boy_cm') or []) or '?'} cm / {', '.join(entities.get('kilo_kg') or []) or '?'} kg",
        "",
        "## Patoloji / Marker",
        dumps(markers.get("markerlar") or {}),
        "",
        "## Tedavi / İşlem",
        f"- Kemoterapi sinyalleri: {', '.join(treatment.get('kemoterapi_sinyalleri') or []) or 'yok/çıkarılamadı'}",
        f"- Sistemik tedavi sinyalleri: {', '.join(treatment.get('sistemik_tedavi_sinyalleri')[:8]) or 'yok/çıkarılamadı'}",
        "",
        "## Lab Uyarıları",
    ]
    if labs.get("alerts"):
        for alert in labs["alerts"][:10]:
            lines.append(f"- {alert['analyte']}: {alert['value']} {alert.get('unit_hint', '')} ({alert['flag']}) {alert.get('date', '')}")
    else:
        lines.append("- Belirgin parse edilmiş lab uyarısı yok.")

    lines.extend(["", "## Risk Sinyalleri"])
    if risks:
        for risk in risks:
            lines.append(f"- [{risk['level']}] {risk['signal']} | Kanıt: {clean_text(risk.get('evidence'), 220)}")
    else:
        lines.append("- Otomatik risk sinyali saptanmadı.")

    lines.extend(["", "## Zaman Çizelgesi İlk Kayıtlar"])
    for event in timeline[:12]:
        lines.append(f"- {event.get('date') or 'tarih yok'} | {event.get('category')} | {clean_text(event.get('title'), 160)}")

    if report_format.lower() == "sbar":
        lines.extend(
            [
                "",
                "## SBAR",
                f"- Situation: {brief.get('client_id')} için onkoloji ağırlıklı kayıt özeti çıkarıldı.",
                f"- Background: {', '.join(entities.get('olasi_tanilar')[:3]) if entities.get('olasi_tanilar') else 'Tanı metinlerden net çıkarılamadı.'}",
                f"- Assessment: {', '.join(r['signal'] for r in risks[:4]) if risks else 'Otomatik yüksek risk sinyali sınırlı.'}",
                "- Recommendation: Bulgular sorumlu hekim tarafından klinik dosya ve güncel tetkiklerle doğrulanmalıdır.",
            ]
        )

    lines.append("")
    lines.append("Not: Bu çıktı klinik karar destek amaçlıdır; tanı/tedavi kararı sorumlu hekim tarafından doğrulanmalıdır.")
    return "\n".join(lines)
