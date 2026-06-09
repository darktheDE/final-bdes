# Phase 4: TheMealDB API Ingestion (Task 1.2)

## 1. Main Goal
Our goal was to extract an alternative dataset consisting of meal recipes, ingredients, and categories from TheMealDB's open API to use for our Big Data processing pipeline.

## 2. What Were We Doing to Achieve That Goal?
We created a standalone, pure-Python extraction script (`src/crawler/fetch_mealdb.py`) designed to interface with TheMealDB's JSON API endpoints. We needed to map the raw API structure (which separates ingredients into 20 distinct `strIngredientX` fields) into a clean, unified schema that works natively with our upcoming MongoDB ingestion.

## 3. What Endpoints Were Targeted?
To minimize HTTP requests while maximizing data retrieval on the free tier, we strategically used the following endpoints:
- `search.php?f={letter}`: By iterating through the alphabet (A-Z), we retrieved the complete metadata (category, area, instructions, and ingredients) for all ~300+ free-tier meals in exactly 26 requests.
- `list.php?c=list`: Extracted the complete list of culinary categories.
- `list.php?a=list`: Extracted the complete list of regional areas.
- `list.php?i=list`: Extracted the raw ingredient metadata database.

## 4. Implementation Details & Schema Normalization
We implemented the `parse_meal()` function to handle the strict transformation of the dataset:
- We dynamically looped over `strIngredient1` through `strIngredient20` and collapsed them into a clean `ingredients: [...]` array, stripping out empty strings and nulls.
- We mapped `idMeal` to our internal `_id` standard (e.g., `"meal_52772"`).

## 5. Offline Fallback Architecture
We implemented a robust `try-except` failover mechanism. If the network drops or the API is unavailable during a run, the script automatically triggers its fallback routine. It looks for the previously saved local copies inside `src/crawler/seed/` (`meals.json`, `categories.json`, `areas.json`, `ingredients.json`) and loads them into memory, ensuring the broader data pipeline never crashes due to external API failures.

## 6. The Result We Got
The script autonomously executed and successfully built four master seed files. It flawlessly parsed 666 unique meals, creating a structured JSON database that perfectly matches our strict Big Data schema and is completely ready for MongoDB insertion.
