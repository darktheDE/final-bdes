# Cycle 1 Guide: Data Ingestion Workflow

This guide explains how Cycle 1 (Data Crawling & Ingestion) operates, from environment setup to final database ingestion. It covers the logic, condition requirements, and data flow of our two main sources: TripAdvisor and TheMealDB.

## 1. Environment & Setup

Before running the ingestion scripts, the environment must be correctly configured:
- **Python**: A virtual environment (`.venv`) with all required packages (`requirements.txt`) including `Scrapy`, `scrapy-playwright`, `playwright-stealth`, and `pymongo`.
- **Database**: MongoDB Server must be running locally on port `27017` with no authentication required for the default connection. The database name targeted is `sentiment_db`.

## 2. TripAdvisor Crawler (Scrapy + Playwright)

### How it Works
1. **Spider Initiation**: The spider starts at the main Ho Chi Minh City restaurant listing URL.
2. **JavaScript Execution**: It uses `scrapy-playwright` headless browsers to wait for specific DOM elements (`#lithium-root`) to render, effectively bypassing Cloudflare CAPTCHAs and loading dynamic content.
3. **Pagination & Extraction**: The crawler extracts URLs for the "Next Page" of restaurants and the individual restaurant review pages, spawning new Playwright requests for each.
4. **Data Scraping**: On a restaurant page, it scrapes the restaurant name, rating, address, and up to 75 reviews per restaurant (extracting user, rating, and comment).

### Data Flow (Direct to MongoDB)
Instead of writing to a JSON file, we implemented an automated Item Pipeline (`TripadvisorMongoPipeline`):
1. The spider yields a raw item.
2. The pipeline intercepts the item and performs on-the-fly cleaning (using RegEx to cast ratings to floats and review counts to ints).
3. The pipeline connects to MongoDB and executes an `update_one` with `upsert=True` using the URL as the `_id`. This guarantees no duplicates.

## 3. TheMealDB Fetcher (REST API)

### How it Works
1. **Alphabetical Iteration**: The `fetch_mealdb.py` script queries the API 26 times, fetching meals starting with every letter from A to Z.
2. **List Extraction**: It also fetches the master lists of Categories, Areas, and Ingredients.
3. **Offline Fallback**: If the network request fails, the script engages an offline fallback mechanism, loading historical data from `src/crawler/seed/`.

### Data Flow (Direct to MongoDB)
1. After parsing the JSON response from the API, the script strips null values and normalizes the schema.
2. A built-in `clean_meal()` function ensures structural integrity.
3. The script connects to MongoDB and upserts all 666+ meals directly into the `meals` collection.
4. Concurrently, the raw data is saved into the `seed/` directory for future offline redundancy.

## 4. Conditions to Run Scripts

- **TripAdvisor**: Run `scrapy crawl tripadvisor` from inside the `src/crawler/tripadvisor_job` directory.
  - *Note*: If you need to pause/resume, use `-s JOBDIR=crawls/run1`.
- **TheMealDB**: Run `python fetch_mealdb.py` from inside the `src/crawler` directory.

Both scripts natively interface with MongoDB and require no intermediate cleanup steps.
