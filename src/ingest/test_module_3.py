import sys
import os

# Add src to sys.path to import modules correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.import_tripadvisor import clean_restaurant
import json

def run_tests():
    print("=== Testing Module 3: Data Normalization in import_tripadvisor.py ===")
    
    sample_restaurant = {
        "_id": "https://www.tripadvisor.com/Restaurant_Review-g293925-d33215720-Reviews-Bun_Ch_Ha_Thanh_by_Hanoi_Corner-Ho_Chi_Minh_City.html",
        "name": "Bún Chả Hà Thành by Hanoi Corner",
        "rating": "4.5",
        "review_count": "(112)",
        "address": "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1, Ho Chi Minh City 70000 Vietnam",
        "district": "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1",
        "city": "Ho Chi Minh City 70000 Vietnam",
        "reviews": [
            {
                "user": "Chloe C",
                "rating": "5 of 5 bubbles",
                "comment": "Excellent food with friendly service by Ly."
            },
            {
                "user": "Fearless",
                "rating": "4 of 5 bubbles",
                "comment": ""
            }
        ]
    }
    
    print("\n[+] Raw Data:")
    print(json.dumps(sample_restaurant, indent=2, ensure_ascii=False))
    
    # Process
    cleaned = clean_restaurant(sample_restaurant.copy())
    
    print("\n[+] Cleaned Data:")
    print(json.dumps(cleaned, indent=2, ensure_ascii=False))
    
    # Assertions
    errors = []
    
    # 1. ID Deduplication
    if cleaned.get('_id') != 'rest_d33215720':
        errors.append(f"Failed ID shorting: Expected 'rest_d33215720', got {cleaned.get('_id')}")
        
    # 2. Rating extraction
    if cleaned.get('rating') != 4.5:
        errors.append(f"Failed rating parse: Expected 4.5, got {cleaned.get('rating')}")
        
    # 3. Review Count parse
    if cleaned.get('review_count') != 112:
        errors.append(f"Failed review_count parse: Expected 112, got {cleaned.get('review_count')}")
        
    # 4. District parsed
    if cleaned.get('district_parsed') != 'Quận 1':
        errors.append(f"Failed district parsing: Expected 'Quận 1', got {cleaned.get('district_parsed')}")
        
    # 5. City normalized
    if cleaned.get('city') != 'Ho Chi Minh City':
        errors.append(f"Failed city normalization: Expected 'Ho Chi Minh City', got {cleaned.get('city')}")
        
    # 6. Reviews rating
    if cleaned['reviews'][0]['rating'] != 5.0:
        errors.append(f"Failed review rating parse: Expected 5.0, got {cleaned['reviews'][0]['rating']}")
        
    if len(errors) == 0:
        print("\n[PASS] All clean_restaurant normalizations worked as expected.")
        return True
    else:
        print("\n[FAIL] Errors encountered:")
        for err in errors:
            print(f"  - {err}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
