import re
import unicodedata


UNKNOWN_LOCATION_VALUES = {"", "unknown", "null", "none", "n/a", "nan"}

_AREA_ALIASES = {
    "an khanh": "An Khánh",
    "ben nghe": "Bến Nghé",
    "ben thanh": "Bến Thành",
    "binh tan": "Bình Tân",
    "binh thanh": "Bình Thạnh",
    "can gio": "Cần Giờ",
    "cu chi": "Củ Chi",
    "go vap": "Gò Vấp",
    "hoc mon": "Hóc Môn",
    "nha be": "Nhà Bè",
    "pham ngu lao": "Phạm Ngũ Lão",
    "phu my hung": "Phú Mỹ Hưng",
    "phu nhuan": "Phú Nhuận",
    "sai gon": "Sài Gòn",
    "saigon": "Sài Gòn",
    "tan binh": "Tân Bình",
    "tan dinh": "Tân Định",
    "tan phong": "Tân Phong",
    "tan phu": "Tân Phú",
    "thao dien": "Thảo Điền",
    "thu duc": "Thủ Đức",
    "vo thi sau": "Võ Thị Sáu",
    "xuan hoa": "Xuân Hòa",
}

_HCMC_PATTERN = re.compile(
    r"\b(ho\s+chi\s+minh\s+city|hcmc|tp\.?\s*hcm|tphcm|sai\s*gon|saigon)\b",
    re.IGNORECASE,
)

_DISTRICT_NUMBER_PATTERNS = (
    re.compile(r"\b(?:Qu[aậ]n|Q\.|District|Dist\.|Dis\.?)\s*(\d{1,2})\b", re.IGNORECASE),
)

_DISTRICT_NAME_PATTERNS = (
    re.compile(
        r"\b(?:Qu[aậ]n|Q\.)\s*([A-Za-zÀ-ỹ][A-Za-zÀ-ỹ0-9\s-]{0,40}?)(?=,|$|\b(?:Vietnam|Ho Chi Minh|HCMC|Tp\.?\s*Hcm)\b)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:District|Dist\.|Dis\.?)\s*([A-Za-zÀ-ỹ][A-Za-zÀ-ỹ0-9\s-]{0,40}?)(?=,|$|\b(?:Vietnam|Ho Chi Minh|HCMC|Tp\.?\s*Hcm)\b)",
        re.IGNORECASE,
    ),
    re.compile(r"\b([A-Za-zÀ-ỹ][A-Za-zÀ-ỹ\s-]{0,40}?)\s+District\b", re.IGNORECASE),
)

_WARD_PATTERNS = (
    re.compile(
        r"\b(?:Phường|P\.|W\.)\s*([A-Za-zÀ-ỹ0-9][A-Za-zÀ-ỹ0-9\s-]{0,40}?)(?=,|$|\b(?:Vietnam|Ho Chi Minh|HCMC|Tp\.?\s*Hcm|District|Dis\.?|Qu[aậ]n|Q\.)\b)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b([A-Za-zÀ-ỹ][A-Za-zÀ-ỹ0-9\s-]{0,40}?)\s+Ward\b(?=,|$|\b(?:Vietnam|Ho Chi Minh|HCMC|Tp\.?\s*Hcm|District|Dis\.?|Qu[aậ]n|Q\.)\b)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bWard\s+([A-Za-zÀ-ỹ0-9][A-Za-zÀ-ỹ0-9\s-]{0,40}?)(?=,|$|\b(?:Vietnam|Ho Chi Minh|HCMC|Tp\.?\s*Hcm|District|Dis\.?|Qu[aậ]n|Q\.)\b)",
        re.IGNORECASE,
    ),
)


def clean_location_text(value) -> str:
    """Collapse whitespace and normalize empty-ish location values."""
    text = str(value or "").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip().strip(",").strip()
    return "" if text.lower() in UNKNOWN_LOCATION_VALUES else text


def is_unknown_location(value) -> bool:
    """Return True for empty or placeholder location values."""
    return clean_location_text(value).lower() in UNKNOWN_LOCATION_VALUES


def normalize_city(*values: str) -> str:
    """Normalize city labels and fall back to any location field containing the city."""
    for raw_value in values:
        text = clean_location_text(raw_value)
        if not text:
            continue
        text = re.sub(r"\b\d{4,6}\b", "", text)
        text = re.sub(r"\bVietnam\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text).strip().strip(",").strip()
        if not text:
            continue
        if _HCMC_PATTERN.search(_strip_accents(text)):
            return "Ho Chi Minh City"
        return text
    return "Unknown"


def extract_admin_area(*values: str) -> str:
    """Extract a normalized district/ward from noisy TripAdvisor location strings."""
    sources = [clean_location_text(value) for value in values if clean_location_text(value)]
    if not sources:
        return "Unknown"

    for source in sources:
        numeric_district = _match_first(source, _DISTRICT_NUMBER_PATTERNS)
        if numeric_district:
            return f"Quận {numeric_district}"

    for source in sources:
        named_district = _match_first(source, _DISTRICT_NAME_PATTERNS)
        if named_district:
            return f"Quận {_normalize_area_name(named_district)}"

    for source in sources:
        ward_name = _match_first(source, _WARD_PATTERNS)
        if ward_name:
            return f"Phường {_normalize_area_name(ward_name)}"

    return "Unknown"


def _match_first(source: str, patterns) -> str | None:
    """Return the first normalized regex capture from a set of patterns."""
    for pattern in patterns:
        match = pattern.search(source)
        if match:
            return _trim_noise(match.group(1))
    return None


def _trim_noise(value: str) -> str:
    """Remove street/building prefixes that leak into admin-area captures."""
    text = clean_location_text(value)
    if not text:
        return ""

    text = re.split(
        r"(?i)\b(?:street|st\.|road|rd\.|avenue|ave\.|boulevard|blvd|lane|hotel|building|tower|floor|level|port|block|đường|đ\.)\b",
        text,
    )[-1]
    text = re.sub(r"^[\d\-/]+", "", text).strip(" -.,")
    text = re.sub(r"\b(?:ward|district)\b$", "", text, flags=re.IGNORECASE).strip(" -.,")
    return clean_location_text(text)


def _normalize_area_name(value: str) -> str:
    """Canonicalize area names so English/Vietnamese variants collapse to one label."""
    text = _trim_noise(value)
    if not text:
        return ""

    ascii_key = _strip_accents(text).lower()
    ascii_key = re.sub(r"[^a-z0-9\s-]", " ", ascii_key)
    ascii_key = re.sub(r"\s+", " ", ascii_key).strip()

    if ascii_key in _AREA_ALIASES:
        return _AREA_ALIASES[ascii_key]
    if re.fullmatch(r"\d{1,2}", ascii_key):
        return ascii_key

    return " ".join(part[:1].upper() + part[1:].lower() for part in text.split())


def _strip_accents(value: str) -> str:
    """Return an ASCII-ish string for regex matching and alias lookup."""
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
