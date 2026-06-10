# Phase 5: Database Schema & Data Cleaning (Task 1.3)

## 1. Main Goal
Our goal was to parse the raw unstructured data we crawled (from TripAdvisor and TheMealDB), clean it, and insert it into a robust local database suitable for our Big Data processing pipeline. 

## 2. Setting Up the Database
Before running any ingestion scripts, the database runtime itself needed to be securely installed and started locally. This was achieved natively on Windows via `winget` (Windows Package Manager).

**Installation Steps Executed:**
We opened `cmd` as Administrator and ran:
```batch
winget install --id MongoDB.Compass.Full -e
winget install --id MongoDB.Server -e
```
This automatically downloaded and configured the MongoDB Server runtime and the Compass GUI.

**Database Connection:**
Once installed, the server automatically boots on the standard `mongodb://localhost:27017/` port. We connected to this URI to create our project database called `sentiment_db`.

## 3. What Were We Doing to Achieve That Goal?
We created `src/ingest/clean_and_populate.py`. This script performs an automated ETL (Extract, Transform, Load) pipeline:
1. **Extract**: It reads `full_output.json` (restaurants) and `seed/meals.json` (recipes).
2. **Transform**: It normalizes strings, types, and schema attributes.
3. **Load**: It securely inserts the data into the MongoDB collections (`restaurants` and `meals`).

## 4. What Problems Did We Face & How Did We Solve Them?

### Problem 1: Dirty Ratings & Counts
Raw HTML scraping often yields dirty strings instead of clean integers and floats. For example, TripAdvisor returns rating strings like `"4.5 of 5 bubbles"` and review counts like `"(128)"`.
**Solution:** We created `extract_float()` and `extract_int()` helper functions using Regular Expressions (`re` library) to dynamically isolate and cast the raw numerical data into pure Python `float` and `int` types before database insertion.

### Problem 2: Duplicate Ingestion
If the pipeline is run multiple times, it risks inserting duplicate restaurants or meals, completely corrupting our statistical analytics.
**Solution:** We wrapped our insertion logic in a `try-except` block catching `pymongo.errors.DuplicateKeyError`. Because we utilize the primary URL/ID as the document `_id`, MongoDB mathematically rejects the duplicate, and our script gracefully skips it without crashing the pipeline.

### Problem 3: The Missing `_id` Illusion
After inserting the documents into MongoDB, viewing them in the MongoDB Compass GUI gave the illusion that the `_id` field strings were "missing" letters towards the end (e.g., `"Review_..."`).
**Solution:** This was merely a visual truncation by the Compass UI to preserve screen layout. The full string was verified to be securely stored and accessible via Python queries or by switching Compass into the JSON `{}` view mode.

## 5. The Result We Got
The script seamlessly ingested all historical records into our active database.
- **1,334** Restaurants inserted
- **666** Meals inserted
- **0** Duplicates occurred

The database is now perfectly staged and ready for Hadoop/HDFS synchronization.
