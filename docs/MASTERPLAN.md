# Project Master Plan: Food & Restaurant Sentiment Analysis System
## Detailed Roadmap, Modules, Cycles, and Tasks (Ubuntu 24.04 WSL2 LTS)

This Master Plan divides the Food & Restaurant Sentiment Analysis System on Ubuntu 24.04 WSL2 LTS into structured, incremental development cycles. Each task lists detailed implementation steps, target files, Linux command references, and a clear "Definition of Done" (DoD).

---

## Development Strategy
1. **Incremental Execution**: One task must be fully completed, tested locally, and verified on WSL2/Ubuntu before moving to the next.
2. **AI-Assisted Work**: Use GEMINI CLI along with `/memory` commands to load this context. Ask the agent to implement specific tasks using: `Implement Task X.Y from MASTERPLAN.md`.
3. **Branching/State Tracking**: Update the `[ ]` checklist status to `[x]` as tasks are completed.

---

## Project Timeline Overview

| Milestone | Target Scope | Expected Deliverables |
| :--- | :--- | :--- |
| **Cycle 0** | Workspace & Dependency Sandbox | `bin/setup.sh`, `bin/run.sh` shell scripts, directory tree setup |
| **Cycle 1** | Scrapers & DBMS Ingestion | TripAdvisor scraper, API parser, MongoDB (raw) & MySQL (cleaned) populated |
| **Cycle 2** | HDFS Sync & Sqoop Pipelines | Sqoop or Python sync scripts, HDFS data structures verified |
| **Cycle 3** | Analytics & MapReduce Engine | 8 Python MapReduce analytics jobs (`mrjob`) on Hadoop YARN Streaming |
| **Cycle 4** | DevOps, Backup & Recovery | Dump/Restore automation shell scripts for MySQL & MongoDB |
| **Cycle 5** | Streamlit Interactive GUI | Web Dashboard, 6 plotly charts, MySQL CRUD, Hive OLAP Queries |
| **Cycle 6** | Validation, Video & Delivery | End-to-end integration test, slide deck, demo video |

---

## Detailed Cycles & Tasks

### Cycle 0: Workspace & Dependency Sandbox (Environment Verification)
*Goal: Ensure any teammate can pull the repo and immediately configure their local WSL2/Ubuntu environment.*

- [x] **Task 0.1: Initialize Directory Tree**
  - **Implementation**: Create standard workspace layout (`bin/`, `src/`, `config/`, `data/`, `docs/`). Add a robust `.gitignore` file to ignore local databases (`data/db/`), HDFS metadata (`data/hdfs/`), Python virtual environments (`venv/`), environment variables (`.env`), and compiled Python files (`__pycache__/`).
  - **DoD**: Run `git status` showing clean working tree with only tracked template files.
- [ ] **Task 0.2: Implement `bin/setup.sh`**
  - **Implementation**: Write a shell script (`#!/bin/bash`) that:
    1. Installs/verifies python3-pip, python3-venv, and OpenJDK 11.
    2. Initializes a virtual environment `venv` using Python 3.10/3.11: `python3 -m venv venv`.
    3. Activates the environment and installs libraries: `pip install -r requirements.txt`.
    4. Initializes database connection drivers and creates tables in MySQL and collections in MongoDB.
  - **DoD**: Execution of `bash bin/setup.sh` runs end-to-end with exit code 0 and verifies python modules exist.
- [ ] **Task 0.3: Implement `bin/run.sh`**
  - **Implementation**: Write a shell script (`#!/bin/bash`) that:
    1. Sets up local environment variables:
       ```bash
       export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
       export HADOOP_HOME=/usr/local/hadoop
       export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
       ```
    2. Starts local daemons safely:
       ```bash
       sudo service mysql start
       sudo service mongod start
       start-dfs.sh
       start-yarn.sh
       ```
    3. Runs the data pipeline and launches the Streamlit GUI.
  - **DoD**: Execution of `./bin/run.sh` successfully boots all services, runs the sync scripts, and launches Streamlit on `localhost:8501`.

---

### Cycle 1: Scrapers & DBMS Ingestion (Data Staging)
*Goal: Crawl, fetch, clean, and load raw data into MongoDB and MySQL.*

