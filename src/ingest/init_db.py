import os
import re
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

# ─────────────────────────────────────────────────────────────────────────────
# Data normalization helpers — align with actual scraped TripAdvisor data
# ─────────────────────────────────────────────────────────────────────────────

def _parse_review_count(value) -> int:
    """Parse review count from various formats.

    TripAdvisor thực tế trả về chuỗi như '(112)' hoặc '1,234'.
    Hàm này extract số nguyên từ chuỗi đó.

    Examples:
        '(112)'  -> 112
        '1,234'  -> 1234
        123      -> 123
        None     -> 0
    """
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    # Extract all digits from string (handles "(112)", "1,234", etc.)
    digits = re.sub(r'\D', '', str(value))
    return int(digits) if digits else 0


def _extract_district(address_or_district: str) -> str:
    """Extract district name from a raw address string."""
    if not address_or_district or str(address_or_district).strip().lower() in ('', 'null', 'none', 'unknown'):
        return 'Unknown'
        
    s = str(address_or_district).strip()
    
    parts = [p.strip() for p in s.split(',')]
    
    for part in reversed(parts):
        # Vietnamese prefix style
        match = re.search(r'(?i)\b(Qu[aậ]n|Huy[eệ]n|Th[aà]nh\s+ph[oố]|Q\.)\s+(.+)', part)
        if match:
            prefix = match.group(1)
            name = match.group(2).strip()
            if prefix.lower() == 'q.':
                prefix = 'Quận'
            return f"{prefix.capitalize()} {name}".strip()
            
        # English suffix style
        match = re.search(r'(?i)\b(.+)\s+District\b', part)
        if match:
            name = match.group(1).strip()
            return f"{name} District"
            
        # English prefix style
        match = re.search(r'(?i)\bDistrict\s+(.+)', part)
        if match:
            return f"District {match.group(1).strip()}"

    # Global fallback if no commas helped
    match = re.search(r'(?i)(Qu[aậ]n|Huy[eệ]n|Q\.|District)\s+([^,]+)', s)
    if match:
        prefix = match.group(1)
        name = match.group(2).strip()
        if prefix.lower() == 'q.':
            prefix = 'Quận'
        if prefix.lower() == 'district':
            return f"District {name}"
        return f"{prefix.capitalize()} {name}"
        
    match = re.search(r'(?i)([^,]+?)\s+District', s)
    if match:
        name = match.group(1).strip()
        words = name.split()
        if len(words) > 3:
            name = " ".join(words[-3:])
        return f"{name} District"

    if len(s) <= 50:
        return s
    return 'Unknown'


def _normalize_city(city_str: str) -> str:
    """Normalize city name, stripping zip codes and extra content.

    TripAdvisor thực tế trả về 'Ho Chi Minh City 70000 Vietnam'.

    Examples:
        'Ho Chi Minh City 70000 Vietnam' -> 'Ho Chi Minh City'
        'HCMC'                           -> 'HCMC'
        'Hà Nội'                         -> 'Hà Nội'
        None                             -> 'Unknown'
    """
    if not city_str or str(city_str).strip().lower() in ('', 'null', 'none'):
        return 'Unknown'

    s = str(city_str).strip()
    # Remove zip codes (4-6 digit numbers)
    s = re.sub(r'\b\d{4,6}\b', '', s)
    # Remove trailing country names commonly appended
    s = re.sub(r'\bVietnam\b', '', s, flags=re.IGNORECASE)
    # Clean extra whitespace
    s = re.sub(r'\s+', ' ', s).strip().strip(',').strip()
    return s if s else 'Unknown'


def _parse_review_rating(rating_val) -> float | None:
    """Parse individual review rating from various string formats.

    TripAdvisor thực tế trả về '5 of 5 bubbles' hoặc '4 of 5 bubbles'.

    Examples:
        '5 of 5 bubbles' -> 5.0
        '4 of 5 bubbles' -> 4.0
        '3.5'            -> 3.5
        4                -> 4.0
        None             -> None
    """
    if rating_val is None:
        return None
    if isinstance(rating_val, (int, float)):
        return float(rating_val)

    s = str(rating_val).strip()
    # Pattern: "X of 5 bubbles" or "X of 5"
    match = re.match(r'^(\d+(?:\.\d+)?)\s+of\s+\d+', s, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Pattern: plain number string
    match = re.match(r'^(\d+(?:\.\d+)?)$', s)
    if match:
        return float(match.group(1))

    return None


def _make_short_id(raw_id: str) -> str:
    """Create a stable, URL-safe short ID from the raw _id value.

    TripAdvisor dùng URL đầy đủ làm _id, VD:
    'https://www.tripadvisor.com/Restaurant_Review-g293925-d33215720-...'
    Hàm extract phần định danh (d\\d+) hoặc dùng hash ngắn.

    Returns:
        'rest_d33215720' nếu tìm thấy dNNNNNNNN trong URL,
        hoặc giữ nguyên raw_id (để tránh mất dữ liệu).
    """
    if not raw_id:
        return ''
    match = re.search(r'-(d\d+)-', str(raw_id))
    if match:
        return f"rest_{match.group(1)}"
    # If not a URL, return as-is (meal IDs, etc.)
    return str(raw_id)


# ─────────────────────────────────────────────────────────────────────────────
# Database setup
# ─────────────────────────────────────────────────────────────────────────────

def get_mysql_connection(create_db=False):
    """Establishes connection to MySQL. Optionally creates the database."""
    def _connect(config, create):
        try:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            if create:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB_NAME} "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
            cursor.close()
            conn.close()

            db_config = config.copy()
            db_config['database'] = MYSQL_DB_NAME
            return mysql.connector.connect(**db_config)
        except mysql.connector.Error as err:
            if err.errno == 1045 and config.get('password') == '':
                # Fallback to 'root' password
                fallback_config = config.copy()
                fallback_config['password'] = 'root'
                return _connect(fallback_config, create)
            print(f"[!] MySQL Connection Error: {err}")
            sys.exit(1)

    return _connect(MYSQL_CONFIG, create_db)


