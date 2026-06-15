-- ============================================================
-- hive_analytics.sql
-- Apache Hive OLAP Analytics Views for Big Data Reports page
-- Database: food_sentiment_db
--
-- Prerequisites:
--   hive_schema.sql must have been executed first to create:
--   mysql_restaurants, mysql_reviews, mongodb_meals external tables
--
-- Views được thiết kế dựa trên data thực tế:
--   - Không dùng price_range (không có trong TripAdvisor data)
--   - Dùng district_parsed (tên quận đã được extract)
--   - rating review đã được parse sang FLOAT bởi init_db.py
--
-- Usage:
--   hive -f src/ingest/hive_analytics.sql
-- ============================================================

USE food_sentiment_db;

-- ────────────────────────────────────────────────────────────
-- View 1: Average Rating by District (Parsed)
-- Maps to: Bar Chart 1 — "Ratings per District"
-- Columns: district (STRING), avg_rating (DOUBLE), total_count (BIGINT)
-- Dùng district_parsed thay vì district thô để nhóm đúng theo quận
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_rating_by_district;
CREATE VIEW view_rating_by_district AS
SELECT
    district_parsed                  AS district,
    ROUND(AVG(rating), 2)            AS avg_rating,
    COUNT(*)                         AS total_count
FROM mysql_restaurants
WHERE district_parsed IS NOT NULL
  AND district_parsed != ''
  AND district_parsed != 'null'
  AND district_parsed != 'Unknown'
  AND rating IS NOT NULL
GROUP BY district_parsed
ORDER BY avg_rating DESC;


-- ────────────────────────────────────────────────────────────
-- View 2: Cuisine / Meal Category Frequency (from TheMealDB)
-- Maps to: Donut Chart — "Cuisine Category Breakdown"
-- Columns: category (STRING), cnt (BIGINT)
-- Phân tích phân bố loại món ăn trong dữ liệu TheMealDB
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_cuisine_frequency;
CREATE VIEW view_cuisine_frequency AS
SELECT
    category,
    COUNT(*) AS cnt
FROM mongodb_meals
WHERE category IS NOT NULL
  AND category != ''
  AND category != 'null'
GROUP BY category
ORDER BY cnt DESC;


-- ────────────────────────────────────────────────────────────
-- View 3: Restaurant Rating Histogram
-- Maps to: Bar Chart — "Phân bố nhà hàng theo nhóm sao"
-- Columns: rating_group (STRING), restaurant_count (BIGINT)
-- Thay thế view_price_segment (dùng price_range — không có trong data)
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_rating_histogram;
CREATE VIEW view_rating_histogram AS
SELECT
    CASE
        WHEN rating < 2.0 THEN '1-2 sao (Kem)'
        WHEN rating < 3.0 THEN '2-3 sao (Duoi TB)'
        WHEN rating < 4.0 THEN '3-4 sao (Trung binh)'
        WHEN rating < 4.5 THEN '4-4.5 sao (Tot)'
        WHEN rating <= 5.0 THEN '4.5-5 sao (Xuat sac)'
        ELSE 'Chua co danh gia'
    END AS rating_group,
    COUNT(*) AS restaurant_count
FROM mysql_restaurants
WHERE rating IS NOT NULL
GROUP BY
    CASE
        WHEN rating < 2.0 THEN '1-2 sao (Kem)'
        WHEN rating < 3.0 THEN '2-3 sao (Duoi TB)'
        WHEN rating < 4.0 THEN '3-4 sao (Trung binh)'
        WHEN rating < 4.5 THEN '4-4.5 sao (Tot)'
        WHEN rating <= 5.0 THEN '4.5-5 sao (Xuat sac)'
        ELSE 'Chua co danh gia'
    END
ORDER BY restaurant_count DESC;



