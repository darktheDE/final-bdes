# Location Normalization Hotfix - 2026-06-15

## Problem observed

- `district_parsed` was mixing raw street fragments, hotel/building names, English `District N`, Vietnamese `Quận N`, and `Unknown`.
- Some records had empty `address`, while others only exposed useful admin info inside `address` instead of `district`.
- Streamlit plots that group by district were therefore fragmented and misleading.

## Decision

- Keep the existing infrastructure, 8 MapReduce jobs, and report layout.
- Fix the issue at the normalization layer only.
- Standardize location labels with one shared helper used by:
  - `src/ingest/init_db.py`
  - `src/ingest/import_tripadvisor.py`
  - `src/mapreduce/mr_rating_by_district.py`

## What changed

- Added `src/common/location_utils.py`.
- Added `src/mapreduce/location_utils.py` so Hadoop Streaming can ship the helper with the MapReduce job.
- Normalization now:
  - maps `District 1`, `Q.1`, `Quận 1` to `Quận 1`
  - falls back from `district` to `address` / `city` when needed
  - prefers explicit district matches, then ward matches
  - normalizes HCMC variants to `Ho Chi Minh City`
  - avoids grouping by street/hotel/floor fragments where possible

## Expected result

- Fewer fake district buckets in Hive/Streamlit reports.
- Better aggregation for Chart 1 and Chart 4 without changing Hadoop/Hive setup.
- Records that truly have no location metadata remain `Unknown`.
- The Hadoop job now imports `location_utils` from the local MapReduce folder and `run_all_jobs.py` ships it with `--file`.

## Recommended rerun sequence

```bash
python src/ingest/init_db.py
python src/ingest/mysql_to_hdfs.py
hive -f src/ingest/hive_schema.sql
hive -f src/ingest/hive_analytics.sql
python src/mapreduce/mr_rating_by_district.py -r hadoop hdfs:///data/raw/restaurants/restaurants.jsonl
```

If you want the usual full project path instead of selective refresh:

```bash
./bin/run.sh --jobs
```
