# Project: Food & Restaurant Sentiment Analysis System (Ubuntu 24.04 WSL2 LTS Big Data Stack)

## General Instructions

- **Ubuntu 24.04 WSL2 Compatibility**: All generated scripts and configurations must run natively on Ubuntu 24.04 LTS inside WSL2.
  - Never write Windows Batch scripts (`.bat`) for active Linux executions. Use Linux Bash scripts (`.sh`) or Python.
  - Paths must follow POSIX standards (e.g., `/usr/local/hadoop`, `./src/crawler/seed/`). Never use backslashes (`\`) for Linux paths.
  - When accessing directories shared between Windows and WSL2, map them correctly (e.g., `/mnt/d/Project/final-bdes/`).
- **Python-Only MapReduce**: All MapReduce code must be written in Python using the `mrjob` library executing via Hadoop Streaming.
- **Robust Ingestion & Fallbacks**: Scraping and API ingestion modules must be offline-tolerant. Always implement a `try-except` fallback block to read from local seed data inside `src/crawler/seed/` if network requests fail or hit rate-limits (HTTP 403/429).
- **Environment Safety**: Set environment variables (such as `JAVA_HOME`, `HADOOP_HOME`, `PATH`) dynamically in the active shell or `.bashrc`. Do not pollute global WSL2 environments unnecessarily.

---

## Coding Style

### Python
- Follow PEP 8 guidelines. Use 4 spaces for indentation.
- Write docstrings for all functions, especially for scraper parsers and MapReduce step definitions.
- Use strict error handling with descriptive logging instead of silent passes.
- Use `pymongo` for MongoDB operations and standard Hadoop Streaming configurations for `mrjob`.

### Bash Shell (`.sh`)
- Use `#!/bin/bash` at the beginning of all shell scripts.
- Use `set -e` to make scripts exit immediately if a command exits with a non-zero status.
- Wrap paths in double quotes: `"${HADOOP_HOME}/bin/hadoop"`.
- Use standard background process controls (e.g., `mongod --fork --logpath ...` or systemctl/service commands) rather than Windows `start`.

---

## Project Structure & File Map

Always place newly generated files or reference existing files using this exact map:
- `bin/setup.sh`: One-click environment verification and automated library installation for Ubuntu 24.04 WSL2.
- `bin/run.sh`: Entry point script to set session variables, launch MongoDB/HDFS, run pipelines, and start Streamlit.
- `src/crawler/`: Scraping scripts (`tripadvisor_job/` Scrapy spider, `fetch_mealdb.py`).
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
  "name": "Pho",
  "rating": 4.5,
  "review_count": 128,
  "address": "123 Nguyen Trai, District 1, HCMC",
  "district": "District 1",
  "city": "HCMC",
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