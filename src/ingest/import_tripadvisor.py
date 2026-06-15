import json
import os
import re
import pymongo
from init_db import _parse_review_count, _extract_district, _normalize_city, _parse_review_rating, _make_short_id

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "sentiment_db"

# Đường dẫn tới dataset mới (MongoDB export từ sentiment_db.restaurants)
# Format: JSON array [{...}, {...}]  (không phải JSONL)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_PATH = os.path.join(BASE_DIR, 'data', 'sentiment_db.restaurants.json')


def extract_float(value):
    """Extract a float from various input types."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r'(\d+(\.\d+)?)', str(value))
    if match:
        return float(match.group(1))
    return None


def _smart_district_parsed(district_raw: str) -> str:
    """Resolve district_parsed từ field 'district' của dataset mới.

    Dataset sentiment_db.restaurants.json đã có field 'district' sạch hơn
    data crawl thô. Có hai dạng:
      1. Đã là tên phường/quận: "Phường Tân Định", "Quận 1"  → dùng trực tiếp.
      2. Vẫn là đường phố đầy đủ: "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1"
         → dùng _extract_district() để extract.

    Heuristic: nếu chuỗi bắt đầu bằng từ khoá quận/phường/huyện → dùng trực tiếp.
    """
    if not district_raw or str(district_raw).strip().lower() in ('', 'null', 'none', 'unknown'):
        return 'Unknown'
    s = str(district_raw).strip()
    # Nếu bắt đầu bằng prefix hành chính → đây đã là tên quận/phường sạch
    if re.match(r'(?i)^(Phường|Quận|Huyện|Thị xã|Thành phố|Q\.)\s+', s):
        return s
    # Nếu không, thử extract với regex từ chuỗi địa chỉ
    return _extract_district(s)


def clean_restaurant(rest):
    """Normalize và clean một bản ghi restaurant từ dataset mới."""
    raw_id = rest.get('_id', rest.get('url', ''))
    rest['_id'] = _make_short_id(str(raw_id)) if raw_id else ''

    rest['rating'] = extract_float(rest.get('rating'))
    # review_count trong dataset mới đã là int, _parse_review_count xử lý cả hai dạng
    rest['review_count'] = _parse_review_count(rest.get('review_count'))

    district_raw = rest.get('district', '') or ''
    rest['district_parsed'] = _smart_district_parsed(district_raw)

    city_raw = rest.get('city', '') or ''
    rest['city'] = _normalize_city(city_raw)

    cleaned_reviews = []
    for r in rest.get('reviews', []):
        # rating trong dataset mới đã là int (không phải "5 of 5 bubbles")
        # _parse_review_rating xử lý cả hai dạng
        r_rating = _parse_review_rating(r.get('rating'))
        r_comment = str(r.get('comment', '')).strip()
        r_user = str(r.get('user', '')).strip()

        if not r_user and not r_comment and r_rating is None:
            continue

        cleaned_reviews.append({
            "user": r_user if r_user else "Anonymous",
            "rating": r_rating,
            "comment": r_comment if r_comment else None
        })

    rest['reviews'] = cleaned_reviews
    return rest


def main():
    print(f"[*] Reading TripAdvisor data from {JSON_PATH}...")
    if not os.path.exists(JSON_PATH):
        print(f"[!] File not found: {JSON_PATH}")
        print(f"    Expected: data/sentiment_db.restaurants.json")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("[!] JSON file must be an array [...] at the top level.")
        return

    print(f"[*] Loaded {len(data)} restaurants from JSON.")
    print(f"[*] Connecting to MongoDB at {MONGO_URI}...")
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    coll = db['restaurants']

    # Xóa collection cũ trước khi import để tránh accumulation
    existing = coll.count_documents({})
    if existing > 0:
        print(f"[*] Dropping existing {existing} documents in collection 'restaurants'...")
        coll.drop()

    print(f"[*] Ingesting {len(data)} restaurants...")
    upsert_count = 0
    skip_count = 0
    for r in data:
        cleaned = clean_restaurant(r)
        if not cleaned['_id']:
            skip_count += 1
            continue

        coll.update_one(
            {'_id': cleaned['_id']},
            {'$set': cleaned},
            upsert=True
        )
        upsert_count += 1

    print(f"[+] Successfully upserted {upsert_count} restaurants into MongoDB '{DB_NAME}.restaurants'.")
    if skip_count > 0:
        print(f"[!] Skipped {skip_count} records with missing/invalid _id.")

    # Verify
    total = coll.count_documents({})
    print(f"[+] MongoDB collection now has {total} documents.")


if __name__ == "__main__":
    main()
