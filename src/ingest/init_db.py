import os
import sys
import pymongo
import mysql.connector
from mysql.connector import errorcode

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "sentiment_db"

# MySQL Configuration
MYSQL_CONFIG = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'port': 3306
}
MYSQL_DB_NAME = "food_sentiment_db"

def get_mysql_connection(create_db=False):
    """Establishes connection to MySQL. Optionally creates the database."""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        if create_db:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.close()
        conn.close()
        
        # Connect to the specific database
        config = MYSQL_CONFIG.copy()
        config['database'] = MYSQL_DB_NAME
        return mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        print(f"[!] MySQL Connection Error: {err}")
        sys.exit(1)

def create_tables(mysql_conn):
    """Creates the restaurants, reviews, and meals tables in MySQL."""
    cursor = mysql_conn.cursor()
    
    tables = {}
    tables['restaurants'] = (
        "CREATE TABLE IF NOT EXISTS `restaurants` ("
        "  `id` varchar(150) NOT NULL,"
        "  `name` varchar(255) NOT NULL,"
        "  `rating` float DEFAULT NULL,"
        "  `review_count` int DEFAULT 0,"
        "  `address` varchar(500) DEFAULT NULL,"
        "  `district` varchar(100) DEFAULT 'Unknown',"
        "  `city` varchar(100) DEFAULT 'Unknown',"
        "  `price_range` varchar(50) DEFAULT NULL,"
        "  PRIMARY KEY (`id`)"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
    )
    
    tables['reviews'] = (
        "CREATE TABLE IF NOT EXISTS `reviews` ("
        "  `id` int NOT NULL AUTO_INCREMENT,"
        "  `restaurant_id` varchar(150) NOT NULL,"
        "  `user` varchar(255) DEFAULT 'Anonymous',"
        "  `rating` float DEFAULT NULL,"
        "  `comment` text DEFAULT NULL,"
        "  PRIMARY KEY (`id`),"
        "  KEY `fk_restaurant_id` (`restaurant_id`),"
        "  CONSTRAINT `fk_reviews_restaurants` FOREIGN KEY (`restaurant_id`) REFERENCES `restaurants` (`id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
    )
    
    tables['meals'] = (
        "CREATE TABLE IF NOT EXISTS `meals` ("
        "  `id` varchar(150) NOT NULL,"
        "  `name` varchar(255) NOT NULL,"
        "  `category` varchar(100) DEFAULT 'Unknown',"
        "  `area` varchar(100) DEFAULT 'Unknown',"
        "  `instructions` text DEFAULT NULL,"
        "  `ingredients` text DEFAULT NULL,"
        "  PRIMARY KEY (`id`)"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
    )
    
    for table_name in ['restaurants', 'reviews', 'meals']:
        ddl = tables[table_name]
        try:
            print(f"[*] Creating table {table_name}...", end=" ")
            cursor.execute(ddl)
            print("OK")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(f"FAILED: {err.msg}")
                
    mysql_conn.commit()
    cursor.close()

def migrate_data():
    """Migrates data from MongoDB collections to MySQL tables."""
    print("\n[*] Connecting to MongoDB...")
    try:
        mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command('ping')
        mongo_db = mongo_client[MONGO_DB_NAME]
    except Exception as e:
        print(f"[!] MongoDB Connection Error: {e}")
        print("[!] Skipping data migration step. (Databases will only contain schema).")
        return

    mysql_conn = get_mysql_connection()
    cursor = mysql_conn.cursor()

    # 1. Migrate Restaurants & Reviews
    print("[*] Migrating restaurants and reviews from MongoDB to MySQL...")
    mongo_rests = list(mongo_db['restaurants'].find({}))
    print(f"    Found {len(mongo_rests)} restaurants in MongoDB.")
    
    rest_insert_stmt = (
        "INSERT INTO restaurants (id, name, rating, review_count, address, district, city, price_range) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE name=VALUES(name), rating=VALUES(rating), "
        "review_count=VALUES(review_count), address=VALUES(address), "
        "district=VALUES(district), city=VALUES(city);"
    )
    
    review_insert_stmt = (
        "INSERT INTO reviews (restaurant_id, user, rating, comment) "
        "VALUES (%s, %s, %s, %s);"
    )
    
    rest_count = 0
    review_count = 0
    
    # Clean previous reviews to avoid infinite accumulation during setup re-runs
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE reviews;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    for r in mongo_rests:
        # Prepare restaurant details
        # Fallback fields if MongoDB has missing attributes
        r_id = r.get('_id', r.get('url', ''))
        if not r_id:
            continue
        name = r.get('name')
        if not name:
            name = "Unnamed Restaurant"
        rating = r.get('rating')
        rev_count = r.get('review_count', 0)
        address = r.get('address')
        district = r.get('district', 'Unknown')
        city = r.get('city', 'Unknown')
        price_range = r.get('price_range')
        
        cursor.execute(rest_insert_stmt, (r_id, name, rating, rev_count, address, district, city, price_range))
        rest_count += 1
        
        # Reviews
        for rev in r.get('reviews', []):
            rev_user = rev.get('user', 'Anonymous')
            rev_rating = rev.get('rating')
            rev_comment = rev.get('comment')
            
            cursor.execute(review_insert_stmt, (r_id, rev_user, rev_rating, rev_comment))
            review_count += 1
            
    # 2. Migrate Meals
    print("[*] Migrating meals from MongoDB to MySQL...")
    mongo_meals = list(mongo_db['meals'].find({}))
    print(f"    Found {len(mongo_meals)} meals in MongoDB.")
    
    meal_insert_stmt = (
        "INSERT INTO meals (id, name, category, area, instructions, ingredients) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE name=VALUES(name), category=VALUES(category), "
        "area=VALUES(area), instructions=VALUES(instructions), ingredients=VALUES(ingredients);"
    )
    
    meal_count = 0
    for m in mongo_meals:
        m_id = m.get('_id')
        if not m_id:
            continue
        m_name = m.get('name')
        if not m_name:
            continue
        category = m.get('category', 'Unknown')
        area = m.get('area', 'Unknown')
        instructions = m.get('instructions')
        
        # Ingredients stored as list in MongoDB, save as comma-separated string in MySQL
        ingredients_list = m.get('ingredients', [])
        ingredients_str = ", ".join(ingredients_list) if isinstance(ingredients_list, list) else str(ingredients_list)
        
        cursor.execute(meal_insert_stmt, (m_id, m_name, category, area, instructions, ingredients_str))
        meal_count += 1

    mysql_conn.commit()
    cursor.close()
    mysql_conn.close()
    
    print(f"[+] Successfully migrated to MySQL:")
    print(f"    - Restaurants: {rest_count}")
    print(f"    - Reviews: {review_count}")
    print(f"    - Meals: {meal_count}")

def main():
    print("=== MySQL Database Setup ===")
    conn = get_mysql_connection(create_db=True)
    create_tables(conn)
    conn.close()
    migrate_data()
    print("[+] Database Setup Completed.")

if __name__ == "__main__":
    main()
