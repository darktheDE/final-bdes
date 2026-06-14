-- ============================================================
-- hive_analytics.sql
-- Apache Hive OLAP Analytics Views for Big Data Reports page
-- Database: food_sentiment_db
--
-- Prerequisites:
--   hive_schema.sql must have been executed first to create:
--   mysql_restaurants, mysql_reviews, mongodb_meals external tables
--
-- Usage:
--   hive -f src/ingest/hive_analytics.sql
-- ============================================================

USE food_sentiment_db;

-- ────────────────────────────────────────────────────────────
-- View 1: Average Rating by District
-- Maps to: Bar Chart 1 — "Ratings per District"
-- Columns: district (STRING), avg_rating (DOUBLE), total_count (BIGINT)
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_rating_by_district;
CREATE VIEW view_rating_by_district AS
SELECT
    district,
    ROUND(AVG(rating), 2)   AS avg_rating,
    COUNT(*)                AS total_count
FROM mysql_restaurants
WHERE district IS NOT NULL
  AND district != ''
  AND district != 'null'
GROUP BY district
ORDER BY avg_rating DESC;


-- ────────────────────────────────────────────────────────────
-- View 2: Cuisine / Meal Category Frequency
-- Maps to: Donut Chart — "Cuisine Breakdown"
-- Columns: category (STRING), cnt (BIGINT)
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
-- View 3: Price Segment Breakdown
-- Maps to: Pie Chart — "Price Distribution"
-- Columns: price_range (STRING), cnt (BIGINT)
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_price_segment;
CREATE VIEW view_price_segment AS
SELECT
    CASE
        WHEN price_range IS NULL OR price_range = '' OR price_range = 'null'
            THEN 'Unknown'
        ELSE price_range
    END AS price_range,
    COUNT(*) AS cnt
FROM mysql_restaurants
GROUP BY
    CASE
        WHEN price_range IS NULL OR price_range = '' OR price_range = 'null'
            THEN 'Unknown'
        ELSE price_range
    END
ORDER BY cnt DESC;


-- ────────────────────────────────────────────────────────────
-- View 4: Average Review Sentiment (Rating) by Price Range
-- Maps to: Bar Chart 2 — "Sentiment Score by Price Category"
-- Columns: price_range (STRING), avg_sentiment (DOUBLE), review_count (BIGINT)
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_sentiment_by_price;
CREATE VIEW view_sentiment_by_price AS
SELECT
    CASE
        WHEN r.price_range IS NULL OR r.price_range = '' OR r.price_range = 'null'
            THEN 'Unknown'
        ELSE r.price_range
    END AS price_range,
    ROUND(AVG(rv.rating), 3)    AS avg_sentiment,
    COUNT(*)                    AS review_count
FROM mysql_reviews rv
JOIN mysql_restaurants r
  ON rv.restaurant_id = r.id
WHERE rv.rating IS NOT NULL
GROUP BY
    CASE
        WHEN r.price_range IS NULL OR r.price_range = '' OR r.price_range = 'null'
            THEN 'Unknown'
        ELSE r.price_range
    END
ORDER BY avg_sentiment DESC;


-- ────────────────────────────────────────────────────────────
-- View 5: Review Star Distribution
-- Maps to: Line Chart — "Star Distribution Curve"
-- Columns: stars (INT), cnt (BIGINT)
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_review_distribution;
CREATE VIEW view_review_distribution AS
SELECT
    CAST(FLOOR(rating) AS INT) AS stars,
    COUNT(*)                   AS cnt
FROM mysql_reviews
WHERE rating IS NOT NULL
  AND rating >= 1
  AND rating <= 5
GROUP BY CAST(FLOOR(rating) AS INT)
ORDER BY stars ASC;


-- ────────────────────────────────────────────────────────────
-- View 6: Delivery vs Dine-in Sentiment Comparison
-- Maps to: Scatter Chart — "Delivery Sentiment Comparison"
-- Columns: service_type (STRING), avg_rating (DOUBLE), review_count (BIGINT)
-- Classifies reviews by presence of delivery keywords in comment text
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS view_delivery_sentiment;
CREATE VIEW view_delivery_sentiment AS
SELECT
    CASE
        WHEN LOWER(comment) LIKE '%delivery%'
          OR LOWER(comment) LIKE '%giao h%ng%'
          OR LOWER(comment) LIKE '%ship%'
          OR LOWER(comment) LIKE '%take.?away%'
          OR LOWER(comment) LIKE '%takeaway%'
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
          OR LOWER(comment) LIKE '%take.?away%'
          OR LOWER(comment) LIKE '%takeaway%'
            THEN 'Delivery'
        ELSE 'Dine-in'
    END;
