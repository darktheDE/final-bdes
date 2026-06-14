import json
import os
import re
import pymongo
from init_db import _parse_review_count, _extract_district, _normalize_city, _parse_review_rating, _make_short_id

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "sentiment_db"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'crawler', 'tripadvisor_job', 'full_output.json')

def extract_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r'(\d+(\.\d+)?)', str(value))
    if match:
        return float(match.group(1))
    return None

def clean_restaurant(rest):
    raw_id = rest.get('_id', rest.get('url', ''))
    rest['_id'] = _make_short_id(str(raw_id)) if raw_id else ''

    rest['rating'] = extract_float(rest.get('rating'))
    rest['review_count'] = _parse_review_count(rest.get('review_count'))
    
    district_raw = rest.get('district', '') or ''
    rest['district_parsed'] = _extract_district(district_raw)
    
    city_raw = rest.get('city', '') or ''
    rest['city'] = _normalize_city(city_raw)
        
    cleaned_reviews = []
    for r in rest.get('reviews', []):
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
        return
        
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"[*] Connecting to MongoDB at {MONGO_URI}...")
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    coll = db['restaurants']
    
    print(f"[*] Ingesting {len(data)} restaurants...")
    upsert_count = 0
    for r in data:
        cleaned = clean_restaurant(r)
        if not cleaned['_id']:
            continue
            
        coll.update_one(
            {'_id': cleaned['_id']},
            {'$set': cleaned},
            upsert=True
        )
        upsert_count += 1
        
    print(f"[+] Successfully upserted {upsert_count} restaurants into MongoDB.")

if __name__ == "__main__":
    main()
