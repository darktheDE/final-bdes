# Project Master Plan: Food & Restaurant Sentiment Analysis System
## Roadmap, Modules, Cycles, and Tasks

This Master Plan divides our Native Windows Big Data project into structured, incremental development cycles. Each cycle contains granular tasks with a clear "Definition of Done" (DoD). 

---

## Development Strategy
1. **Incremental Execution**: One task must be fully completed, tested locally, and verified on Windows before moving to the next.
2. **AI-Assisted Work**: Use GEMINI CLI along with `/memory` commands to load this context. Ask the agent to implement specific tasks using: `Implement Task X.Y from MASTERPLAN.md`.
3. **Branching/State Tracking**: Update the `[ ]` checklist status to `[x]` as tasks are completed.

---

## Project Timeline Overview

| Milestone | Target Scope | Expected Deliverables |
| :--- | :--- | :--- |
| **Cycle 0** | Workspace & Dependency Sandbox | `setup.bat`, `run.bat` shell, directory tree setup |
| **Cycle 1** | Scrapers & MongoDB Ingestion | TripAdvisor scraper, API parser, raw database populated |
| **Cycle 2** | HDFS Sync Pipelines | Data migration script, HDFS data structures verified |
| **Cycle 3** | Analytics & MapReduce | 8 Python MapReduce analytics jobs (`mrjob`) |
| **Cycle 4** | DevOps, Backup & Recovery | Dump/Restore automation, system resilience scripts |
| **Cycle 5** | Streamlit Interactive GUI | Web Dashboard, 5+ plotly charts, full CRUD interface |
| **Cycle 6** | Validation, Video & Delivery | End-to-end integration test, slide deck, demo video |

---

## Detailed Cycles & Tasks

### Cycle 0: Workspace & Dependency Sandbox (Environment Verification)
*Goal: Ensure any teammate can pull the repo and immediately configure their local environment.*

- [ x] **Task 0.1: Initialize Directory Tree**
  - Create the exact directory tree as defined in `README.md` and `GEMINI.md`.
  - Create standard `.gitignore` to ignore local datasets, database runtimes, and system caches (`data/`, `__pycache__/`, `.env`).
- [ ] **Task 0.2: Implement `bin/setup.bat`**
  - Write a batch script to install Python dependencies from `requirements.txt`.
  - Auto-download compatible versions of `winutils.exe` and `hadoop.dll` directly to a local project directory (`tools/`).
  - Copy `hadoop.dll` to `C:\Windows\System32\` (or handle it locally).
- [ ] **Task 0.3: Implement `bin/run.bat` (Skeleton Mode)**
  - Write a batch script that sets up environment variables (`JAVA_HOME`, `HADOOP_HOME`) locally for the command session.
  - Test and output these paths in the shell to verify path resolutions without global registry pollution.

---

### Cycle 1: Scrapers & MongoDB Ingestion (Data Staging)
*Goal: Crawl, fetch, clean, and load raw data into MongoDB.*

- [x] **Task 1.1: Implement TripAdvisor Python Scraper**
  - File: `src/crawler/tripadvisor_job` (Scrapy Spider)
  - Implement parsing of restaurant profiles and user reviews.
  - Successfully extracted 1334 restaurants and 44,000+ reviews to `full_output.json` (acting as our primary local seed).
- [x] **Task 1.2: Implement TheMealDB API Parser**
  - File: `src/crawler/fetch_mealdb.py`
  - Fetch meal categories, regions, ingredients, and recipes. Include local JSON seed fallback.
- [x] **Task 1.3: Setup Database Schema & Data Cleaning**
  - File: `src/ingest/clean_and_populate.py`
  - Parse collected raw files, apply pandas/pyspark cleaning (remove duplicates, normalize dates, fill null values).
  - Populate MongoDB local collection `restaurants` and `meals` with structured JSON documents.

---

### Cycle 2: Storage & Sync Pipelines (HDFS Synchronization)
*Goal: Sync the clean relational/document structures from MongoDB to Hadoop HDFS.*

- [ ] **Task 2.1: Create HDFS Sync Script**
  - File: `src/ingest/mongo_to_hdfs.py`
  - Read data from MongoDB collections using PySpark or PyMongo.
  - Write data to HDFS at `hdfs://localhost:9000/data/raw/` in CSV or JSON format.
- [ ] **Task 2.2: Verify HDFS Integration**
  - Expand `bin/run.bat` to automatically start HDFS namenode/datanode services and execute the sync script.
  - Validate output files using command line queries: `hdfs dfs -ls /data/raw/`.

---

### Cycle 3: Analytics & MapReduce Engine (8 Analytical Jobs)
*Goal: Write and test 8 independent MapReduce jobs using Python's `mrjob` library.*

