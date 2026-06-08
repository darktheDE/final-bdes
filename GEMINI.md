# Project: Food & Restaurant Sentiment Analysis System (Native Windows Big Data Stack)

## General Instructions

- **Native Windows Compatibility**: All generated scripts must run natively on Windows 10/11 without WSL2, Docker, or Linux VMs. 
  - Never write Shell/Bash scripts (`.sh`). Use Windows Batch scripts (`.bat`) or Python.
  - Windows paths often contain spaces (e.g., `C:\Program Files`). In Batch scripts, always wrap path variables in double quotes (e.g., `"%HADOOP_HOME%\bin"`).
  - In Python, use raw strings `r"..."` or forward slashes `/` for file paths to avoid backslash escaping issues.
- **Python-Only MapReduce**: Do not generate Java MapReduce classes. All MapReduce code must be written in Python using the `mrjob` library.
- **Robust Ingestion & Fallbacks**: Scraping and API ingestion modules must be offline-tolerant. Always implement a `try-except` fallback block to read from local seed data inside `src/crawler/seed/` if network requests fail or hit rate-limits (HTTP 403/429).
- **Environment Safety**: When launching services via batch scripts, configure environment variables locally for the active command prompt session. Do not permanently alter the user's global system environment variables.

---

## Coding Style

### Python
- Follow PEP 8 guidelines. Use 4 spaces for indentation.
- Write docstrings for all functions, especially for scraper parsers and MapReduce step definitions.
- Use strict error handling with descriptive logging instead of silent passes.
- Use `pymongo` for MongoDB operations and standard Hadoop Streaming configurations for `mrjob`.

### Windows Batch (`.bat`)
- Use `@echo off` at the beginning of scripts to keep the output clean.
- Use `setlocal` where appropriate to isolate variables.
- Wrap paths in double quotes: `"%~dp0..\data\db"`.
- Use `start` to run background daemons (e.g., `start "MongoDB" mongod ...`) so they run in separate windows and do not block the execution pipeline.

---

## Project Structure & File Map

Always place newly generated files or reference existing files using this exact map:
- `bin/setup.bat`: One-click environment verification and automated binary setup (downloads `winutils.exe` and `hadoop.dll`).
- `bin/run.bat`: Entry point script to set session variables, launch MongoDB/HDFS, run pipelines, and start Streamlit.
- `src/crawler/`: Scraping scripts (`scrape_tripadvisor.py`, `fetch_mealdb.py`).
- `src/crawler/seed/`: Offline backup files for local development.
- `src/ingest/`: MongoDB-to-HDFS data pipeline (`mongo_to_hdfs.py`).
- `src/mapreduce/`: Contains the 8 independent MapReduce jobs (e.g., `mr_cuisine_count.py`).
- `src/streamlit_app/`: Frontend dashboard application (`app.py`).

---

## Data Schema Reference

Ensure any code dealing with database interactions or MapReduce analytics maps exactly to these schemas to avoid `KeyError` exceptions:

### MongoDB Collection: `restaurants` (TripAdvisor Schema)
```json
{
  "_id": "restaurant_12345",
  "name": "Pho Hung",
  "rating": 4.5,
  "review_count": 128,
  "address": "123 Nguyen Trai, District 1, HCMC",
  "district": "District 1",
  "city": "HCMC",
  "cuisines": ["Vietnamese", "Soup"],
  "price_range": "$$ - $$$",
  "reviews": [
    {
      "user": "Alice",
      "rating": 5,
      "comment": "Excellent Pho! The broth is very rich and authentic."
    }
  ]
}
```

### MongoDB Collection: `meals` (TheMealDB Schema)
```json
{
  "_id": "meal_52772",
  "name": "Pho",
  "category": "Beef",
  "area": "Vietnamese",
  "instructions": "Simmer beef bones with star anise, ginger, and fish sauce...",
  "ingredients": ["Beef", "Rice Noodles", "Star Anise", "Ginger", "Onion"]
}
```