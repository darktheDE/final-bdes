"""
hive_connector.py
─────────────────
Centralized Hive query module for the Streamlit Big Data Reports page.

Connection strategy (3-layer fallback):
  Priority 1 — pyhive TCP: Connect to HiveServer2 on localhost:10000.
               Cleanest approach; no subprocess overhead; structured results.
  Priority 2 — subprocess CLI: Execute `hive -S -e "<sql>"` directly.
               Works without HiveServer2 daemon; parses TSV stdout.
  Priority 3 — Offline mock: Return pre-computed static DataFrames when
               Hive is completely unavailable (development / CI mode).

Public API:
  query_hive(sql: str, database: str = "food_sentiment_db") -> pd.DataFrame
  get_hive_status() -> str   # "live" | "subprocess" | "offline"
"""

from __future__ import annotations

import logging
import subprocess
from io import StringIO
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Maximum seconds to wait for a single Hive subprocess call
HIVE_QUERY_TIMEOUT = 180

# ──────────────────────────────────────────────────────────────────────────────
# Internal state: cache the detected connection mode so we don't re-probe
# HiveServer2 on every chart render.
# ──────────────────────────────────────────────────────────────────────────────
_HIVE_MODE: Optional[str] = None  # "live" | "subprocess" | "offline"

# Pre-computed representative mock DataFrames for fallback/offline display
_OFFLINE_MOCK_DATA: dict[str, pd.DataFrame] = {
    "view_rating_by_district": pd.DataFrame([
        {"district": "Quận 1", "avg_rating": 4.5, "total_count": 120},
        {"district": "Quận 3", "avg_rating": 4.3, "total_count": 95},
        {"district": "Quận 5", "avg_rating": 4.2, "total_count": 80},
        {"district": "Quận 7", "avg_rating": 4.4, "total_count": 110},
        {"district": "Quận 10", "avg_rating": 4.1, "total_count": 75},
        {"district": "Bình Thạnh", "avg_rating": 4.25, "total_count": 90},
        {"district": "Tân Bình", "avg_rating": 4.05, "total_count": 65},
    ]),
    "view_cuisine_frequency": pd.DataFrame([
        {"category": "Beef", "cnt": 150},
        {"category": "Chicken", "cnt": 120},
        {"category": "Pork", "cnt": 95},
        {"category": "Seafood", "cnt": 80},
        {"category": "Vegetarian", "cnt": 60},
        {"category": "Dessert", "cnt": 45},
    ]),
    "view_top_districts": pd.DataFrame([
        {"district": "Quận 1", "restaurant_count": 45, "avg_rating": 4.5},
        {"district": "Quận 7", "restaurant_count": 38, "avg_rating": 4.4},
        {"district": "Quận 3", "restaurant_count": 32, "avg_rating": 4.3},
        {"district": "Bình Thạnh", "restaurant_count": 28, "avg_rating": 4.25},
        {"district": "Quận 5", "restaurant_count": 25, "avg_rating": 4.2},
    ]),
    "view_rating_histogram": pd.DataFrame([
        {"rating_group": "4.5-5 sao (Xuất sắc)", "restaurant_count": 180},
        {"rating_group": "4-4.5 sao (Tốt)", "restaurant_count": 250},
        {"rating_group": "3-4 sao (Trung bình)", "restaurant_count": 120},
        {"rating_group": "2-3 sao (Dưới TB)", "restaurant_count": 45},
        {"rating_group": "1-2 sao (Kém)", "restaurant_count": 15},
    ]),
    "view_review_distribution": pd.DataFrame([
        {"stars": 1, "cnt": 15},
        {"stars": 2, "cnt": 30},
        {"stars": 3, "cnt": 85},
        {"stars": 4, "cnt": 280},
        {"stars": 5, "cnt": 620},
    ]),
    "view_delivery_sentiment": pd.DataFrame([
        {"service_type": "Delivery", "avg_rating": 4.250, "review_count": 450},
        {"service_type": "Dine-in", "avg_rating": 4.450, "review_count": 820},
    ]),
    "view_cuisine_area": pd.DataFrame([
        {"area": "Vietnamese", "meal_count": 24},
        {"area": "Italian", "meal_count": 18},
        {"area": "Chinese", "meal_count": 15},
        {"area": "Japanese", "meal_count": 12},
    ]),
}


