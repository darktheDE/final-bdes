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


def _probe_hiveserver2() -> bool:
    """Return True if HiveServer2 is reachable on localhost:10000 via pyhive."""
    try:
        from pyhive import hive  # type: ignore
        conn = hive.connect(host="localhost", port=10000, database="food_sentiment_db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True
    except Exception as exc:
        logger.debug("pyhive probe failed: %s", exc)
        return False


def _probe_hive_cli() -> bool:
    """Return True if `hive` CLI binary is accessible and Hive metastore responds."""
    try:
        result = subprocess.run(
            ["hive", "-S", "-e", "USE food_sentiment_db; SELECT 1;"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except Exception as exc:
        logger.debug("hive CLI probe failed: %s", exc)
        return False


def get_hive_status() -> str:
    """
    Detect and cache the best available Hive connection mode.

    Returns:
        "live"       — pyhive connected to HiveServer2 successfully.
        "subprocess" — Hive CLI available but HiveServer2 not running.
        "offline"    — Neither mode available; will use mock data.
    """
    global _HIVE_MODE
    if _HIVE_MODE is not None:
        return _HIVE_MODE

    if _probe_hiveserver2():
        _HIVE_MODE = "live"
    elif _probe_hive_cli():
        _HIVE_MODE = "subprocess"
    else:
        _HIVE_MODE = "offline"

    logger.info("Hive connection mode resolved: %s", _HIVE_MODE)
    return _HIVE_MODE


def _query_via_pyhive(sql: str, database: str) -> pd.DataFrame:
    """Execute SQL through pyhive and return a DataFrame."""
    from pyhive import hive  # type: ignore

    conn = hive.connect(host="localhost", port=10000, database=database)
    try:
        # Bật chế độ Local Mode để Hive tự xử lý SQL trong RAM
        # Giúp tránh đẩy Job lên YARN gây lỗi "return code 2" do thiếu RAM/Java conflict
        cursor = conn.cursor()
        cursor.execute("set hive.exec.mode.local.auto=true")
        
        df = pd.read_sql(sql, conn)
        # Strip table-prefix from column names (pyhive may return "tablename.col")
        df.columns = [c.split(".")[-1] for c in df.columns]
        return df
    finally:
        conn.close()


def _query_via_subprocess(sql: str, database: str) -> pd.DataFrame:
    """Execute SQL through `hive -S -e` subprocess and parse TSV output."""
    full_sql = f"set hive.cli.print.header=true; USE {database}; {sql}"
    result = subprocess.check_output(
        ["hive", "-S", "-e", full_sql],
        stderr=subprocess.STDOUT,
        timeout=HIVE_QUERY_TIMEOUT,
    )
    output = result.decode("utf-8", errors="replace")

    # Filter out SLF4J noise, Hadoop INFO lines, and blank lines
    clean_lines = [
        line for line in output.split("\n")
        if line.strip()
        and not line.startswith("SLF4J")
        and not line.startswith("WARN")
        and not line.startswith("INFO")
        and not line.startswith("log4j")
        and not line.startswith("Hive Session")
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
    ("view_price_segment",
     "SELECT price_range, cnt FROM view_price_segment"),
    ("view_sentiment_by_price",
     "SELECT price_range, avg_sentiment, review_count FROM view_sentiment_by_price"),
    ("view_review_distribution",
     "SELECT stars, cnt FROM view_review_distribution"),
    ("view_delivery_sentiment",
     "SELECT service_type, avg_rating, review_count FROM view_delivery_sentiment"),
]


def batch_query_all_views() -> dict[str, pd.DataFrame]:
    """
    Run all 6 analytics views in a single Hive subprocess call.

    Returns a dict mapping view_key -> pd.DataFrame.
    Falls back to mock data for any view that fails to parse.
    Falls back entirely to mock data if subprocess fails.
    """
    mode = get_hive_status()

    if mode == "offline":
        return {key: _MOCK_DATA[key].copy() for key, _ in BATCH_QUERIES}

    if mode == "live":
        # pyhive: still run individually (connection reuse is handled by the driver)
        results: dict[str, pd.DataFrame] = {}
        for key, sql in BATCH_QUERIES:
            try:
                df = _query_via_pyhive(sql, "food_sentiment_db")
                results[key] = df if not df.empty else _MOCK_DATA[key].copy()
            except Exception as exc:
                logger.warning("pyhive batch query failed for %s: %s", key, exc)
                results[key] = _MOCK_DATA[key].copy()
        return results

    # subprocess mode: build one big script with SELECT statements separated
    # by a !echo sentinel so we can split the output back into 6 blocks.
    sql_parts = []
    for i, (key, sql) in enumerate(BATCH_QUERIES):
        sql_parts.append(f"set hive.cli.print.header=true;")
        sql_parts.append(f"{sql};")
        if i < len(BATCH_QUERIES) - 1:
            sql_parts.append(f"!echo {_BATCH_SEP};")

    full_sql = f"USE food_sentiment_db; " + " ".join(sql_parts)

    try:
        proc = subprocess.run(
            ["hive", "-S", "-e", full_sql],
            capture_output=True,
            text=True,
            timeout=HIVE_QUERY_TIMEOUT,
        )
        raw = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        logger.warning("Batch Hive query timed out after %ds, using mock data", HIVE_QUERY_TIMEOUT)
        return {key: _MOCK_DATA[key].copy() for key, _ in BATCH_QUERIES}
    except Exception as exc:
        logger.warning("Batch Hive query failed: %s, using mock data", exc)
        return {key: _MOCK_DATA[key].copy() for key, _ in BATCH_QUERIES}

    # Split output on sentinel
    blocks = raw.split(_BATCH_SEP)

    results = {}
    for i, (key, _) in enumerate(BATCH_QUERIES):
        block = blocks[i] if i < len(blocks) else ""
        # Filter noise
        clean_lines = [
            line for line in block.split("\n")
            if line.strip()
            and not line.startswith("SLF4J")
            and not line.startswith("WARN")
            and not line.startswith("INFO")
            and not line.startswith("log4j")
            and not line.startswith("Hive Session")
            and not line.startswith("Logging")
            and not line.startswith("OK")
            and not line.startswith("Time taken")
        ]
        clean_block = "\n".join(clean_lines)
        try:
            if clean_block.strip():
                df = pd.read_csv(StringIO(clean_block), sep="\t")
                df.columns = [c.split(".")[-1] for c in df.columns]
                results[key] = df if not df.empty else _MOCK_DATA[key].copy()
            else:
                results[key] = _MOCK_DATA[key].copy()
        except Exception as exc:
            logger.warning("Failed to parse block for %s: %s", key, exc)
            results[key] = _MOCK_DATA[key].copy()

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Offline mock DataFrames — one per view, mirrors expected Hive output schema
# ──────────────────────────────────────────────────────────────────────────────

_MOCK_DATA: dict[str, pd.DataFrame] = {
    "view_rating_by_district": pd.DataFrame({
        "district": ["Quận 1", "Quận 3", "Quận 5", "Bình Thạnh", "Quận 7",
                     "Tân Bình", "Quận 10", "Phú Nhuận"],
        "avg_rating": [4.35, 4.28, 4.10, 4.20, 4.45, 4.15, 4.05, 4.30],
        "total_count": [312, 198, 87, 145, 203, 134, 76, 110],
    }),
    "view_cuisine_frequency": pd.DataFrame({
        "category": ["Seafood", "Chicken", "Beef", "Vegetarian", "Pork",
                     "Pasta", "Dessert", "Miscellaneous", "Lamb", "Side"],
        "cnt": [85, 78, 65, 52, 47, 43, 38, 35, 24, 18],
    }),
    "view_price_segment": pd.DataFrame({
        "price_range": ["Budget", "Moderate", "Luxury", "Unknown"],
        "cnt": [487, 612, 158, 77],
    }),
    "view_sentiment_by_price": pd.DataFrame({
        "price_range": ["Luxury", "Moderate", "Budget", "Unknown"],
        "avg_sentiment": [4.52, 4.21, 3.95, 3.80],
        "review_count": [8423, 24156, 18934, 3201],
    }),
    "view_review_distribution": pd.DataFrame({
        "stars": [1, 2, 3, 4, 5],
        "cnt": [612, 1478, 5834, 18920, 22450],
    }),
    "view_delivery_sentiment": pd.DataFrame({
        "service_type": ["Dine-in", "Delivery"],
        "avg_rating": [4.22, 3.98],
        "review_count": [41830, 7464],
    }),
}


def _get_mock(view_name: str) -> pd.DataFrame:
    """Return pre-computed mock DataFrame for the given view name."""
    for key, df in _MOCK_DATA.items():
        if key in view_name.lower():
            return df.copy()
    return pd.DataFrame()


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def query_hive(sql: str, database: str = "food_sentiment_db") -> pd.DataFrame:
    """
    Execute a HiveQL query and return results as a pandas DataFrame.

    Automatically selects the best available connection mode:
    - pyhive (live TCP connection to HiveServer2) if available.
    - subprocess hive CLI as fallback.
    - Pre-computed offline mock DataFrames as last resort.

    Args:
        sql:      HiveQL SELECT statement or VIEW reference.
        database: Hive database context (default: food_sentiment_db).

    Returns:
        pd.DataFrame with query results. Never raises; returns empty
        DataFrame or mock data on any failure.
    """
    mode = get_hive_status()

    if mode == "live":
        try:
            return _query_via_pyhive(sql, database)
        except Exception as exc:
            logger.warning("pyhive query failed, trying subprocess: %s", exc)
            # Downgrade mode for subsequent calls
            global _HIVE_MODE
            _HIVE_MODE = "subprocess" if _probe_hive_cli() else "offline"
            mode = _HIVE_MODE

    if mode == "subprocess":
        try:
            return _query_via_subprocess(sql, database)
        except Exception as exc:
            logger.warning("hive CLI query failed, using mock: %s", exc)
            _HIVE_MODE = "offline"
            mode = "offline"

    # mode == "offline"
    return _get_mock(sql)


def reset_connection_cache() -> None:
    """Force re-probing of Hive connection on next query_hive() call."""
    global _HIVE_MODE
    _HIVE_MODE = None