- [ ] **Task 3.1: MapReduce Job 1 - Average Rating by District**
  - File: `src/mapreduce/mr_rating_by_district.py`
  - Calculates average restaurant reviews and ratings for each district.
- [ ] **Task 3.2: MapReduce Job 2 - Cuisine Frequency Counter**
  - File: `src/mapreduce/mr_cuisine_count.py`
  - Counts which food genres/cuisines are most popular among restaurants.
- [ ] **Task 3.3: MapReduce Job 3 - Price Category Distribution**
  - File: `src/mapreduce/mr_price_segment.py`
  - Groups and counts restaurants into affordability tiers (Budget, Moderate, Luxury).
- [ ] **Task 3.4: MapReduce Job 4 - Sentiment Sentiment Analysis**
  - File: `src/mapreduce/mr_sentiment_analysis.py`
  - Evaluates review comments using simple keyword matching (e.g., "delicious", "bad", "slow") to output positive vs. negative ratios per restaurant.
- [ ] **Task 3.5: MapReduce Job 5 - Meal-to-Restaurant Ingredient Matching**
  - File: `src/mapreduce/mr_ingredient_match.py`
  - Correlates recipe ingredients from the `meals` collection with cuisine profiles of target restaurants.
- [ ] **Task 3.6: MapReduce Job 6 - Top 10 Most Reviewed Restaurants**
  - File: `src/mapreduce/mr_top_reviewed.py`
  - Performs a top-K analysis on review counts to identify local hotspot restaurants.
- [ ] **Task 3.7: MapReduce Job 7 - Review Distribution Profile**
  - File: `src/mapreduce/mr_review_distribution.py`
  - Aggregates rating frequencies across the standard 1-to-5 star scale.
- [ ] **Task 3.8: MapReduce Job 8 - Delivery Status & Active Restaurant Count**
  - File: `src/mapreduce/mr_delivery_analysis.py`
  - Computes counts of active delivery-supported restaurants versus dine-in locations.

---

### Cycle 4: DevOps, Backup & Resilience
*Goal: Secure data pipelines with simple recovery commands.*

- [ ] **Task 4.1: Automate MongoDB Backup & Restore**
  - File: `src/backup/db_backup.bat` / `src/backup/db_restore.bat`
  - Write commands executing `mongodump` and `mongorestore` to keep database snapshots inside `/data/backups/`.
- [ ] **Task 4.2: Add Health Checks in Start Scripts**
  - Update `bin/run.bat` to detect if MongoDB port 27017 is already blocked by another process and gracefully alert the user.

---

### Cycle 5: Interactive GUI (Streamlit Web Dashboard)
*Goal: Build a beautiful, interactive frontend on Windows connecting to MongoDB and triggering HDFS/MapReduce.*

- [ ] **Task 5.1: Build Streamlit Base Layout**
  - File: `src/streamlit_app/app.py`
  - Establish a multi-page dashboard layout using sidebars.
- [ ] **Task 5.2: Create Full CRUD Interface**
  - Provide interactive forms where users can **Create** new restaurants, **Read** current entries, **Update** cuisine tags, and **Delete** listings in real-time.
- [ ] **Task 5.3: Develop Visualization Page (5 Charts, 3 Types)**
  - Integrate interactive Plotly or Altair graphs:
    - *Type 1 (Bar Charts)*: Top-reviewed restaurants, average rating by district.
    - *Type 2 (Pie Charts)*: Cuisine distributions, price-tier metrics.
    - *Type 3 (Scatter/Map Plot or Line Chart)*: Geographic/district heat map of restaurant densities.
- [ ] **Task 5.4: Implement Trigger Operations**
  - Add interactive buttons in Streamlit to let users click and run:
    - Backup/Restore operations.
    - HDFS Synchronizations.
    - Hadoop MapReduce analysis triggers (and render the text results on screen).

---

### Cycle 6: Verification, Slides & Demo Video
*Goal: Finalize reports, slide decks, and record a high-quality video following HCMUTE standards.*

- [ ] **Task 6.1: End-to-End Integration Testing**
  - Clean the environment, pull the code onto another Windows machine, and run `bin/setup.bat` then `bin/run.bat` to verify zero-error execution.
- [ ] **Task 6.2: Draft Slides & Document Report**
  - Format the final report step-by-step (according to course templates).
  - Draft slides (10–15 slides) covering Architecture, MapReduce, and Streamlit results.
- [ ] **Task 6.3: Record and Edit Presentation Video**
  - Include HCMUTE IT Faculty Logo watermark throughout the video.
  - Record the voiceover/narration, add soft background music, and compile subtitles.
  - Ensure all team members introduce themselves on webcam at the start.
```