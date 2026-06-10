# System Architecture & Data Blueprint
## Food & Restaurant Sentiment Analysis System (Ubuntu 24.04 WSL2)

This document outlines the system architecture, component interactions, data pipeline flow, and precise database schemas. Both human developers and the Gemini AI Agent must align with this architectural blueprint during implementation.

---

## 1. System Architecture Overview

The system is built as a lightweight, modular Big Data pipeline designed to run natively on Ubuntu 24.04 LTS within a Windows Subsystem for Linux (WSL2) sandbox.

```text
+-------------------------------------------------------------+
|                     1. DATA SOURCE LAYER                    |
|  - TripAdvisor Restaurants (Crawl via requests/bs4)          |
|  - TheMealDB Cuisine Recipes (Fetch via REST API)           |
|  + Multi-source requirement met (BeautifulSoup & API)       |
+-------------------------------------------------------------+
                               | (Python Crawler with Seed Fallback)
                               v
+-------------------------------------------------------------+
|                     2. STAGING DATA LAYER                   |
|  - MongoDB Community Server 8.0 LTS (NoSQL on port 27017)   |
|  - Operations: CRUD, local staging, schema normalization     |
+-------------------------------------------------------------+
                               | (Sync Script: JSON Lines / .jsonl)
                               v
+-------------------------------------------------------------+
|                     3. BIG DATA STORAGE LAYER               |
|  - Hadoop Distributed File System (HDFS on port 9000)       |
|  - Runs native on WSL2 environment (no winutils.exe needed)  |
+-------------------------------------------------------------+
                               | (Python mrjob / Hadoop Streaming)
                               v
+-------------------------------------------------------------+
|                     4. DISTRIBUTED ANALYTICS                |
|  - 8 MapReduce Analytics Jobs executing on YARN/Hadoop      |
|  - Processing outputs saved back into HDFS                  |
+-------------------------------------------------------------+
                               | (Query / Read Operations)
                               v
+-------------------------------------------------------------+
|                     5. PRESENTATION LAYER (GUI)             |
|  - Streamlit Application (Local port 8501)                  |
|  - Interactive CRUD Forms, Plotly Charts, Job Triggers      |
+-------------------------------------------------------------+
```

---

## 2. Component Pipeline Details

### 2.1. Ingestion Layer
- **Source 1**: Web Crawler parses raw restaurant HTML from TripAdvisor.
- **Source 2**: HTTP client fetches recipe records from TheMealDB API.
  - *Data Enrichment Context*: TheMealDB provides standardized lists of ingredients and cuisines which are cross-referenced with TripAdvisor comments to detect recipe alignment and authenticate user feedback details.
- **Offline Fallback**: If network failures or rate-limits occur, a fallback router reads raw pre-saved text dumps inside `src/crawler/seed/`.
- **Cleaning**: Raw strings are parsed, datatypes cast (ratings to Float, counts to Int), and normalized into Python dictionaries.

### 2.2. NoSQL Staging Layer
- Cleaned objects are ingested into a local MongoDB server using `pymongo`.
- MongoDB acts as the primary Transactional Database (OLTP), handling everyday CRUD queries triggered by the Streamlit user interface.

### 2.3. Big Data Storage Layer (HDFS)
- MongoDB is not optimal for MapReduce. Therefore, data is synchronized to HDFS.
- **Data Export Format**: Documents are written to HDFS in **JSON Lines (`.jsonl`)** format. In this format, every single line in the text file represents exactly one valid, independent JSON object.
  - *Why?* Hadoop splits input data line-by-line. Standard JSON arrays break when split, whereas JSON Lines files are native to MapReduce streaming.
- **HDFS File Paths**:
  - Raw Restaurants: `hdfs://localhost:9000/data/raw/restaurants.jsonl`
  - Raw Meals: `hdfs://localhost:9000/data/raw/meals.jsonl`

### 2.4. MapReduce Processing Layer
- Jobs are written in Python using `mrjob`.
- When triggered, `mrjob` packages the Python script, invokes the Hadoop Streaming JAR, loads the JSON Lines file from HDFS, processes keys/values, and outputs text files into the HDFS directory: `hdfs://localhost:9000/data/processed/mapreduce/`.

---

## 3. Database Schemas & Collections

### 3.1. Collection: `restaurants`
Stored in MongoDB database `sentiment_db`, collection `restaurants`.

| Field Name | Datatype | Example | Description |
| :--- | :--- | :--- | :--- |
| `_id` | String / ObjectId | `"restaurant_12345"` | Unique Identifier |
| `name` | String | `"Pho Hung"` | Restaurant Name |
| `rating` | Double (Float) | `4.5` | Average rating (1.0 to 5.0) |
| `review_count` | Int32 (Integer) | `128` | Total number of reviews |
| `address` | String | `"123 Nguyen Trai, D1"` | Exact physical address |
| `district` | String | `"District 1"` | Standardized District name |
| `city` | String | `"HCMC"` | Standardized City name |
| `cuisines` | Array (Strings) | `["Vietnamese", "Soup"]` | Food genre labels |
| `price_range` | String | `"$$ - $$$"` | Affordable tier category |
| `reviews` | Array (Objects) | *See reviews sub-document below* | List of user feedback comments |

**`reviews` Sub-Document Structure:**
```json
{
  "user": "Alice",
  "rating": 5,
  "comment": "Excellent Pho! Very authentic taste."
}
```

### 3.2. Collection: `meals`
Stored in MongoDB database `sentiment_db`, collection `meals`.

| Field Name | Datatype | Example | Description |
| :--- | :--- | :--- | :--- |
| `_id` | String | `"meal_52772"` | Unique API Meal ID |
| `name` | String | `"Pho"` | Standardized Dish Name |
| `category` | String | `"Beef"` | Food Category |
| `area` | String | `"Vietnamese"` | Origin country/region |
| `instructions` | String | `"Boil bones for hours..."` | Recipe step-by-step |
| `ingredients` | Array (Strings) | `["Beef", "Star Anise"]` | Core recipe ingredients |

---

## 4. Integration & Control Flow

### 4.1. Streamlit as the Controller
The Streamlit GUI dashboard at `localhost:8501` (running inside WSL2, accessible from Windows host browser) acts as the command center:
1.  **Direct Read/Write**: Modifies MongoDB directly using a persistent `pymongo.MongoClient` instance (providing instant CRUD feedback).
2.  **DevOps Execution**: Triggers backups by running `mongodump` via Python's `subprocess` module.
3.  **Big Data Sync**: Triggers the sync pipeline via a subprocess to run the staging-to-storage HDFS data flow.
4.  **Analytics Invocation**: Triggers `mrjob` analytics. Streamlit runs the command `python src/mapreduce/mr_rating_by_district.py -r hadoop hdfs:///data/raw/restaurants.jsonl`, reads the standard output stream, and plots the calculated aggregates into Plotly graphs on the fly.