- [x] **Task 1.1: Implement TripAdvisor Python Scraper**
  - **File**: `src/crawler/tripadvisor_job/` (Scrapy Spider or BeautifulSoup script)
  - **Implementation**: Parse restaurant name, rating, address, district, city, review count, and reviews array. Store output raw JSON in `src/crawler/tripadvisor_job/full_output.json`.
  - **DoD**: Exposes 1,334 restaurants and 44,000+ reviews in structured JSON.
- [x] **Task 1.2: Implement TheMealDB API Parser**
  - **File**: `src/crawler/fetch_mealdb.py`
  - **Implementation**: Loop letters A-Z on `search.php?f={}`. Flatten `strIngredient1` to `strIngredient20` into a unified `ingredients` array. Implement offline backup to read from `src/crawler/seed/meals.json` if network hits 403 or 429.
  - **DoD**: Generates structured `meals.json` seed containing 666 clean recipe records.
- [x] **Task 1.3: Setup Database Schema & Data Ingestion (ETL)**
  - **File**: `src/ingest/clean_and_populate.py`
  - **Implementation**: 
    1. Read raw JSON inputs. Clean rating strings (e.g., "4.5 of 5 bubbles" -> `4.5`) and review counts.
    2. Write documents into MongoDB database `sentiment_db` collections `restaurants` and `meals`.
    3. Write structured records into MySQL database `food_sentiment_db` tables `restaurants`, `reviews`, and `meals` (relational CSDL schema) using `mysql.connector`. Implement `DuplicateKeyError` and duplicate primary key checks.
  - **DoD**: Run the Python script and verify MongoDB collections and MySQL tables contain 1,334 restaurants and 666 meals with zero duplicate records.

---

### Cycle 2: Storage & Sync Pipelines (HDFS Synchronization)
*Goal: Sync the clean structures from MySQL/MongoDB to Hadoop HDFS.*

- [ ] **Task 2.1: Create HDFS Sync Script**
  - **File**: `src/ingest/mysql_to_hdfs.py` / `src/ingest/mongo_to_hdfs.py` (or use Apache Sqoop)
  - **Implementation**: 
    * If Python: Connect to databases, query clean records, format them as JSON Lines (`.jsonl`), and stream them to HDFS:
      ```bash
      hdfs dfs -mkdir -p /data/raw
      hdfs dfs -put -f /tmp/restaurants.jsonl /data/raw/restaurants.jsonl
      ```
    * If Apache Sqoop: Run the sqoop command to import MySQL tables directly into HDFS directory `/data/raw/` in CSV or parquet format.
  - **DoD**: Run scripts and verify files exist on HDFS using `hdfs dfs -ls /data/raw/`.
- [ ] **Task 2.2: Verify HDFS Integration & Hive Schema**
  - **Implementation**: Create Hive schemas inside `/usr/local/hive` or using HiveQL script `src/ingest/hive_schema.sql` to map the HDFS raw paths.
  - **DoD**: Execute `hive -f src/ingest/hive_schema.sql` and verify Hive tables can be queried via `hive -e "SELECT COUNT(*) FROM restaurants"`.

---

### Cycle 3: Analytics & MapReduce Engine (8 Analytical Jobs)
*Goal: Write and test 8 independent MapReduce jobs using Python's `mrjob` library running on YARN.*

- [ ] **Task 3.1: MapReduce Job 1 - Average Rating by District**
  - **File**: `src/mapreduce/mr_rating_by_district.py`
  - **DoD**: Outputs average rating and review counts aggregated by district name.
- [ ] **Task 3.2: MapReduce Job 2 - Cuisine Frequency Counter**
  - **File**: `src/mapreduce/mr_cuisine_count.py`
  - **DoD**: Returns a sorted frequency distribution of cuisine tags across HCMC restaurants.
- [ ] **Task 3.3: MapReduce Job 3 - Price Category Distribution**
  - **File**: `src/mapreduce/mr_price_segment.py`
  - **DoD**: Aggregates restaurant count by price category (Budget, Moderate, Luxury).
- [ ] **Task 3.4: MapReduce Job 4 - Review Sentiment Analysis**
  - **File**: `src/mapreduce/mr_sentiment_analysis.py`
  - **DoD**: Evaluates comment blocks using a simple keyword lexer to return positive/negative ratios per restaurant.
