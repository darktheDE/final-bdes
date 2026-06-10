import os
import sys
import json
import time
import string
import requests
from requests.exceptions import RequestException

# Paths (Windows Compatible)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(BASE_DIR, 'seed')
SEED_FILE = os.path.join(SEED_DIR, 'meals.json')

# TheMealDB API
API_SEARCH_LETTER = "https://www.themealdb.com/api/json/v1/1/search.php?f={}"
API_LIST_CATEGORIES = "https://www.themealdb.com/api/json/v1/1/list.php?c=list"
API_LIST_AREAS = "https://www.themealdb.com/api/json/v1/1/list.php?a=list"
API_LIST_INGREDIENTS = "https://www.themealdb.com/api/json/v1/1/list.php?i=list"

def parse_meal(raw_meal):
    """
    Parses a raw meal object from TheMealDB API into our required schema:
    {
      "_id": "meal_52772",
      "name": "Pho",
      "category": "Beef",
      "area": "Vietnamese",
      "instructions": "Simmer beef bones...",
      "ingredients": ["Beef", "Rice Noodles", ...]
    }
    """
    meal_id = raw_meal.get("idMeal")
    if not meal_id:
        return None
        
    ingredients = []
    # The API returns up to 20 ingredients as strIngredient1 to strIngredient20
    for i in range(1, 21):
        ing = raw_meal.get(f"strIngredient{i}")
        if ing and isinstance(ing, str) and ing.strip():
            ingredients.append(ing.strip())

    parsed = {
        "_id": f"meal_{meal_id}",
        "name": raw_meal.get("strMeal"),
        "category": raw_meal.get("strCategory"),
        "area": raw_meal.get("strArea"),
        "instructions": raw_meal.get("strInstructions"),
        "ingredients": ingredients
    }
    return parsed

def fetch_from_api():
    """Fetches all meals from the API by searching alphabet A-Z."""
    print("[*] Attempting to fetch meals from TheMealDB API...")
    all_meals = []
    
    # Iterate through a to z
    for letter in string.ascii_lowercase:
        url = API_SEARCH_LETTER.format(letter)
        print(f"    -> Fetching letter '{letter.upper()}'...", end=" ")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            meals = data.get("meals")
            if meals:
                for raw in meals:
                    parsed = parse_meal(raw)
                    if parsed:
                        all_meals.append(parsed)
                print(f"Found {len(meals)} meals.")
            else:
                print("No meals.")
                
            # Be polite to the API
            time.sleep(0.5)
            
        except RequestException as e:
            print(f"FAILED! Error: {e}")
            raise RuntimeError("API request failed.") from e
            
    # Fetch lists
    print("\n[*] Fetching Categories...")
    try:
        res = requests.get(API_LIST_CATEGORIES, timeout=10)
        res.raise_for_status()
        categories = res.json().get('meals', [])
        print(f"    -> Found {len(categories)} categories.")
    except Exception as e:
        print(f"FAILED to fetch categories: {e}")
        categories = []
        
    print("[*] Fetching Areas...")
    try:
        res = requests.get(API_LIST_AREAS, timeout=10)
        res.raise_for_status()
        areas = res.json().get('meals', [])
        print(f"    -> Found {len(areas)} areas.")
    except Exception as e:
        print(f"FAILED to fetch areas: {e}")
        areas = []
        
    print("[*] Fetching Ingredients...")
    try:
        res = requests.get(API_LIST_INGREDIENTS, timeout=10)
        res.raise_for_status()
        ingredients = res.json().get('meals', [])
        print(f"    -> Found {len(ingredients)} ingredients.")
    except Exception as e:
        print(f"FAILED to fetch ingredients: {e}")
        ingredients = []
            
    return all_meals, categories, areas, ingredients

def save_to_seed(data, filename="meals.json"):
    """Saves the fetched data to the seed file for offline fallback."""
    os.makedirs(SEED_DIR, exist_ok=True)
    filepath = os.path.join(SEED_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"[*] Successfully saved {len(data)} items to seed file: {filepath}")

def load_from_seed():
    """Loads data from the local seed files."""
    print("[*] Attempting to load meals from local seed fallback...")
    if not os.path.exists(SEED_FILE):
        print(f"[!] Seed file not found at {SEED_FILE}.")
        return None, None, None, None
        
    try:
        with open(SEED_FILE, 'r', encoding='utf-8') as f:
            meals_data = json.load(f)
        print(f"[*] Successfully loaded {len(meals_data)} meals from seed fallback.")
        
        categories_data, areas_data, ingredients_data = [], [], []
        
        cat_file = os.path.join(SEED_DIR, 'categories.json')
        if os.path.exists(cat_file):
            with open(cat_file, 'r', encoding='utf-8') as f: categories_data = json.load(f)
            
        area_file = os.path.join(SEED_DIR, 'areas.json')
        if os.path.exists(area_file):
            with open(area_file, 'r', encoding='utf-8') as f: areas_data = json.load(f)
            
        ing_file = os.path.join(SEED_DIR, 'ingredients.json')
        if os.path.exists(ing_file):
            with open(ing_file, 'r', encoding='utf-8') as f: ingredients_data = json.load(f)
            
        return meals_data, categories_data, areas_data, ingredients_data
    except Exception as e:
        print(f"[!] Failed to read seed file: {e}")
        return None, None, None, None

def main():
    print("=== TheMealDB Ingestion Script ===")
    meals_data, categories, areas, ingredients = None, None, None, None
    
    try:
        # 1. Try to fetch from API
        meals_data, categories, areas, ingredients = fetch_from_api()
        # 2. Save to seed as backup
        if meals_data:
            save_to_seed(meals_data, "meals.json")
        if categories: save_to_seed(categories, "categories.json")
        if areas: save_to_seed(areas, "areas.json")
        if ingredients: save_to_seed(ingredients, "ingredients.json")
            
    except Exception as e:
        print(f"\n[!] Network error encountered: {e}")
        print("[!] Engaging Offline Fallback Mechanism...\n")
        
        # 3. Offline Fallback
        meals_data, categories, areas, ingredients = load_from_seed()
        
    if not meals_data:
        print("[-] Critical Failure: Could not retrieve meal data from API or Seed.")
        sys.exit(1)
        
    print(f"\n[+] Ingestion Complete.")
    print(f"    Total Meals: {len(meals_data)}")
    if categories: print(f"    Total Categories: {len(categories)}")
    if areas: print(f"    Total Areas: {len(areas)}")
    if ingredients: print(f"    Total Ingredients: {len(ingredients)}")
    
    # Optional: Save to a final output location if needed, 
    # but for now seed/meals.json acts as the master record.

if __name__ == "__main__":
    main()
