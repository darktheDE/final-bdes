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
| **Cycle 0** | Base Services Manual Setup | SSH, OpenJDK 8, MySQL, MongoDB, Hadoop, and Hive installation |
| **Cycle 1** | Workspace & Dependency Sandbox | `bin/setup.sh`, `bin/run.sh` shell scripts, directory tree setup |
| **Cycle 2** | Scrapers & DBMS Ingestion | TripAdvisor scraper, API parser, MongoDB (raw) & MySQL (cleaned) populated |
| **Cycle 3** | HDFS Sync & Sqoop Pipelines | Sqoop or Python sync scripts, HDFS data structures verified |
| **Cycle 4** | Analytics & MapReduce Engine | 8 Python MapReduce analytics jobs (`mrjob`) on Hadoop YARN Streaming |
| **Cycle 5** | DevOps, Backup & Recovery | Dump/Restore automation shell scripts for MySQL & MongoDB |
| **Cycle 6** | Streamlit Interactive GUI | Web Dashboard, 6 plotly charts, MySQL CRUD, Hive OLAP Queries |
| **Cycle 7** | Validation, Video & Delivery | End-to-end integration test, slide deck, demo video |

---

## Detailed Cycles & Tasks

### Cycle 0: Base Services Infrastructure Setup (Manual Installation)
*Goal: Manually download, install, and configure database and big data daemons on a clean Ubuntu 24.04 WSL2 environment.*

- [x] **Task 0.1: Configure SSH Server for Hadoop localhost Access**
  - **Step-by-Step**:
    1. Install OpenSSH server package: `sudo apt update && sudo apt install openssh-server -y`
    2. Start SSH daemon: `sudo service ssh start`
    3. Generate and register keypairs for passwordless localhost access:
       ```bash
       ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
       cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
       chmod 0600 ~/.ssh/authorized_keys
       ```
    4. Test using: `ssh localhost`
  - **DoD**: Command `ssh localhost` executes successfully without prompting for password or passphrase.

- [x] **Task 0.2: Install Java Development Kit (JDK 8)**
  - **Step-by-Step**:
    1. Install OpenJDK 8 JDK package: `sudo apt install openjdk-8-jdk -y`
    2. Add Java environment variable configuration to shell initialization profile:
       ```bash
       echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' >> ~/.bashrc
       source ~/.bashrc
       ```
  - **Test Command**: `java -version`
  - **DoD**: Output prints OpenJDK version `1.8.x`.

- [x] **Task 0.3: Install and Configure MySQL Server 8.0**
  - **Step-by-Step**:
    1. Install MySQL server: `sudo apt install mysql-server -y`
    2. Start MySQL daemon service: `sudo service mysql start`
    3. Set native password configuration for root:
       ```sql
       -- Access via: sudo mysql
       ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root';
       FLUSH PRIVILEGES;
       ```
    4. Create schema: `CREATE DATABASE food_sentiment_db;`
  - **Test Command**: `mysql -u root -proot -e "SHOW DATABASES;"`
  - **DoD**: Output contains `food_sentiment_db`.

- [x] **Task 0.4: Install MongoDB Community Server 8.0 LTS**
  - **Step-by-Step**:
    1. Import MongoDB 8.0 GPG key and repository lists:
       ```bash
       sudo apt install gnupg curl -y
       curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg
       echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
       sudo apt update
       sudo apt install -y mongodb-org
       ```
    2. Start MongoDB daemon: `sudo service mongod start`
  - **Test Command**: `mongosh --eval "db.adminCommand('ping')"`
  - **DoD**: Command prints `ok: 1` verification JSON message.