def _probe_hiveserver2() -> bool:
    """Return True if HiveServer2 can execute a real JsonSerDe query via pyhive.

    Tests with an actual COUNT(*) query on a JsonSerDe external table — not just
    SELECT 1 — because HiveServer2 may connect fine but fail at MR execution time
    due to missing HCatalog jars in YARN container classpath.
    """
    try:
        from pyhive import hive  # type: ignore
        conn = hive.connect(host="localhost", port=10000, database="food_sentiment_db")
        cursor = conn.cursor()
        cursor.execute("set hive.exec.mode.local.auto=true")
        cursor.execute("set hive.exec.mode.local.auto.inputbytes.max=134217728")
        cursor.execute("set hive.aux.jars.path=file:///usr/local/hive/lib/hive-hcatalog-core-3.1.3.jar")
        # Real test: query a JsonSerDe external table
        cursor.execute("SELECT COUNT(*) FROM mysql_restaurants")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None and result[0] > 0
    except Exception as exc:
        logger.debug("pyhive probe failed: %s", exc)
        return False


def _get_hive_bin() -> str:
    """Resolve the absolute path to the hive CLI binary.

    Tries common install paths in case Streamlit is launched without
    /usr/local/hive/bin on PATH (e.g. via bin/run.sh subprocess).
    """
    import shutil
    # Try system PATH first
    hive_cmd = shutil.which("hive")
    if hive_cmd:
        return hive_cmd
    # Common install paths
    for candidate in [
        "/usr/local/hive/bin/hive",
        "/usr/bin/hive",
        "/opt/hive/bin/hive",
    ]:
        import os
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return "hive"  # fallback — will fail with FileNotFoundError if missing


