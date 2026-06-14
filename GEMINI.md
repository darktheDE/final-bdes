# Project: Food & Restaurant Sentiment Analysis System (Ubuntu 24.04 WSL2 LTS Big Data Stack)

## General Instructions & Environment Prerequisite Constraints

- **Ubuntu 24.04 WSL2 Clean Environment**: The system is assumed to run on a clean Ubuntu 24.04 LTS installation inside WSL2. **No services are pre-installed.**
- **Service Installation Restriction**:
  - The setup script `bin/setup.sh` **MUST NOT** install system-wide database or big data services (MySQL, MongoDB, Hadoop, Hive, Java).
  - The developer/user must install these services manually.
  - `bin/setup.sh` is strictly limited to:
    1. Verifying if basic command line utilities are present (python3, pip3, java).
    2. Creating the Python virtual environment (`venv`).
    3. Installing Python dependencies from `requirements.txt`.
    4. Running database schema initialization (`src/ingest/init_db.py`) **only if** MySQL/MongoDB services are running. If they are not running, print a clear diagnostic warning and exit gracefully without crashing.
- **Ubuntu 24.04 WSL2 Compatibility**: All generated scripts and configurations must run natively on Ubuntu 24.04 LTS inside WSL2.
  - Never write Windows Batch scripts (`.bat`) for active Linux executions. Use Linux Bash scripts (`.sh`) or Python.
  - Paths must follow POSIX standards (e.g., `/usr/local/hadoop`, `./src/crawler/seed/`). Never use backslashes (`\`) for Linux paths.
  - When accessing directories shared between Windows and WSL2, map them correctly (e.g., `/mnt/d/Project/final-bdes/`).
- **Python-Only MapReduce**: All MapReduce code must be written in Python using the `mrjob` library executing via Hadoop Streaming.
- **Robust Ingestion & Fallbacks**: Scraping and API ingestion modules must be offline-tolerant. Always implement a `try-except` fallback block to read from local seed data inside `src/crawler/seed/` if network requests fail or hit rate-limits (HTTP 403/429).
- **No Personal Identifiers**: Do not include any personal identifiers or usernames (e.g., `kienhung`, `kien_hung`) in scripts, configuration files, paths, or setup commands. All scripts and paths must be generic (e.g., using `$USER`, `$HOME`, or dynamic user detection) to ensure the pipeline runs out-of-the-box on multiple independent machines.
- **Standard WSL2 Deployment & Testing Workflow**: Follow the step-by-step procedure defined in `SETUP_GUIDE.md` and verify the components using `TEST_PLAN.md` to guarantee a clean install and execution on any standalone WSL2 Ubuntu environment.
- **Environment Safety**: Set environment variables (such as `JAVA_HOME`, `HADOOP_HOME`, `PATH`) dynamically in the active shell or `.bashrc`. Do not pollute global WSL2 environments unnecessarily.
- **Infrastructure Logging & Reusability**:
  - Keep a complete log of all installation, setup, configuration, and debugging processes to assist with report writing and make it simple to replicate the system on other environments.
  - Consolidate all infrastructure installation steps (for Java, Hadoop, Hive, databases, etc.), environment variables, XML configuration files (Hadoop and Hive site XMLs), and dependency fixes (Guava mismatch, MySQL JDBC jar download) into a single unified Bash script: `bin/install_infra.sh`.
  - Save execution history, configuration files, and troubleshooting steps in the task logs (`docs/process/`) to fulfill the course project requirements.
- **Hive Java 8 Runtime Requirement**: Apache Hive 3.1.3 must run under **Java 8** (`/usr/lib/jvm/java-8-openjdk-amd64`) due to classloading incompatibilities on Java 11+. Hadoop's `hadoop-env.sh` must export `JAVA_HOME` conditionally (`export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-11-openjdk-amd64}`) to preserve the Java 8 setting when Hive executes Hadoop commands.
- **Dedicated Hive Metastore User**: Always configure a dedicated MySQL user (e.g., `hive` with password `hive`) with full privileges on the `hive_metastore` schema. Do not use passwordless `root` accounts for Hive Metastore connections to avoid authentication errors with Java JDBC drivers.

---

## Technical Stack & Version Specifications

To avoid runtime compatibility issues, both developer and AI Agent must strictly align with the following component versions:
- **Java Platform**: OpenJDK 11 LTS (Required for Apache Hadoop compatibility)
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
- `bin/setup.sh`: One-click environment verification and automated library installation for Ubuntu 24.04 WSL2.
- `bin/run.sh`: Entry point script to set session variables, launch MySQL/MongoDB/HDFS, run pipelines, and start Streamlit.
- `src/crawler/`: Scraping scripts (`tripadvisor_job/` Scrapy spider, `fetch_mealdb.py`).
- `src/crawler/seed/`: Offline backup files for local development.
- `src/ingest/`: MongoDB-to-HDFS and MySQL-to-HDFS data pipeline (`mongo_to_hdfs.py`, `mysql_to_hdfs.py`).
- `src/mapreduce/`: Contains the 8 independent MapReduce jobs (e.g., `mr_cuisine_count.py`).
- `src/streamlit_app/`: Frontend dashboard application (`app.py`).

---

## Data Schema Reference

Ensure any code dealing with database interactions or MapReduce analytics maps exactly to these schemas:

### MongoDB Collection: `restaurants` (TripAdvisor Raw Schema)
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

### MySQL Relational Tables (Cleaned Schema)
- **Table:** `restaurants`
  - `id` (VARCHAR(50), Primary Key)
  - `name` (VARCHAR(100))
  - `rating` (FLOAT)
  - `review_count` (INT)
  - `address` (VARCHAR(255))
  - `district` (VARCHAR(50))
  - `city` (VARCHAR(50))
  - `price_range` (VARCHAR(20))
- **Table:** `reviews`
  - `id` (INT, Auto Increment, Primary Key)
  - `restaurant_id` (VARCHAR(50), Foreign Key pointing to `restaurants(id)`)
  - `user` (VARCHAR(50))
  - `rating` (FLOAT)
  - `comment` (TEXT)
- **Table:** `meals`
  - `id` (VARCHAR(50), Primary Key)
  - `name` (VARCHAR(100))
  - `category` (VARCHAR(50))
  - `area` (VARCHAR(50))
  - `instructions` (TEXT)
  - `ingredients` (TEXT) -- Comma-separated list or JSON array string