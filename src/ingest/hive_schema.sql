-- ============================================================
-- hive_schema.sql
-- Apache Hive External Table Definitions
-- Database: food_sentiment_db
--
-- Lưu ý về schema thực tế:
--   - TripAdvisor 'district' là chuỗi địa chỉ đường phố đầy đủ
--   - TripAdvisor review 'rating' là STRING dạng "5 of 5 bubbles"
--   - TripAdvisor 'review_count' là STRING dạng "(112)"
--   - Không có field price_range trong data TripAdvisor
--   - 'district_parsed' là tên quận đã được extract (do init_db.py xử lý)
--
-- Usage:
--   hive -f src/ingest/hive_schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS food_sentiment_db;
USE food_sentiment_db;

-- ────────────────────────────────────────────────────────────────────────────
-- 1. MongoDB TripAdvisor Restaurants Table (Raw Nested Structure)
--    Source: /data/raw/restaurants/restaurants.jsonl (exported by mongo_to_hdfs.py)
--
--    Phản ánh đúng schema thực tế từ TripAdvisor spider:
--    - 'district' chứa chuỗi địa chỉ thô (có thể là đường + quận)
--    - 'review_count' là INT sau khi parse từ "(112)"
--    - reviews.rating là FLOAT sau khi parse từ "5 of 5 bubbles"
-- ────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS mongodb_restaurants;
CREATE EXTERNAL TABLE IF NOT EXISTS mongodb_restaurants (
    id             STRING,
    name           STRING,
    rating         FLOAT,
    review_count   INT,
    address        STRING,
    district       STRING,
    city           STRING,
    reviews        ARRAY<STRUCT<`user`:STRING, rating:FLOAT, comment:STRING>>
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/data/raw/restaurants';


-- ────────────────────────────────────────────────────────────────────────────
-- 2. MongoDB TheMealDB Meals Table (Recipe Data)
--    Source: /data/raw/meals/meals.jsonl (exported by mongo_to_hdfs.py)
--
--    Schema TheMealDB chuẩn: ingredients là mảng tên nguyên liệu,
--    area là vùng ẩm thực (Turkish, British...), category là loại món ăn
-- ────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS mongodb_meals;
CREATE EXTERNAL TABLE IF NOT EXISTS mongodb_meals (
    id             STRING,
    name           STRING,
    category       STRING,
    area           STRING,
    instructions   STRING,
    ingredients    ARRAY<STRING>
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/data/raw/meals';


-- ────────────────────────────────────────────────────────────────────────────
-- 3. MySQL Restaurants Table (Normalized/Flat — exported by mysql_to_hdfs.py)
--    Đây là phiên bản đã normalize từ MongoDB:
--    - 'district_parsed' = tên quận đã extract (VD: "Quận 1")
--    - Không còn 'price_range' (field này không có trong data thực)
-- ────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS mysql_restaurants;
CREATE EXTERNAL TABLE IF NOT EXISTS mysql_restaurants (
    id               STRING,
    name             STRING,
    rating           FLOAT,
    review_count     INT,
    address          STRING,
    district         STRING,
    district_parsed  STRING,
    city             STRING
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/data/raw/mysql_restaurants';


-- ────────────────────────────────────────────────────────────────────────────
-- 4. MySQL Reviews Table (Relational Reviews)
--    Source: /data/raw/mysql_reviews/reviews.jsonl
--    'rating' ở đây đã được parse sang FLOAT bởi init_db.py
-- ────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS mysql_reviews;
CREATE EXTERNAL TABLE IF NOT EXISTS mysql_reviews (
    id              INT,
    restaurant_id   STRING,
    `user`          STRING,
    rating          FLOAT,
    comment         STRING
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/data/raw/mysql_reviews';


-- ────────────────────────────────────────────────────────────────────────────
-- 5. MySQL Meals Table (Relational Meals — flat version of MongoDB meals)
--    'ingredients' là chuỗi comma-separated (VD: "Garlic, Onion, Pepper")
-- ────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS mysql_meals;
CREATE EXTERNAL TABLE IF NOT EXISTS mysql_meals (
    id             STRING,
    name           STRING,
    category       STRING,
    area           STRING,
    instructions   STRING,
    ingredients    STRING
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/data/raw/mysql_meals';
