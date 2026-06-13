-- Create Hive Database for the project
CREATE DATABASE IF NOT EXISTS food_sentiment_db;
USE food_sentiment_db;

-- 1. MongoDB TripAdvisor Restaurants Table (Nested Structure)
CREATE EXTERNAL TABLE IF NOT EXISTS mongodb_restaurants (
    id STRING,
    name STRING,
    rating FLOAT,
    review_count INT,
    address STRING,
    district STRING,
    city STRING,
    reviews ARRAY<STRUCT<`user`:STRING, rating:FLOAT, comment:STRING>>
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION '/data/raw/restaurants';

-- 2. MongoDB TheMealDB Meals Table (Nested Array)
CREATE EXTERNAL TABLE IF NOT EXISTS mongodb_meals (
    id STRING,
    name STRING,
    category STRING,
    area STRING,
    instructions STRING,
    ingredients ARRAY<STRING>
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION '/data/raw/meals';

-- 3. MySQL Restaurants Table (Normalized/Flat)
CREATE EXTERNAL TABLE IF NOT EXISTS mysql_restaurants (
    id STRING,
    name STRING,
    rating FLOAT,
    review_count INT,
    address STRING,
    district STRING,
    city STRING,
    price_range STRING
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION '/data/raw/mysql_restaurants';

-- 4. MySQL Reviews Table (Relational Reviews)
CREATE EXTERNAL TABLE IF NOT EXISTS mysql_reviews (
    id INT,
    restaurant_id STRING,
    `user` STRING,
    rating FLOAT,
    comment STRING
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION '/data/raw/mysql_reviews';

-- 5. MySQL Meals Table (Relational Meals)
CREATE EXTERNAL TABLE IF NOT EXISTS mysql_meals (
    id STRING,
    name STRING,
    category STRING,
    area STRING,
    instructions STRING,
    ingredients STRING
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION '/data/raw/mysql_meals';
