# System Architecture & Data Blueprint
## Food & Restaurant Sentiment Analysis System (Ubuntu 24.04 WSL2)

This document outlines the system architecture, component interactions, data pipeline flow, and precise database schemas. Both human developers and the Gemini AI Agent must align with this architectural blueprint.

---

## 1. Technology Stack & Version Specifications

To prevent compatibility issues and ensure reliable executions, the following specific versions are set as the project standard:

* **Java Platform**: `OpenJDK 8 LTS` (Java 8 is required for Apache Hive 3.x map-reduce tasks to avoid Kryo `NoSuchFieldException` errors)
* **Hadoop Ecosystem**: `Apache Hadoop 3.3.6 LTS` (Running in pseudo-distributed configuration)
* **Data Warehouse**: `Apache Hive 3.1.3` (Utilized to map HDFS output directories to HiveQL tables)
* **NoSQL Database**: `MongoDB Community Server 8.0 LTS` (Stores raw crawled TripAdvisor reviews)
* **Relational Database**: `MySQL Server 8.0` (Stores cleaned schemas for transactional and Streamlit CRUD)
* **Python Language**: `Python 3.10` / `Python 3.11` (Configured inside a virtual environment `venv` to prevent `distutils` package missing exceptions in Python 3.12+)
* **Web UI Framework**: `Streamlit 1.35.0`
* **Scraping Framework**: `Scrapy 2.11.0` / `BeautifulSoup4 4.12.0`

---

## 2. System Architecture Overview

The system is built as a lightweight, modular Big Data pipeline designed to run natively on Ubuntu 24.04 LTS within a Windows Subsystem for Linux (WSL2) sandbox.

```text
[ Ingestion Layer ]
  - TripAdvisor Scraper (Python BeautifulSoup)
  - TheMealDB API Client (HTTP Requests)
         |
         v
[ Staging & OLTP Layer ]
  - MongoDB (NoSQL)  --> Stores raw unstructured reviews (nested reviews array)
  - MySQL (Relational) -> Stores cleaned structured tables (restaurants, reviews, meals)
         |               + -> Direct Streamlit SQL queries & CRUD Operations
         v
[ Big Data Synchronization ]
  - Python Export scripts (or Apache Sqoop)
  - Writes structured data to HDFS in JSON Lines (.jsonl) or CSV format
         |
         v
[ Storage & processing (OLAP) ]
  - HDFS (Port 9000) -> Central Data Lake
  - YARN & Hadoop MapReduce (mrjob) -> Batch analytical job execution
         |
         v
[ Data Warehouse Layer ]
  - Apache Hive -> Maps processed output directories on HDFS into SQL tables
         |
         v
[ Presentation Layer (GUI) ]
  - Streamlit Application (Local port 8501)
  - Direct relational CRUD & SQL reports via MySQL connection
  - Big Data OLAP reporting via HiveQL / Apache Hive connection
```

---

## 2. Component Pipeline Details

### 2.1. Ingestion Layer
- **Source 1**: Web Crawler parses raw restaurant HTML from TripAdvisor.
- **Source 2**: HTTP client fetches recipe records from TheMealDB API.
  - *Data Enrichment Context*: TheMealDB provides standardized lists of ingredients and cuisines which are cross-referenced with TripAdvisor comments to detect recipe alignment and authenticate user feedback details.
- **Offline Fallback**: If network failures or rate-limits occur, a fallback router reads raw pre-saved text dumps inside `src/crawler/seed/`.
- **Cleaning**: Raw strings are parsed, datatypes cast (ratings to Float, counts to Int), and normalized into Python dictionaries.

### 2.2. Staging & Transactional Layer (OLTP)
To satisfy transactional requirements and support user interaction efficiently, a **Hybrid Database** approach is implemented:
- **MongoDB (NoSQL Document Store)**: Acts as the storage engine for raw, highly nested data. Best suited for TripAdvisor records containing nested arrays of review logs.
- **MySQL (Relational Database)**: Stores the cleaned and normalized datasets split into relational entities. Streamlit connects directly to MySQL using `mysql-connector-python` to perform fast **CRUD (Create, Read, Update, Delete)** operations. This avoids querying distributed systems like HDFS for single-record transactional operations.

### 2.3. Big Data Storage Layer (HDFS)
- For historical and large-scale analytics, structured tables from MySQL/MongoDB are exported and synchronized to HDFS.
- **Data Export Format**: Documents are written to HDFS in **JSON Lines (`.jsonl`)** format. In this format, every single line in the text file represents exactly one valid, independent JSON object.
  - *Why?* Hadoop splits input data line-by-line. Standard JSON arrays break when split, whereas JSON Lines files are native to MapReduce streaming.
- **HDFS File Paths**:
  - Raw Restaurants: `hdfs://localhost:9000/data/raw/restaurants/restaurants.jsonl`
  - Raw Meals: `hdfs://localhost:9000/data/raw/meals/meals.jsonl`