def _probe_hive_cli() -> bool:
    """Return True if `hive` CLI binary is accessible and Hive metastore responds."""
    try:
        hive_bin = _get_hive_bin()
        result = subprocess.run(
            [hive_bin, "-S", "-e", "USE food_sentiment_db; SELECT COUNT(*) FROM mysql_restaurants;"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except Exception as exc:
        logger.debug("hive CLI probe failed: %s", exc)
        return False


def get_hive_status() -> str:
    """
    Detect and cache the best available Hive connection mode.

    Returns:
        "live"       — pyhive connected to HiveServer2 and can run JsonSerDe queries.
        "subprocess" — Hive CLI available and working.
        "offline"    — Neither mode available; will use mock data.
    """
    global _HIVE_MODE
    if _HIVE_MODE is not None:
        return _HIVE_MODE

    # Prefer subprocess CLI — it reliably uses local mode and avoids YARN classpath issues
    if _probe_hive_cli():
        _HIVE_MODE = "subprocess"
    elif _probe_hiveserver2():
        _HIVE_MODE = "live"
    else:
        _HIVE_MODE = "offline"

    logger.info("Hive connection mode resolved: %s", _HIVE_MODE)
    return _HIVE_MODE
    return _HIVE_MODE


def _query_via_pyhive(sql: str, database: str) -> pd.DataFrame:
    """Execute SQL through pyhive and return a DataFrame.

    Dùng cursor trực tiếp thay vì pd.read_sql() để đảm bảo lệnh SET
    hive.exec.mode.local.auto=true có hiệu lực trong cùng một session.
    (pd.read_sql tạo cursor mới bên trong, làm mất SET đã chạy trước đó.)
    """
    from pyhive import hive  # type: ignore

    conn = hive.connect(host="localhost", port=10000, database=database)
    try:
        cursor = conn.cursor()
        # SET phải chạy trên cùng cursor với query để có hiệu lực
        cursor.execute("set hive.exec.mode.local.auto=true")
        cursor.execute("set hive.exec.mode.local.auto.inputbytes.max=134217728")
        cursor.execute("set hive.exec.mode.local.auto.tasks.max=4")
        cursor.execute("set hive.aux.jars.path=file:///usr/local/hive/lib/hive-hcatalog-core-3.1.3.jar")
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            return pd.DataFrame()
        # Strip table-prefix from column names (pyhive may return "tablename.col")
        cols = [desc[0].split(".")[-1] for desc in cursor.description]
        return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()


def _query_via_subprocess(sql: str, database: str) -> pd.DataFrame:
    """Execute SQL through `hive -S -e` subprocess and parse TSV output."""
    hive_bin = _get_hive_bin()
    full_sql = f"set hive.exec.mode.local.auto=true; set hive.cli.print.header=true; USE {database}; {sql}"
    result = subprocess.check_output(
        [hive_bin, "-S", "-e", full_sql],
        stderr=subprocess.STDOUT,
        timeout=HIVE_QUERY_TIMEOUT,
    )
    output = result.decode("utf-8", errors="replace")

    # Filter out all noise lines — any line that isn't actual TSV data/header
    _NOISE_PREFIXES = (
        "SLF4J", "WARN", "INFO", "log4j", "Hive Session", "Logging",
        "OK", "Time taken", "your ",          # tty bogus screen size warning
        "Ended Job", "Error during", "Examining",
        "Task with", "Task ID", "URL:", "-----", "Diagnostic",
        "Caused by", "at ", "FAILED:", "Exception",
    )
    clean_lines = [
        line for line in output.split("\n")
        if line.strip()
        and not any(line.startswith(p) for p in _NOISE_PREFIXES)
        and "bogus" not in line
        and "expect trouble" not in line
    ]
    clean_output = "\n".join(clean_lines)

    if not clean_output.strip():
        return pd.DataFrame()

    df = pd.read_csv(StringIO(clean_output), sep="\t")
    # Strip table-prefix from column names (hive CLI may return "view.col")
    df.columns = [c.split(".")[-1] for c in df.columns]
    return df



# ──────────────────────────────────────────────────────────────────────────────
# Batch query: run all 6 analytics views in a SINGLE subprocess call.
# This avoids spawning 6 separate JVMs; instead one JVM does everything.
# ──────────────────────────────────────────────────────────────────────────────

# Sentinel string used to split multiple result blocks in one stdout stream
_BATCH_SEP = "---BATCH_SEP---"

# Ordered list of (view_key, sql) for the 6 analytics charts
BATCH_QUERIES: list[tuple[str, str]] = [
    ("view_rating_by_district",
     "SELECT district, avg_rating, total_count FROM view_rating_by_district LIMIT 20"),
    ("view_cuisine_frequency",
     "SELECT category, cnt FROM view_cuisine_frequency LIMIT 15"),
    ("view_top_districts",
     "SELECT district, restaurant_count, avg_rating FROM view_top_districts LIMIT 20"),
    ("view_rating_histogram",
     "SELECT rating_group, restaurant_count FROM view_rating_histogram"),
    ("view_review_distribution",
     "SELECT stars, cnt FROM view_review_distribution"),
    ("view_delivery_sentiment",
     "SELECT service_type, avg_rating, review_count FROM view_delivery_sentiment"),
]


def batch_query_all_views(use_mock_data: bool = False) -> dict[str, pd.DataFrame]:
    """
    Run all 6 analytics views and return a dict mapping view_key -> pd.DataFrame.

    Each view is queried individually to avoid batch parsing issues where one
    failing query contaminates subsequent queries' output.
    """
    if use_mock_data:
        return {key: df.copy() for key, df in _OFFLINE_MOCK_DATA.items()}

    mode = get_hive_status()

    if mode == "offline":
        return {key: pd.DataFrame() for key, _ in BATCH_QUERIES}

    results: dict[str, pd.DataFrame] = {}

    for key, sql in BATCH_QUERIES:
        try:
            if mode == "live":
                df = _query_via_pyhive(sql, "food_sentiment_db")
            else:
                df = _query_via_subprocess(sql, "food_sentiment_db")

            results[key] = df if (df is not None and not df.empty) else pd.DataFrame()
        except Exception as exc:
            logger.warning("Hive query failed for %s (%s mode): %s", key, mode, exc)
            import traceback
            logger.warning(traceback.format_exc())
            results[key] = pd.DataFrame()

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def query_hive(sql: str, database: str = "food_sentiment_db", use_mock_data: bool = False) -> pd.DataFrame:
    """
    Execute a HiveQL query and return results as a pandas DataFrame.

    Automatically selects the best available connection mode:
    - pyhive (live TCP connection to HiveServer2) if available.
    - subprocess hive CLI as fallback.
    - Pre-computed offline mock DataFrames as last resort (if enabled).

    Args:
        sql:           HiveQL SELECT statement or VIEW reference.
        database:      Hive database context (default: food_sentiment_db).
        use_mock_data: If True, return mock data immediately.

    Returns:
        pd.DataFrame with query results.
    """
    if use_mock_data:
        sql_lower = sql.lower()
        for key, df in _OFFLINE_MOCK_DATA.items():
            if key in sql_lower:
                return df.copy()
        return pd.DataFrame()

    mode = get_hive_status()

    if mode == "live":
        try:
            df = _query_via_pyhive(sql, database)
            if df is not None and not df.empty:
                return df
        except Exception as exc:
            logger.warning("pyhive query failed, trying subprocess: %s", exc)
            # Downgrade mode for subsequent calls
            global _HIVE_MODE
            _HIVE_MODE = "subprocess" if _probe_hive_cli() else "offline"
            mode = _HIVE_MODE

    if mode == "subprocess":
        try:
            df = _query_via_subprocess(sql, database)
            if df is not None and not df.empty:
                return df
        except Exception as exc:
            logger.warning("hive CLI query failed: %s", exc)
            _HIVE_MODE = "offline"
            mode = "offline"

    return pd.DataFrame()


def reset_connection_cache() -> None:
    """Force re-probing of Hive connection on next query_hive() call."""
    global _HIVE_MODE
    _HIVE_MODE = None