-- ────────────────────────────────────────────────────────────
-- View 4: Top Districts by Restaurant Count
-- Maps to: Horizontal Bar — "Quận nào có nhiều nhà hàng nhất?"
-- Columns: district (STRING), restaurant_count (BIGINT), avg_rating (DOUBLE)
-- Thay thế view_sentiment_by_price (dùng price_range — không có trong data)
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_top_districts;
CREATE VIEW view_top_districts AS
SELECT
    district_parsed                   AS district,
    COUNT(*)                          AS restaurant_count,
    ROUND(AVG(rating), 2)             AS avg_rating
FROM mysql_restaurants
WHERE district_parsed IS NOT NULL
  AND district_parsed != 'Unknown'
  AND district_parsed != ''
GROUP BY district_parsed
ORDER BY restaurant_count DESC;


-- ────────────────────────────────────────────────────────────
-- View 5: Review Star Distribution
-- Maps to: Line Chart — "Phân phối số sao đánh giá"
-- Columns: stars (INT), cnt (BIGINT)
-- review.rating đã được parse thành FLOAT bởi init_db.py
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_review_distribution;
CREATE VIEW view_review_distribution AS
SELECT
    CAST(rating AS INT) AS stars,
    COUNT(*)            AS cnt
FROM mysql_reviews
WHERE rating IS NOT NULL
  AND rating >= 1
  AND rating <= 5
GROUP BY CAST(rating AS INT)
ORDER BY stars ASC;



-- ────────────────────────────────────────────────────────────
-- View 6: Delivery vs Dine-in Sentiment Comparison
-- Maps to: Scatter Chart — "Delivery Sentiment Comparison"
-- Columns: service_type (STRING), avg_rating (DOUBLE), review_count (BIGINT)
-- Phân loại review theo từ khóa liên quan đến delivery/giao hàng
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_delivery_sentiment;
CREATE VIEW view_delivery_sentiment AS
SELECT
    CASE
        WHEN LOWER(comment) LIKE '%delivery%'
          OR LOWER(comment) LIKE '%giao h%ng%'
          OR LOWER(comment) LIKE '%ship%'
          OR LOWER(comment) LIKE '%takeaway%'
          OR LOWER(comment) LIKE '%take away%'
          OR LOWER(comment) LIKE '%mang ve%'
          OR LOWER(comment) LIKE '%shopeefood%'
          OR LOWER(comment) LIKE '%grab food%'
            THEN 'Delivery'
        ELSE 'Dine-in'
    END AS service_type,
    ROUND(AVG(rating), 3) AS avg_rating,
    COUNT(*)              AS review_count
FROM mysql_reviews
WHERE comment IS NOT NULL
  AND comment != ''
  AND rating IS NOT NULL
GROUP BY
    CASE
        WHEN LOWER(comment) LIKE '%delivery%'
          OR LOWER(comment) LIKE '%giao h%ng%'
          OR LOWER(comment) LIKE '%ship%'
          OR LOWER(comment) LIKE '%takeaway%'
          OR LOWER(comment) LIKE '%take away%'
          OR LOWER(comment) LIKE '%mang ve%'
          OR LOWER(comment) LIKE '%shopeefood%'
          OR LOWER(comment) LIKE '%grab food%'
            THEN 'Delivery'
        ELSE 'Dine-in'
    END;


-- ────────────────────────────────────────────────────────────
-- View 7: Cuisine Area Distribution (TheMealDB)
-- Maps to: Map/Bar — "Phân bố vùng ẩm thực toàn cầu"
-- Columns: area (STRING), meal_count (BIGINT)
-- Mối liên hệ TheMealDB ↔ TripAdvisor: ingredients từ MealDB
-- được dùng trong mr_ingredient_match để match với review comments
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_cuisine_area;
CREATE VIEW view_cuisine_area AS
SELECT
    area,
    COUNT(*) AS meal_count
FROM mongodb_meals
WHERE area IS NOT NULL
  AND area != ''
  AND area != 'null'
GROUP BY area
ORDER BY meal_count DESC;
