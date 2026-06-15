import re
import unicodedata


_AREA_ALIASES = {
    "an khanh": "An Khanh",
    "ben nghe": "Ben Nghe",
    "ben thanh": "Ben Thanh",
    "binh thanh": "Binh Thanh",
    "go vap": "Go Vap",
    "pham ngu lao": "Pham Ngu Lao",
    "phu nhuan": "Phu Nhuan",
    "sai gon": "Sai Gon",
    "saigon": "Sai Gon",
    "tan binh": "Tan Binh",
    "tan dinh": "Tan Dinh",
    "tan phong": "Tan Phong",
    "thao dien": "Thao Dien",
    "thu duc": "Thu Duc",
    "vo thi sau": "Vo Thi Sau",
    "xuan hoa": "Xuan Hoa",
}


def clean_location_text(value) -> str:
    """Collapse whitespace and normalize placeholder values."""
    text = str(value or "").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip().strip(",").strip()
    return "" if text.lower() in {"", "unknown", "null", "none", "n/a", "nan"} else text


def strip_accents(value: str) -> str:
    """Return an ASCII-like string for easier matching."""
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def trim_noise(value: str) -> str:
    """Drop obvious street/building suffixes from extracted areas."""
    text = clean_location_text(value)
    if not text:
        return ""

    text = re.split(
        r"(?i)\b(?:street|st\.|road|rd\.|avenue|ave\.|boulevard|blvd|lane|hotel|building|tower|floor|level|port|block|duong|d\.)\b",
        text,
    )[-1]
    text = re.sub(r"^[\d\-/]+", "", text).strip(" -.,")
    text = re.sub(r"\b(?:ward|district)\b$", "", text, flags=re.IGNORECASE).strip(" -.,")
    return clean_location_text(text)


def normalize_area_name(value: str) -> str:
    """Canonicalize area names so variants group together."""
    text = trim_noise(value)
    if not text:
        return ""

    ascii_key = strip_accents(text).lower()
    ascii_key = re.sub(r"[^a-z0-9\s-]", " ", ascii_key)
    ascii_key = re.sub(r"\s+", " ", ascii_key).strip()

    if ascii_key in _AREA_ALIASES:
        return _AREA_ALIASES[ascii_key]
    if re.fullmatch(r"\d{1,2}", ascii_key):
        return ascii_key

    return " ".join(part[:1].upper() + part[1:].lower() for part in ascii_key.split())


def match_first(source: str, patterns) -> str | None:
    """Return the first non-empty capture from candidate patterns."""
    for pattern in patterns:
        match = pattern.search(source)
        if match:
            return trim_noise(match.group(1))
    return None


def extract_admin_area(*location_parts: str) -> str:
    """Extract a stable district/ward label from raw location fields."""
    sources = [clean_location_text(value) for value in location_parts if clean_location_text(value)]
    if not sources:
        return "Unknown"

    district_number_patterns = (
        re.compile(r"\b(?:Quan|Q\.|District|Dist\.|Dis\.?)\s*(\d{1,2})\b", re.IGNORECASE),
    )
    district_name_patterns = (
        re.compile(
            r"\b(?:Quan|Q\.)\s*([A-Za-z][A-Za-z0-9\s-]{0,40}?)(?=,|$|\b(?:Vietnam|Ho Chi Minh|HCMC|Tp\.?\s*Hcm)\b)",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:District|Dist\.|Dis\.?)\s*([A-Za-z][A-Za-z0-9\s-]{0,40}?)(?=,|$|\b(?:Vietnam|Ho Chi Minh|HCMC|Tp\.?\s*Hcm)\b)",
            re.IGNORECASE,
        ),
        re.compile(r"\b([A-Za-z][A-Za-z\s-]{0,40}?)\s+District\b", re.IGNORECASE),
    )
    ward_patterns = (
        re.compile(
            r"\b(?:Phuong|P\.|W\.)\s*([A-Za-z0-9][A-Za-z0-9\s-]{0,40}?)(?=,|$|\b(?:Vietnam|Ho Chi Minh|HCMC|Tp\.?\s*Hcm|District|Dis\.?|Quan|Q\.)\b)",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b([A-Za-z][A-Za-z0-9\s-]{0,40}?)\s+Ward\b(?=,|$|\b(?:Vietnam|Ho Chi Minh|HCMC|Tp\.?\s*Hcm|District|Dis\.?|Quan|Q\.)\b)",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bWard\s+([A-Za-z0-9][A-Za-z0-9\s-]{0,40}?)(?=,|$|\b(?:Vietnam|Ho Chi Minh|HCMC|Tp\.?\s*Hcm|District|Dis\.?|Quan|Q\.)\b)",
            re.IGNORECASE,
        ),
    )

    for source in sources:
        numeric_district = match_first(strip_accents(source), district_number_patterns)
        if numeric_district:
            return f"Quan {numeric_district}"

    for source in sources:
        named_district = match_first(strip_accents(source), district_name_patterns)
        if named_district:
            return f"Quan {normalize_area_name(named_district)}"

    for source in sources:
        ward_name = match_first(strip_accents(source), ward_patterns)
        if ward_name:
            return f"Phuong {normalize_area_name(ward_name)}"

    return "Unknown"