### 2.4. MapReduce Processing Layer (OLAP)
- Jobs are written in Python using `mrjob`.
- When triggered, `mrjob` packages the Python script, invokes the Hadoop Streaming JAR, loads the JSON Lines file from HDFS, processes keys/values, and outputs text files into the HDFS directory: `hdfs://localhost:9000/data/processed/mapreduce/`.

### 2.5. Data Warehouse Layer
- **Apache Hive** mounts the output directories generated by the MapReduce engine on HDFS and represents them as structured SQL tables. This allows the Streamlit frontend to execute SQL-like HiveQL queries instead of reading raw text files from HDFS directly, providing an industry-standard OLAP analytics reporting layer.

---

## 3. Database Schemas & Collections

### 3.1. MongoDB Collection: `restaurants`
Stored in MongoDB database `sentiment_db`, collection `restaurants`.

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
- `district` (full address) → `district_parsed` (extracted district name, e.g. `"Quận 1"`)
- `city` `"Ho Chi Minh City 70000 Vietnam"` → `"Ho Chi Minh City"`
- review `rating` `"5 of 5 bubbles"` → FLOAT `5.0`

### 3.2. MySQL Relational Database Schema
Stored in MySQL database `food_sentiment_db`.

#### Table: `restaurants`
| Field Name | Datatype | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(255) | Primary Key | Unique restaurant ID (rest_dXXXXXXXX) |
| `name` | VARCHAR(255) | Not Null | Restaurant name |
| `rating` | FLOAT | Default NULL | Rating score |
| `review_count` | INT | Default 0 | Total reviews count |
| `address` | VARCHAR(500) | Default NULL | Physical address |
| `district` | VARCHAR(255) | Default "Unknown" | Raw District string from TripAdvisor |
| `district_parsed` | VARCHAR(100) | Default "Unknown" | Parsed district (e.g. "Quận 1") |
| `city` | VARCHAR(100) | Default "Unknown" | City location |

#### Table: `reviews`
| Field Name | Datatype | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INT | Primary Key, Auto-Increment | Unique review ID |
| `restaurant_id` | VARCHAR(255) | Foreign Key -> `restaurants(id)` | Associated restaurant |
| `user` | VARCHAR(255) | Default "Anonymous" | Reviewer username |
| `rating` | FLOAT | Default NULL | Reviewer rating |
| `comment` | TEXT | Default NULL | User comment text |

#### Table: `meals`
| Field Name | Datatype | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(255) | Primary Key | Unique meal ID (meal_XXXXX) |
| `name` | VARCHAR(255) | Not Null | Standardized meal name |
| `category` | VARCHAR(100) | Default "Unknown" | Meal category |
| `area` | VARCHAR(100) | Default "Unknown" | Origin region |
| `instructions` | TEXT | Default NULL | Step-by-step instructions |
| `ingredients` | TEXT | Default NULL | Ingredients array (comma-separated) |

---

## 4. MapReduce Jobs (8 Analytics Jobs)

The system runs 8 independent analytical jobs implemented via `mrjob`:

| Job | Input Source | Description |
|-----|--------------|-------------|
| `mr_rating_by_district.py` | restaurants.jsonl | Average rating and total review counts grouped by `district_parsed` |
| `mr_cuisine_count.py` | meals.jsonl | Frequency count of meal categories & geographical areas |
| `mr_rating_bucket.py` | restaurants.jsonl | Count of restaurants in different rating groups (e.g. 4.5-5.0, 4.0-4.5) |
| `mr_sentiment_analysis.py` | restaurants.jsonl | Simple sentiment analysis of reviews to calculate positive/negative polarity |
| `mr_ingredient_match.py` | restaurants.jsonl | Matches ingredients from `meals` with review comments to find top mentioned ingredients |
| `mr_top_reviewed.py` | restaurants.jsonl | Finds the top 10 most-reviewed restaurants across the city |
| `mr_review_distribution.py` | restaurants.jsonl | Calculates the distribution percentage of star ratings (1 to 5 stars) |
| `mr_delivery_analysis.py` | restaurants.jsonl | Compares average rating of reviews mentioning "delivery/order" vs dine-in reviews |

---

## 5. Hive Analytics Views

Apache Hive creates external tables mapping the HDFS MapReduce outputs for SQL querying via Streamlit:

| Hive View / Table | Data Source |
|-------------------|-------------|
| `mr_rating_by_district` | HDFS: `/data/processed/mapreduce/rating_by_district` |
| `mr_cuisine_count` | HDFS: `/data/processed/mapreduce/cuisine_count` |
| `mr_rating_bucket` | HDFS: `/data/processed/mapreduce/rating_bucket` |
| `mr_sentiment_analysis` | HDFS: `/data/processed/mapreduce/sentiment_analysis` |
| `mr_ingredient_match` | HDFS: `/data/processed/mapreduce/ingredient_match` |
| `mr_top_reviewed` | HDFS: `/data/processed/mapreduce/top_reviewed` |
| `mr_review_distribution` | HDFS: `/data/processed/mapreduce/review_distribution` |
| `mr_delivery_analysis` | HDFS: `/data/processed/mapreduce/delivery_analysis` |