import json
import os
import re
import pymongo
from pymongo.errors import DuplicateKeyError

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRAWLER_DIR = os.path.join(BASE_DIR, 'crawler')
RESTAURANTS_JSON = os.path.join(CRAWLER_DIR, 'tripadvisor_job', 'full_output.json')
MEALS_JSON = os.path.join(CRAWLER_DIR, 'seed', 'meals.json')

# Database configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "sentiment_db"

def extract_float(value):
    """Extracts a float from a string like '4.5 of 5 bubbles' or returns float natively."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    
    # Extract digits and optional decimal
    match = re.search(r'(\d+(\.\d+)?)', str(value))
    if match:
        return float(match.group(1))
    return None

def extract_int(value):
    """Extracts an integer from strings like '(1,500 reviews)' or '(128)'."""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    
    # Remove non-digits
    digits = re.sub(r'\D', '', str(value))
    if digits:
        return int(digits)
    return 0

def clean_restaurant(rest):
    """Cleans a single restaurant document."""
    # Clean main rating
    rest['rating'] = extract_float(rest.get('rating'))
    
    # Clean review count
    rest['review_count'] = extract_int(rest.get('review_count'))
    
    # Default location fields if missing
    if not rest.get('district'):
        rest['district'] = "Unknown"
    if not rest.get('city'):
        rest['city'] = "Unknown"
    
    # Clean reviews
    cleaned_reviews = []
    for r in rest.get('reviews', []):
        r_rating = extract_float(r.get('rating'))
        r_comment = str(r.get('comment', '')).strip()
        r_user = str(r.get('user', '')).strip()
        
        # Only keep reviews that have at least a user or a comment or a rating
        if not r_user and not r_comment and r_rating is None:
            continue
            
        cleaned_reviews.append({
            "user": r_user if r_user else "Anonymous",
            "rating": r_rating,
            "comment": r_comment if r_comment else None
        })
        
    rest['reviews'] = cleaned_reviews
    return rest

def clean_meal(meal):
    """Cleans a single meal document."""
    if not meal.get('area'):
        meal['area'] = "Unknown"
    if not meal.get('category'):
        meal['category'] = "Unknown"
        
    # Ensure ingredients list is clean
    raw_ingredients = meal.get('ingredients', [])
    clean_ingredients = [str(i).strip() for i in raw_ingredients if i and str(i).strip()]
    meal['ingredients'] = clean_ingredients
    
    return meal

def populate_mongodb():
    print(f"Connecting to MongoDB at {MONGO_URI}...")
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Check connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
    except Exception as e:
        print(f"FAILED to connect to MongoDB: {e}")
        print("Please ensure MongoDB is running on localhost:27017.")
        return

    db = client[DB_NAME]
    rest_coll = db['restaurants']
    meals_coll = db['meals']

    # 1. Process Restaurants
    print(f"\nProcessing restaurants from: {RESTAURANTS_JSON}")
    if os.path.exists(RESTAURANTS_JSON):
        try:
            with open(RESTAURANTS_JSON, 'r', encoding='utf-8') as f:
                restaurants = json.load(f)
            
            inserted_count = 0
            skipped_count = 0
            
            for raw_rest in restaurants:
                cleaned = clean_restaurant(raw_rest)
                
                try:
                    rest_coll.insert_one(cleaned)
                    inserted_count += 1
                except DuplicateKeyError:
                    skipped_count += 1
                    
            print(f"Restaurants -> Inserted: {inserted_count} | Ignored (Duplicates): {skipped_count}")
        except Exception as e:
            print(f"Error processing restaurants: {e}")
    else:
        print(f"File not found: {RESTAURANTS_JSON}")

    # 2. Process Meals
    print(f"\nProcessing meals from: {MEALS_JSON}")
    if os.path.exists(MEALS_JSON):
        try:
            with open(MEALS_JSON, 'r', encoding='utf-8') as f:
                meals = json.load(f)
            
            inserted_count = 0
            skipped_count = 0
            
            for raw_meal in meals:
                cleaned = clean_meal(raw_meal)
                
                try:
                    meals_coll.insert_one(cleaned)
                    inserted_count += 1
                except DuplicateKeyError:
                    skipped_count += 1
                    
            print(f"Meals -> Inserted: {inserted_count} | Ignored (Duplicates): {skipped_count}")
        except Exception as e:
            print(f"Error processing meals: {e}")
    else:
        print(f"File not found: {MEALS_JSON}")

    print("\nDatabase Schema & Data Cleaning complete.")

if __name__ == "__main__":
    populate_mongodb()