- [x] **Task 0.5: Install and Configure Apache Hadoop 3.3.6**
  - **Step-by-Step**:
    1. Download Apache Hadoop 3.3.6 tarball package and extract it to `/usr/local/hadoop`:
       ```bash
       wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
       sudo tar -xzf hadoop-3.3.6.tar.gz -C /usr/local/
       sudo mv /usr/local/hadoop-3.3.6 /usr/local/hadoop
       sudo chown -R $USER:$USER /usr/local/hadoop
       ```
    2. Append Hadoop path variables into `~/.bashrc`:
       ```bash
       export HADOOP_HOME=/usr/local/hadoop
       export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
       ```
    3. Modify configuration files in `/usr/local/hadoop/etc/hadoop/`:
       - `hadoop-env.sh`: Add `export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64`
       - `core-site.xml`:
         ```xml
         <configuration>
             <property>
                 <name>fs.defaultFS</name>
                 <value>hdfs://localhost:9000</value>
             </property>
         </configuration>
         ```
       - `hdfs-site.xml`:
         ```xml
         <configuration>
             <property>
                 <name>dfs.replication</name>
                 <value>1</value>
             </property>
         </configuration>
         ```
       - `yarn-site.xml`: Add NodeManager configuration and disable virtual memory checks.
    4. Format HDFS filesystem metadata: `hdfs namenode -format`
    5. Run services: `start-dfs.sh` and `start-yarn.sh`
  - **Test Command**: `jps`
  - **DoD**: Processes list includes NameNode, DataNode, SecondaryNameNode, ResourceManager, and NodeManager.

- [x] **Task 0.6: Install Apache Hive 3.1.3 & Connect MySQL Metastore**
  - **Step-by-Step**:
    1. Download Hive 3.1.3 and extract to `/usr/local/hive`:
       ```bash
       wget https://archive.apache.org/dist/hive/hive-3.1.3/apache-hive-3.1.3-bin.tar.gz
       sudo tar -xzf apache-hive-3.1.3-bin.tar.gz -C /usr/local/
       sudo mv /usr/local/apache-hive-3.1.3-bin /usr/local/hive
       sudo chown -R $USER:$USER /usr/local/hive
       ```
    2. Add path variable mappings into `~/.bashrc`:
       ```bash
       export HIVE_HOME=/usr/local/hive
       export PATH=$PATH:$HIVE_HOME/bin
       ```
    3. Download MySQL JDBC connector `.jar` library (e.g., `mysql-connector-java-8.0.x.jar`) and copy into `/usr/local/hive/lib/`.
    4. Configure Hive metastore connections inside `/usr/local/hive/conf/hive-site.xml` to point to local MySQL instance.
    5. Execute metastore schema setup: `schematool -dbType mysql -initSchema`
  - **Test Command**: `hive -e "show databases;"`
  - **DoD**: Execution prints output with `default` table name workspace context.


---

### Cycle 1: Workspace & Dependency Sandbox (Environment Verification)
*Goal: Ensure any teammate can pull the repo and immediately configure their local WSL2/Ubuntu environment.*

- [x] **Task 1.1: Initialize Directory Tree**
  - **Implementation**: Create standard workspace layout (`bin/`, `src/`, `config/`, `data/`, `docs/`). Add a robust `.gitignore` file to ignore local databases (`data/db/`), HDFS metadata (`data/hdfs/`), Python virtual environments (`venv/`), environment variables (`.env`), and compiled Python files (`__pycache__/`).
  - **DoD**: Run `git status` showing clean working tree with only tracked template files.
