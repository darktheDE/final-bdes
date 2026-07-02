# Project: Food & Restaurant Sentiment Analysis System (Ubuntu 24.04 WSL2 LTS Big Data Stack)

## General Instructions & Environment Prerequisite Constraints

- **Ubuntu 24.04 WSL2 Clean Environment**: The system is assumed to run on a clean Ubuntu 24.04 LTS installation inside WSL2. **No services are pre-installed.**
- **Service Installation Restriction**:
  - The script `bin/install_infra.sh` handles ALL infrastructure installation: Java 8, Hadoop, Hive, MySQL, MongoDB, Python venv.
  - The developer/user must run `bin/install_infra.sh` once on a clean machine, then use `bin/run.sh` for every subsequent run.
  - `bin/run.sh` is the **sole entry point** for running the full pipeline. It accepts `--crawl` flag to fetch fresh data.
- **Ubuntu 24.04 WSL2 Compatibility**: All generated scripts and configurations must run natively on Ubuntu 24.04 LTS inside WSL2.
  - Never write Windows Batch scripts (`.bat`) for active Linux executions. Use Linux Bash scripts (`.sh`) or Python.
  - Paths must follow POSIX standards (e.g., `/usr/local/hadoop`, `./src/crawler/seed/`). Never use backslashes (`\`) for Linux paths.
  - When accessing directories shared between Windows and WSL2, map them correctly (e.g., `/mnt/d/Project/...` or relative path `./`).
- **Python-Only MapReduce**: All MapReduce code must be written in Python using the `mrjob` library executing via Hadoop Streaming.
- **Robust Ingestion & Fallbacks**: Scraping and API ingestion modules must be offline-tolerant. Always implement a `try-except` fallback block to read from local seed data inside `src/crawler/seed/` if network requests fail or hit rate-limits (HTTP 403/429).
- **No Personal Identifiers**: Do not include any personal identifiers or usernames (e.g., `kienhung`, `kien_hung`) in scripts, configuration files, paths, or setup commands. All scripts and paths must be generic (e.g., using `$USER`, `$HOME`, or dynamic user detection) to ensure the pipeline runs out-of-the-box on multiple independent machines.
- **Standard WSL2 Deployment & Testing Workflow**: Follow the step-by-step procedure defined in `SETUP_GUIDE.md` and verify the components using `TEST_PLAN.md` to guarantee a clean install and execution on any standalone WSL2 Ubuntu environment.
- **Environment Safety**: Set environment variables (such as `JAVA_HOME`, `HADOOP_HOME`, `PATH`) dynamically in the active shell or `.bashrc`. Do not pollute global WSL2 environments unnecessarily.
- **Infrastructure Logging & Reusability**:
  - Keep a complete log of all installation, setup, configuration, and debugging processes to assist with report writing and make it simple to replicate the system on other environments.
  - Consolidate all infrastructure installation steps (for Java, Hadoop, Hive, databases, etc.), environment variables, XML configuration files (Hadoop and Hive site XMLs), and dependency fixes (Guava mismatch, MySQL JDBC jar download) into a single unified Bash script: `bin/install_infra.sh`.
  - Save execution history, configuration files, and troubleshooting steps in the task logs (`docs/process/`) to fulfill the course project requirements.
- **Unified Java 8 Runtime**: Apache Hadoop 3.3.6 and Apache Hive 3.1.3 must both strictly run under **Java 8** (`/usr/lib/jvm/java-8-openjdk-amd64`). This unified setup prevents Kryo serialization crashes (`NoSuchFieldException: parentOffset`) in Hive 3.x while executing MapReduce tasks.
- **Dedicated Hive Metastore User**: Always configure a dedicated MySQL user (e.g., `hive` with password `hive`) with full privileges on the `hive_metastore` schema. Do not use passwordless `root` accounts for Hive Metastore connections to avoid authentication errors with Java JDBC drivers.

---

## Technical Stack & Version Specifications

To avoid runtime compatibility issues, both developer and AI Agent must strictly align with the following component versions:
- **Java Platform**: OpenJDK 8 LTS (Required for stable Apache Hive MapReduce compatibility)
- **Hadoop Ecosystem**: Apache Hadoop 3.3.6 LTS (Configured in pseudo-distributed mode)
- **Data Warehouse**: Apache Hive 3.1.3 (Configured to map HDFS directories)
- **NoSQL Database**: MongoDB Community Server 8.0 LTS
- **Relational Database**: MySQL Server 8.0
- **Python Language**: Python 3.10 / 3.11 (Configured via `venv` virtual environment to prevent `distutils` import errors)
- **Web Application**: Streamlit 1.35.0 (Running on host port 8501)
- **Scraping Framework**: Scrapy 2.11.0 / BeautifulSoup4 4.12.0

---

## AI Agent Collaboration Workflow & Guidelines

When implementing any task in this repository, the AI Agent must follow these step-by-step guidelines:
1. **Read Prerequisites & Documentation**:
   - Before executing code modifications, read the relevant files in `docs/` (e.g., `docs/REQUIREMENTS.md` for grading criteria, `docs/ARCHITECTURE.md` for architecture flows, `docs/TROUBLESHOOTING.md` for quick diagnostics).
2. **Strict Schema Compliance**:
   - Ensure all data parsing, loading, and MapReduce jobs strictly comply with the database schemas listed below.
3. **Incremental Testing**:
   - For every script or feature, provide the exact test command (e.g. `python -m pytest` or raw execution verification).
   - Test scripts using mock or seed data in `src/crawler/seed/` before asserting success.

---

## Coding Style

### Python
- Follow PEP 8 guidelines. Use 4 spaces for indentation.
- Write docstrings for all functions, especially for scraper parsers, database connection modules, and MapReduce step definitions.
- Use strict error handling with descriptive logging instead of silent passes.
- Use `pymongo` for MongoDB operations and `mysql.connector` or `SQLAlchemy` for MySQL transactional CRUD.

### Bash Shell (`.sh`)
- Use `#!/bin/bash` at the beginning of all shell scripts.
- Use `set -e` to make scripts exit immediately if a command exits with a non-zero status.
- Wrap paths in double quotes: `"${HADOOP_HOME}/bin/hadoop"`.
- Use standard service commands (e.g., `sudo service mysql start` or `sudo service mongod start`) to handle local database daemons.

---

## Project Structure & File Map

Always place newly generated files or reference existing files using this exact map:
- `bin/install_infra.sh`: **Run once** — installs Java 8, Hadoop 3.3.6, Hive 3.1.3, MySQL, MongoDB, Python venv, and all dependencies. Also copies XML config from `conf/`.
- `bin/run.sh`: **Entry point** — starts all services, optionally fetches data (`--crawl`), runs MapReduce jobs (`--jobs`), launches Streamlit on port 8501.
- `bin/stop.sh`: Stops all services. Accepts `--backup` (backup before stop) and `--cleandata` (wipe all data, for demo).
- `conf/hadoop/`: Hadoop XML config files (`core-site.xml`, `hdfs-site.xml`, `yarn-site.xml`, `mapred-site.xml`).
- `conf/hive/hive-site.xml`: Hive metastore config.
- `conf/mrjob.conf`: mrjob Hadoop runner config.
- `src/crawler/`: Scraping scripts (`tripadvisor_job/` Scrapy spider, `fetch_mealdb.py`).
- `src/crawler/seed/`: Offline backup files for local development.
- `src/ingest/`: Data normalization + DB init (`init_db.py`), MongoDB-to-HDFS (`mongo_to_hdfs.py`), MySQL-to-HDFS (`mysql_to_hdfs.py`), Hive schema/analytics SQL.
- `src/mapreduce/`: Contains 8 independent MapReduce jobs.
- `src/streamlit_app/`: Frontend dashboard (`app.py`, `hive_connector.py`).
- `src/backup/`: Backup and restore scripts (`db_backup.sh`, `db_restore.sh`).
- `docs/process/`: Execution logs, debug notes, refactor logs.

---

## Data Schema Reference

Ensure any code dealing with database interactions or MapReduce analytics maps exactly to these schemas.

> **⚠️ Source of Truth**: Schemas below reflect **actual scraped data**, not original design assumptions.

### MongoDB Collection: `restaurants` (TripAdvisor — Actual Scraped Schema)
```json
{
  "_id": "https://www.tripadvisor.com/Restaurant_Review-g293925-d33215720-...",
  "name": "Bún Chả Hà Thành by Hanoi Corner",
  "rating": 5.0,
  "review_count": "(112)",
  "address": "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1, Ho Chi Minh City 70000 Vietnam",
  "district": "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1",
  "city": "Ho Chi Minh City 70000 Vietnam",
  "reviews": [
    {
      "user": "Chloe C",
      "rating": "5 of 5 bubbles",
      "comment": "Excellent food with friendly service by Ly."
    }
  ]
}
```
**Parsing rules applied by `init_db.py`:**
- `_id` (URL) → `id` extracted as `rest_dXXXXXXXX`
- `review_count` `"(112)"` → INT `112`
- `district` (full address) → `district_parsed` (extracted quận name, e.g. `"Quận 1"`)
- `city` `"Ho Chi Minh City 70000 Vietnam"` → `"Ho Chi Minh City"`
- review `rating` `"5 of 5 bubbles"` → FLOAT `5.0`
- **No `price_range` field exists in TripAdvisor data**

### MongoDB Collection: `meals` (TheMealDB — Actual Schema)
```json
{
  "_id": "meal_53262",
  "name": "Adana kebab",
  "category": "Lamb",
  "area": "Turkish",
  "instructions": "step 1\r\nFinely chop the peppers...",
  "ingredients": ["Romano Pepper", "Lamb Mince", "Red Pepper Paste"]
}
```
**Relationship to TripAdvisor data**: `mr_ingredient_match.py` uses the `ingredients` list from TheMealDB as a vocabulary to find ingredient mentions in TripAdvisor review comments.

### MySQL Relational Tables (Cleaned Schema — post-normalize)
- **Table:** `restaurants`
  - `id` (VARCHAR(255), Primary Key) — e.g. `rest_d33215720`
  - `name` (VARCHAR(255))
  - `rating` (FLOAT) — restaurant-level average rating
  - `review_count` (INT) — parsed from `"(112)"`
  - `address` (VARCHAR(500)) — full raw address
  - `district` (VARCHAR(255)) — raw district string from TripAdvisor
  - `district_parsed` (VARCHAR(100)) — extracted quận name, e.g. `"Quận 1"`
  - `city` (VARCHAR(100)) — normalized, e.g. `"Ho Chi Minh City"`
  - ~~`price_range`~~ — **REMOVED** (field does not exist in TripAdvisor data)
- **Table:** `reviews`
  - `id` (INT, Auto Increment, Primary Key)
  - `restaurant_id` (VARCHAR(255), Foreign Key → `restaurants(id)`)
  - `user` (VARCHAR(255))
  - `rating` (FLOAT) — parsed from `"5 of 5 bubbles"` → `5.0`
  - `comment` (TEXT)
- **Table:** `meals`
  - `id` (VARCHAR(255), Primary Key) — e.g. `meal_53262`
  - `name` (VARCHAR(255))
  - `category` (VARCHAR(100)) — e.g. `"Lamb"`, `"Seafood"`
  - `area` (VARCHAR(100)) — e.g. `"Turkish"`, `"British"`
  - `instructions` (TEXT)
  - `ingredients` (TEXT) — comma-separated string, e.g. `"Garlic, Onion, Pepper"`

### MapReduce Jobs (8 jobs)
| Job | Input | Description |
|-----|-------|-------------|
| `mr_rating_by_district.py` | restaurants.jsonl | Avg rating per parsed district |
| `mr_cuisine_count.py` | meals.jsonl | Frequency of meal categories & areas |
| `mr_rating_bucket.py` | restaurants.jsonl | Count restaurants per rating group (replaces price_segment) |
| `mr_sentiment_analysis.py` | restaurants.jsonl | Sentiment score per restaurant from review comments |
| `mr_ingredient_match.py` | restaurants.jsonl | Ingredient mentions in reviews (linked to TheMealDB) |
| `mr_top_reviewed.py` | restaurants.jsonl | Top 10 most-reviewed restaurants |
| `mr_review_distribution.py` | restaurants.jsonl | Distribution of star ratings in reviews |
| `mr_delivery_analysis.py` | restaurants.jsonl | Avg rating: delivery-mentioned vs dine-in reviews |