- [ ] **Task 3.5: MapReduce Job 5 - Meal-to-Restaurant Ingredient Matching**
  - **File**: `src/mapreduce/mr_ingredient_match.py`
  - **DoD**: Matches recipe ingredients from `meals` to comment keywords in restaurants serving that cuisine.
- [ ] **Task 3.6: MapReduce Job 6 - Top 10 Most Reviewed Restaurants**
  - **File**: `src/mapreduce/mr_top_reviewed.py`
  - **DoD**: Emits the top 10 hotspot locations based on total review counts.
- [ ] **Task 3.7: MapReduce Job 7 - Review Distribution Profile**
  - **File**: `src/mapreduce/mr_review_distribution.py`
  - **DoD**: Aggregates the frequency of review stars from 1.0 to 5.0.
- [ ] **Task 3.8: MapReduce Job 8 - Delivery Status Analysis**
  - **File**: `src/mapreduce/mr_delivery_analysis.py`
  - **DoD**: Compares review sentiments between delivery-friendly and dine-in-only locations.

---

### Cycle 4: DevOps, Backup & Resilience
*Goal: Secure databases with backup recovery shell commands.*

- [ ] **Task 4.1: Automate MongoDB & MySQL Backup & Restore**
  - **File**: `src/backup/db_backup.sh` / `src/backup/db_restore.sh`
  - **Implementation**: 
    * Backup: Run `mysqldump -u root -p food_sentiment_db > /data/backups/mysql_backup.sql` and `mongodump --db sentiment_db --out /data/backups/mongo/`.
    * Restore: Run `mysql -u root -p food_sentiment_db < mysql_backup.sql` and `mongorestore --db sentiment_db /data/backups/mongo/sentiment_db/`.
  - **DoD**: Running `./src/backup/db_backup.sh` creates timestamped backups in `/data/backups/` and restore script recovers deleted data.
- [ ] **Task 4.2: Port & Service Checks**
  - **Implementation**: Update `bin/run.sh` with a port detection loop (`netstat` or `ss`) to verify that ports 3306 (MySQL), 27017 (MongoDB), 9000 (HDFS), and 10000 (Hive) are not blocked.

---

### Cycle 5: Interactive GUI (Streamlit Web Dashboard)
*Goal: Build a beautiful, interactive frontend on WSL2 connecting to MySQL/Hive and triggering HDFS/MapReduce.*

- [ ] **Task 5.1: Build Streamlit Base Layout**
  - **File**: `src/streamlit_app/app.py`
  - **DoD**: Establish pages (Data Management, Real-time CRUD, Analytics Reports, Job Triggers).
- [ ] **Task 5.2: Create Full MySQL CRUD Interface**
  - **Implementation**: Streamlit forms to create, query, modify, and delete restaurant listings inside MySQL using SQL transactions.
  - **DoD**: Users can add a new restaurant on screen, search it, update its district, and delete it with instant feedback.
- [ ] **Task 5.3: Develop Visualization Page (6 Charts, 3 Types)**
  - **Implementation**: Query Apache Hive server using `PyHive` to fetch aggregated MapReduce output values and render Plotly charts (Bar chart of district ratings, Pie chart of cuisines, and Map/Scatter plot of districts).
  - **DoD**: Renders 6 working charts showing big data insights.
- [ ] **Task 5.4: DevOps Operations Triggers**
  - **Implementation**: Add buttons in Streamlit to trigger `db_backup.sh`, runs the sync pipeline, and launches MapReduce analysis jobs asynchronously.
  - **DoD**: Verify execution triggers run successfully from the GUI.

---

### Cycle 6: Verification, Slides & Demo Video
*Goal: Finalize reports, slide decks, and record a high-quality video following HCMUTE standards.*

- [ ] **Task 6.1: End-to-End Integration Testing**
  - **DoD**: Deploy the project folder to a fresh WSL2 instance, run setup, boot services, trigger crawler, perform HDFS sync, execute MapReduce, view results in Hive, and run Streamlit dashboard without a single terminal crash.
- [ ] **Task 6.2: Draft Slides & Document Report**
  - **DoD**: Produce a step-by-step report including WSL2 configurations and screenshots. Complete a 12-slide presentation deck.
- [ ] **Task 6.3: Record and Edit Presentation Video**
  - **DoD**: Export a 7-minute Full HD demo video featuring the group's webcam introduction, school logo watermarks, narration, background music, and Vietnamese subtitles.