def create_tables(mysql_conn):
    """Creates the restaurants, reviews, and meals tables in MySQL.

    Lưu ý: field 'price_range' đã bị loại bỏ vì TripAdvisor không
    cung cấp thông tin giá theo phân khúc này.
    Field 'district_parsed' được thêm để lưu tên quận đã được extract.
    """
    cursor = mysql_conn.cursor()

    tables = {}
    tables['restaurants'] = (
        "CREATE TABLE IF NOT EXISTS `restaurants` ("
        "  `id` varchar(255) NOT NULL,"
        "  `name` varchar(255) NOT NULL,"
        "  `rating` float DEFAULT NULL,"
        "  `review_count` int DEFAULT 0,"
        "  `address` varchar(500) DEFAULT NULL,"
        "  `district` varchar(255) DEFAULT 'Unknown',"
        "  `district_parsed` varchar(100) DEFAULT 'Unknown',"
        "  `city` varchar(100) DEFAULT 'Unknown',"
        "  PRIMARY KEY (`id`)"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
    )

    tables['reviews'] = (
        "CREATE TABLE IF NOT EXISTS `reviews` ("
        "  `id` int NOT NULL AUTO_INCREMENT,"
        "  `restaurant_id` varchar(255) NOT NULL,"
        "  `user` varchar(255) DEFAULT 'Anonymous',"
        "  `rating` float DEFAULT NULL,"
        "  `comment` text DEFAULT NULL,"
        "  PRIMARY KEY (`id`),"
        "  KEY `fk_restaurant_id` (`restaurant_id`),"
        "  CONSTRAINT `fk_reviews_restaurants` FOREIGN KEY (`restaurant_id`) "
        "    REFERENCES `restaurants` (`id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
    )

    tables['meals'] = (
        "CREATE TABLE IF NOT EXISTS `meals` ("
        "  `id` varchar(255) NOT NULL,"
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


def _alter_tables_if_needed(mysql_conn):
    """Alter existing tables to match the new schema if they already exist.

    Xử lý trường hợp bảng đã tồn tại từ lần chạy trước với schema cũ
    (còn price_range, thiếu district_parsed).
    """
    cursor = mysql_conn.cursor()

    # Add district_parsed column if not exists
    try:
        cursor.execute(
            "ALTER TABLE restaurants "
            "ADD COLUMN `district_parsed` varchar(100) DEFAULT 'Unknown' "
            "AFTER `district`;"
        )
        print("[*] Added column 'district_parsed' to restaurants table.")
    except mysql.connector.Error as err:
        if err.errno == 1060:  # ER_DUP_FIELDNAME
            pass  # Column already exists, that's fine
        else:
            print(f"[!] Warning alter district_parsed: {err}")

    # Drop price_range column if exists
    try:
        cursor.execute("ALTER TABLE restaurants DROP COLUMN `price_range`;")
        print("[*] Dropped legacy column 'price_range' from restaurants table.")
    except mysql.connector.Error as err:
        if err.errno == 1091:  # ER_CANT_DROP_FIELD_OR_KEY
            pass  # Column doesn't exist, already clean
        else:
            print(f"[!] Warning drop price_range: {err}")

    mysql_conn.commit()
    cursor.close()


def migrate_data():
    """Migrates data from MongoDB collections to MySQL tables.

    Áp dụng các hàm normalize để đảm bảo data được chuẩn hóa trước
    khi lưu vào MySQL.
    """
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
    _alter_tables_if_needed(mysql_conn)
    cursor = mysql_conn.cursor()

    # ── 1. Migrate Restaurants & Reviews ─────────────────────────────────────
    print("[*] Migrating restaurants and reviews from MongoDB to MySQL...")
    mongo_rests = list(mongo_db['restaurants'].find({}))
    print(f"    Found {len(mongo_rests)} restaurants in MongoDB.")

    rest_insert_stmt = (
        "INSERT INTO restaurants "
        "  (id, name, rating, review_count, address, district, district_parsed, city) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE "
        "  name=VALUES(name), rating=VALUES(rating), "
        "  review_count=VALUES(review_count), address=VALUES(address), "
        "  district=VALUES(district), district_parsed=VALUES(district_parsed), "
        "  city=VALUES(city);"
    )

    review_insert_stmt = (
        "INSERT INTO reviews (restaurant_id, user, rating, comment) "
        "VALUES (%s, %s, %s, %s);"
    )

    rest_count = 0
    review_count = 0

    # Clean previous reviews to avoid accumulation during re-runs
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE reviews;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    for r in mongo_rests:
        # Build short, stable ID from URL or _id
        raw_id = r.get('_id', r.get('url', ''))
        r_id = _make_short_id(str(raw_id)) if raw_id else ''
        if not r_id:
            continue

        name = r.get('name') or 'Unnamed Restaurant'
        rating = r.get('rating')
        if rating is not None:
            try:
                rating = float(rating)
            except (ValueError, TypeError):
                rating = None

        # Normalize review_count: TripAdvisor returns "(112)" as string
        review_count_raw = r.get('review_count', 0)
        rev_count = _parse_review_count(review_count_raw)

        address = r.get('address') or ''

        # district field from TripAdvisor is actually the full street address
        district_raw = r.get('district', '') or ''
        district_parsed = _extract_district(district_raw)

        city_raw = r.get('city', '') or ''
        city = _normalize_city(city_raw)

        try:
            cursor.execute(rest_insert_stmt, (
                r_id, name, rating, rev_count,
                address, district_raw, district_parsed, city
            ))
            rest_count += 1
        except mysql.connector.Error as e:
            print(f"    [!] Skipping restaurant '{name}': {e}")
            continue

        # Reviews
        for rev in r.get('reviews', []):
            rev_user = rev.get('user', 'Anonymous') or 'Anonymous'
            # TripAdvisor review rating is "5 of 5 bubbles"
            rev_rating = _parse_review_rating(rev.get('rating'))
            rev_comment = rev.get('comment')

            try:
                cursor.execute(review_insert_stmt, (r_id, rev_user, rev_rating, rev_comment))
                review_count += 1
            except mysql.connector.Error as e:
                print(f"    [!] Skipping review for '{name}': {e}")

    # ── 2. Migrate Meals ──────────────────────────────────────────────────────
    print("[*] Migrating meals from MongoDB to MySQL...")
    mongo_meals = list(mongo_db['meals'].find({}))
    print(f"    Found {len(mongo_meals)} meals in MongoDB.")

    meal_insert_stmt = (
        "INSERT INTO meals (id, name, category, area, instructions, ingredients) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE "
        "  name=VALUES(name), category=VALUES(category), "
        "  area=VALUES(area), instructions=VALUES(instructions), "
        "  ingredients=VALUES(ingredients);"
    )

    meal_count = 0
    for m in mongo_meals:
        m_id = m.get('_id')
        if not m_id:
            continue
        m_name = m.get('name')
        if not m_name:
            continue

        category = m.get('category') or 'Unknown'
        area = m.get('area') or 'Unknown'
        instructions = m.get('instructions')

        # Ingredients stored as list → comma-separated string in MySQL
        ingredients_list = m.get('ingredients', [])
        if isinstance(ingredients_list, list):
            ingredients_str = ', '.join(str(i) for i in ingredients_list if i)
        else:
            ingredients_str = str(ingredients_list)

        try:
            cursor.execute(meal_insert_stmt, (
                m_id, m_name, category, area, instructions, ingredients_str
            ))
            meal_count += 1
        except mysql.connector.Error as e:
            print(f"    [!] Skipping meal '{m_name}': {e}")

    mysql_conn.commit()
    cursor.close()
    mysql_conn.close()
    mongo_client.close()

    print(f"\n[+] Successfully migrated to MySQL:")
    print(f"    - Restaurants : {rest_count}")
    print(f"    - Reviews     : {review_count}")
    print(f"    - Meals       : {meal_count}")

    # Print a few sample parsed districts for manual verification
    if rest_count > 0:
        print("\n[*] Sample district parsing results (first 5 restaurants):")
        sample_conn = get_mysql_connection()
        sample_cursor = sample_conn.cursor()
        sample_cursor.execute(
            "SELECT name, district, district_parsed, city "
            "FROM restaurants LIMIT 5;"
        )
        rows = sample_cursor.fetchall()
        for row in rows:
            print(f"    Name: {row[0][:30]:<32} | district_parsed: {row[2]:<20} | city: {row[3]}")
        sample_cursor.close()
        sample_conn.close()


def main():
    print("=== MySQL Database Setup ===")
    conn = get_mysql_connection(create_db=True)
    create_tables(conn)
    conn.close()
    migrate_data()
    print("\n[+] Database Setup Completed.")


if __name__ == "__main__":
    main()