- [x] **Task 1.2: Implement `bin/setup.sh`**
  - **Prerequisite Reading**: [GEMINI.md](file:///d:/Project/final-bdes/GEMINI.md), [ARCHITECTURE.md](file:///d:/Project/final-bdes/docs/ARCHITECTURE.md)
  - **Implementation Constraints**:
    - Do **NOT** install system-wide services like MySQL Server, MongoDB Server, Apache Hadoop, or Apache Hive.
    - Check if basic command-line dependencies are available (`python3`, `pip3`, `java`).
    - Initialize the Python virtual environment (`venv`) with `python3 -m venv venv`.
    - Activate `venv` and install/upgrade packages via `pip install -r requirements.txt`.
    - Run the schema migration script `src/ingest/init_db.py`. If services (MySQL or MongoDB) are not active/reachable, print clear warning guidelines and exit gracefully with status code `0`.
  - **Verification / Test**: Run `bash bin/setup.sh` on a clean terminal. Ensure it configures `venv` and runs without throwing fatal errors.
  - **DoD**: Execution of `bash bin/setup.sh` completes with exit code 0, creating the `venv` folder containing all installed python dependencies.
- [x] **Task 1.3: Implement `bin/run.sh`**
  - **Implementation**: Write a shell script (`#!/bin/bash`) that:
    1. Sets up local environment variables:
       ```bash
       export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
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

### Cycle 2: Scrapers & DBMS Ingestion (Data Staging)
*Goal: Crawl, fetch, clean, and load raw data into MongoDB and MySQL.*

- [x] **Task 2.1: Implement TripAdvisor Python Scraper**
  - **File**: `src/crawler/tripadvisor_job/` (Scrapy Spider or BeautifulSoup script)
  - **Implementation**: Parse restaurant name, rating, address, district, city, review count, and reviews array. Store output raw JSON in `src/crawler/tripadvisor_job/full_output.json`.
  - **DoD**: Exposes 1,334 restaurants and 44,000+ reviews in structured JSON.
- [x] **Task 2.2: Implement TheMealDB API Parser**
  - **File**: `src/crawler/fetch_mealdb.py`
  - **Implementation**: Loop letters A-Z on `search.php?f={}`. Flatten `strIngredient1` to `strIngredient20` into a unified `ingredients` array. Implement offline backup to read from `src/crawler/seed/meals.json` if network hits 403 or 429.
  - **DoD**: Generates structured `meals.json` seed containing 666 clean recipe records.
- [x] **Task 2.3: Setup Database Schema & Data Ingestion (ETL)**
  - **File**: `src/ingest/clean_and_populate.py`
  - **Implementation**: 
    1. Read raw JSON inputs. Clean rating strings (e.g., "4.5 of 5 bubbles" -> `4.5`) and review counts.
    2. Write documents into MongoDB database `sentiment_db` collections `restaurants` and `meals`.
    3. Write structured records into MySQL database `food_sentiment_db` tables `restaurants`, `reviews`, and `meals` (relational CSDL schema) using `mysql.connector`. Implement `DuplicateKeyError` and duplicate primary key checks.
  - **DoD**: Run the Python script and verify MongoDB collections and MySQL tables contain 1,334 restaurants and 666 meals with zero duplicate records.

---

### Cycle 3: Storage & Sync Pipelines (HDFS Synchronization)
*Goal: Sync the clean structures from MySQL/MongoDB to Hadoop HDFS.*

- [x] **Task 3.1: Create HDFS Sync Script**
  - **File**: `src/ingest/mysql_to_hdfs.py` / `src/ingest/mongo_to_hdfs.py` (or use Apache Sqoop)
  - **Implementation**: 
    * If Python: Connect to databases, query clean records, format them as JSON Lines (`.jsonl`), and stream them to HDFS:
      ```bash
      hdfs dfs -mkdir -p /data/raw
      hdfs dfs -put -f /tmp/restaurants.jsonl /data/raw/restaurants.jsonl
      ```
    * If Apache Sqoop: Run the sqoop command to import MySQL tables directly into HDFS directory `/data/raw/` in CSV or parquet format.
  - **DoD**: Run scripts and verify files exist on HDFS using `hdfs dfs -ls /data/raw/`.
- [x] **Task 3.2: Verify HDFS Integration & Hive Schema**
  - **Implementation**: Create Hive schemas inside `/usr/local/hive` or using HiveQL script `src/ingest/hive_schema.sql` to map the HDFS raw paths.
  - **DoD**: Execute `hive -f src/ingest/hive_schema.sql` and verify Hive tables can be queried via `hive -e "SELECT COUNT(*) FROM restaurants"`.

---

### Cycle 4: Analytics & MapReduce Engine (8 Analytical Jobs)
*Goal: Write and test 8 independent MapReduce jobs using Python's `mrjob` library running on YARN.*

- **Prerequisite Reading**: [GEMINI.md](file:///d:/Project/final-bdes/GEMINI.md), [ARCHITECTURE.md](file:///d:/Project/final-bdes/docs/ARCHITECTURE.md#3-database-schemas--collections)

- [x] **Task 4.1: MapReduce Job 1 - Average Rating by District**
  - **File**: [mr_rating_by_district.py](file:///d:/Project/final-bdes/src/mapreduce/mr_rating_by_district.py)
  - **Step-by-Step**:
    1. Read input JSON Lines representing restaurants.
    2. Extract `district` and `rating` from each record.
    3. Yield `(district, (rating, 1))` in the mapper.
    4. Aggregate ratings and counts in the reducer to calculate the mean rating.
  - **Test Command**: `python src/mapreduce/mr_rating_by_district.py data/raw/restaurants.jsonl`
  - **DoD**: Outputs list of districts with their average rating and review counts.

- [x] **Task 4.2: MapReduce Job 2 - Cuisine Frequency Counter**
  - **File**: [mr_cuisine_count.py](file:///d:/Project/final-bdes/src/mapreduce/mr_cuisine_count.py)
  - **Step-by-Step**:
    1. Read input JSON Lines representing meals.
    2. Map category or area tags to count individual cuisines.
    3. Yield `(cuisine, 1)` for each occurrence.
    4. Reduce by summing counts and sort the output by frequency.
  - **Test Command**: `python src/mapreduce/mr_cuisine_count.py data/raw/meals.jsonl`
  - **DoD**: Returns a sorted frequency distribution of cuisine/category tags.

- [x] **Task 4.3: MapReduce Job 3 - Price Category Distribution**
  - **File**: [mr_price_segment.py](file:///d:/Project/final-bdes/src/mapreduce/mr_price_segment.py)
  - **Step-by-Step**:
    1. Read TripAdvisor restaurants.
    2. Map `price_range` categories (e.g. Budget, Moderate, Luxury) to count values.
    3. Yield `(price_range, 1)`.
    4. Reducer sums up occurrences per price category.
  - **Test Command**: `python src/mapreduce/mr_price_segment.py data/raw/restaurants.jsonl`
  - **DoD**: Aggregates total restaurant count by price category.

- [x] **Task 4.4: MapReduce Job 4 - Review Sentiment Analysis**
  - **File**: [mr_sentiment_analysis.py](file:///d:/Project/final-bdes/src/mapreduce/mr_sentiment_analysis.py)
  - **Step-by-Step**:
    1. Parse the TripAdvisor nested reviews structure.
    2. Tokenize `comment` text.
    3. Perform keyword matching against a simple internal word list (e.g. positive: "good", "excellent", "delicious"; negative: "bad", "slow", "poor").
    4. Output `(restaurant_name, sentiment_score)` and calculate averages.
  - **Test Command**: `python src/mapreduce/mr_sentiment_analysis.py data/raw/restaurants.jsonl`
  - **DoD**: Emits sentiment scores and positive/negative ratios per restaurant.

- [x] **Task 4.5: MapReduce Job 5 - Meal-to-Restaurant Ingredient Matching**
  - **File**: [mr_ingredient_match.py](file:///d:/Project/final-bdes/src/mapreduce/mr_ingredient_match.py)
  - **Step-by-Step**:
    1. Read meals (ingredients list) and restaurant comments.
    2. Identify mentions of recipe ingredients in user comments.
    3. Map and reduce to calculate ingredient matches.
  - **Test Command**: `python src/mapreduce/mr_ingredient_match.py data/raw/restaurants.jsonl data/raw/meals.jsonl`
  - **DoD**: Yields match frequencies of meal ingredients in restaurant reviews.

- [x] **Task 4.6: MapReduce Job 6 - Top 10 Most Reviewed Restaurants**
  - **File**: [mr_top_reviewed.py](file:///d:/Project/final-bdes/src/mapreduce/mr_top_reviewed.py)
  - **Step-by-Step**:
    1. Map restaurant name/id to their `review_count`.
    2. Reducer collects all records, sorts them in descending order of `review_count`, and emits the top 10.
  - **Test Command**: `python src/mapreduce/mr_top_reviewed.py data/raw/restaurants.jsonl`
  - **DoD**: Outputs top 10 restaurants sorted by review count.

- [x] **Task 4.7: MapReduce Job 7 - Review Distribution Profile**
  - **File**: [mr_review_distribution.py](file:///d:/Project/final-bdes/src/mapreduce/mr_review_distribution.py)
  - **Step-by-Step**:
    1. Parse review ratings (1.0 to 5.0) from reviews array.
    2. Yield `(rating_score, 1)`.
    3. Sum count of reviews for each star rating level.
  - **Test Command**: `python src/mapreduce/mr_review_distribution.py data/raw/restaurants.jsonl`
  - **DoD**: Returns distribution counts of review stars.

- [x] **Task 4.8: MapReduce Job 8 - Delivery Status Analysis**
  - **File**: [mr_delivery_analysis.py](file:///d:/Project/final-bdes/src/mapreduce/mr_delivery_analysis.py)
  - **Step-by-Step**:
    1. Classify restaurants based on delivery keywords in comments/description.
    2. Correlate delivery availability with sentiment scores.
    3. Emit average rating or sentiment for delivery vs. non-delivery.
  - **Test Command**: `python src/mapreduce/mr_delivery_analysis.py data/raw/restaurants.jsonl`
  - **DoD**: Compares and outputs review sentiments between delivery-friendly and dine-in-only locations.

---

### Cycle 5: DevOps, Backup & Resilience
*Goal: Secure databases with backup recovery shell commands.*

- **Prerequisite Reading**: [TROUBLESHOOTING.md](file:///d:/Project/final-bdes/docs/TROUBLESHOOTING.md), [GEMINI.md](file:///d:/Project/final-bdes/GEMINI.md)

- [x] **Task 5.1: Automate MongoDB & MySQL Backup & Restore**
  - **Files**: [db_backup.sh](file:///d:/Project/final-bdes/src/backup/db_backup.sh) / [db_restore.sh](file:///d:/Project/final-bdes/src/backup/db_restore.sh)
  - **Step-by-Step**:
    1. Write `db_backup.sh` to run `mysqldump` and `mongodump`, outputting to a timestamped folder in `/data/backups/`.
    2. Write `db_restore.sh` using `mysql` client and `mongorestore` to load the specified dump.
  - **Test Command**: `bash src/backup/db_backup.sh` then check `/data/backups/`. Test recovery with `bash src/backup/db_restore.sh <backup_folder>`.
  - **DoD**: Backups generate files with non-zero sizes; restore successfully recovers mock data after simulated drops.

- [x] **Task 5.2: Port & Service Checks**
  - **File**: [run.sh](file:///d:/Project/final-bdes/bin/run.sh)
  - **Step-by-Step**:
    1. Integrate active socket detection checks (`ss -tln` or `netstat`) inside `bin/run.sh`.
    2. Check ports: 3306 (MySQL), 27017 (MongoDB), 9000 (HDFS), 10000 (Hive Server 2), and 8501 (Streamlit).
  - **Test Command**: `bash bin/run.sh` (should warn or launch required daemons).
  - **DoD**: Displays a clean text matrix table showing status (Active/Inactive) of each required service port.

---

### Cycle 6: Interactive GUI (Streamlit Web Dashboard)
*Goal: Build a beautiful, interactive frontend on WSL2 connecting to MySQL/Hive and triggering HDFS/MapReduce.*

- **Prerequisite Reading**: [GEMINI.md](file:///d:/Project/final-bdes/GEMINI.md#technical-stack-and-version-specifications), [ARCHITECTURE.md](file:///d:/Project/final-bdes/docs/ARCHITECTURE.md#25-data-warehouse-layer)

- [x] **Task 6.1: Build Streamlit Base Layout**
  - **File**: [app.py](file:///d:/Project/final-bdes/src/streamlit_app/app.py)
  - **Step-by-Step**:
    1. Create a multi-page sidebar layout (pages: Data Management/CRUD, Big Data Reports, Job Execution).
    2. Setup page settings, load styling headers (vibrant/dark mode theme).
  - **Test Command**: `streamlit run src/streamlit_app/app.py`
  - **DoD**: The application runs on port 8501 showing structured navigation tabs.

- [x] **Task 6.2: Create Full MySQL CRUD Interface**
  - **File**: [app.py](file:///d:/Project/final-bdes/src/streamlit_app/app.py)
  - **Step-by-Step**:
    1. Add forms to insert new restaurant listings into MySQL table `restaurants`.
    2. Query listings with search filters, edit attributes, and execute DELETE operations.
  - **Test Command**: Insert a test restaurant through the UI, edit its rating, and verify it updates in MySQL via terminal client.
  - **DoD**: Users can perform C, R, U, D operations directly on the screen with instant UI feedback.

- [x] **Task 6.3: Develop Visualization Page (6 Charts, 3 Types)**
  - **File**: [app.py](file:///d:/Project/final-bdes/src/streamlit_app/app.py)
  - **Step-by-Step**:
    1. Fetch aggregated MapReduce results from Apache Hive tables.
    2. Render 6 Plotly charts:
       - 2 Bar charts (e.g. ratings by district, sentiment by restaurant category).
       - 2 Pie/donut charts (cuisine frequency distribution, price segment breakdown).
       - 2 Scatter/line plots (reviews distribution curve, sentiment comparison).
  - **Test Command**: Load the reports tab and verify charts render with mock data.
  - **DoD**: Screen renders exactly 6 interactive Plotly charts across 3 different visualization types.

- [x] **Task 6.4: DevOps Operations Triggers**
  - **File**: [app.py](file:///d:/Project/final-bdes/src/streamlit_app/app.py)
  - **Step-by-Step**:
    1. Add UI buttons to trigger `db_backup.sh` and execution of MapReduce scripts using `subprocess`.
    2. Print stdout/stderr logs in the UI to notify the developer of success.
  - **Test Command**: Click the backup button and confirm a new sql/bson file is written.
  - **DoD**: Shell scripts run asynchronously from the Streamlit UI, returning successful exit status logs.

- [x] **Task 6.5: Connect Big Data Reports Page to Apache Hive (Live OLAP Queries)**
  - **Files**:
    - [app.py](file:///d:/Project/final-bdes/src/streamlit_app/app.py)
    - [hive_analytics.sql](file:///d:/Project/final-bdes/src/ingest/hive_analytics.sql) *(new)*
    - [hive_connector.py](file:///d:/Project/final-bdes/src/streamlit_app/hive_connector.py) *(new)*
  - **Background**: Task 6.3 completed 6 Plotly charts using mock/static DataFrames. The existing `run_hive_query()` function in `app.py` is already scaffolded but never called. The Hive external tables are already defined in `hive_schema.sql` and mapped to HDFS `/data/raw/`. This task replaces mock DataFrames with real Hive OLAP results.
  - **Step-by-Step**:
    1. **Create `src/ingest/hive_analytics.sql`**: Define 6 HiveQL analytic views/queries, each mapping to one Plotly chart in the Reports page:
       - `VIEW_rating_by_district`: `SELECT district, AVG(rating) AS avg_rating, COUNT(*) AS total FROM mysql_restaurants GROUP BY district ORDER BY avg_rating DESC`
       - `VIEW_cuisine_frequency`: `SELECT category, COUNT(*) AS cnt FROM mongodb_meals GROUP BY category ORDER BY cnt DESC`
       - `VIEW_price_segment`: `SELECT price_range, COUNT(*) AS cnt FROM mysql_restaurants GROUP BY price_range`
       - `VIEW_sentiment_by_price`: Join `mysql_reviews` + `mysql_restaurants`, compute AVG rating per `price_range`
       - `VIEW_review_distribution`: `SELECT rating, COUNT(*) AS cnt FROM mysql_reviews GROUP BY rating ORDER BY rating`
       - `VIEW_delivery_sentiment`: Classify delivery vs dine-in using keyword matching in `comment` text, compute AVG rating per type
    2. **Create `src/streamlit_app/hive_connector.py`**: A module encapsulating Hive connection logic with dual-mode support:
       - **Primary mode**: Use `pyhive` library (`from pyhive import hive`) to connect to HiveServer2 on `localhost:10000` (TCP JDBC-like connection, no subprocess needed).
       - **Fallback mode**: If `pyhive` connection fails (Hive not running), gracefully fall back to executing `hive -S -e` via `subprocess` (existing `run_hive_query` approach).
       - **Offline mode**: If both Hive modes fail, return pre-computed seed DataFrames from `src/crawler/seed/` JSON files so the UI never shows blank charts.
       - Export a single `query_hive(sql: str) -> pd.DataFrame` function.
    3. **Update `src/streamlit_app/app.py`** — `render_reports_page()` function:
       - Import `hive_connector.query_hive`
       - Replace each mock `pd.DataFrame({...})` with a call to `query_hive(<VIEW_SQL>)`
       - Add a status indicator (badge/spinner) showing "Live Hive Data" or "Offline Mode (Mock Data)" so the user knows the data source at a glance
       - Wrap all chart rendering in try/except to fall back to mock data gracefully if Hive query returns empty DataFrame
    4. **Update `requirements.txt`**: Add `pyhive[hive]` and `thrift` dependencies.
    5. **Validate `hive_schema.sql` tables**: Ensure `mysql_restaurants`, `mysql_reviews`, `mongodb_meals` external tables exist and point to valid HDFS paths before running analytics queries.
  - **Test Commands**:
    ```bash
    # Start HiveServer2 (WSL2)
    hive --service hiveserver2 &
    # Wait ~15 seconds then verify port
    ss -tln | grep 10000
    # Test pyhive connection
    python -c "from pyhive import hive; c = hive.connect('localhost'); print('OK')"
    # Run Streamlit
    streamlit run src/streamlit_app/app.py
    ```
  - **DoD**: The Big Data Reports page displays all 6 Plotly charts populated with live data queried from Apache Hive external tables (backed by HDFS). A data source indicator confirms "Live Hive Data" when HiveServer2 is running. Charts gracefully fall back to offline mock data when Hive is unavailable.

---

### Cycle 7: Verification, Slides & Demo Video
*Goal: Finalize reports, slide decks, and record a high-quality video following HCMUTE standards.*

- **Prerequisite Reading**: [REQUIREMENTS.md](file:///d:/Project/final-bdes/docs/REQUIREMENTS.md#4-yeu-cau-ve-bao-cao-slides--video)

- [ ] **Task 7.1: End-to-End Integration Testing**
  - **Step-by-Step**:
    1. Clone/deploy codebase on clean WSL2 instance.
    2. Execute `bin/setup.sh` to configure venv.
    3. Run `bin/run.sh` to start ingestion, sync, and GUI.
  - **DoD**: Zero terminal errors, with verification screenshot logs added to reports directory.

- [ ] **Task 7.2: Draft Slides & Document Report**
  - **Files**: Create report document and a slides presentation deck.
  - **DoD**: PDF report (20+ pages step-by-step layout) and 10-15 slides presentation prepared.

- [ ] **Task 7.3: Record and Edit Presentation Video**
  - **DoD**: Export a 7-minute Full HD demo video with Vietnamese subtitles, narration, background music, webcam feed, and HCMUTE branding watermarks.