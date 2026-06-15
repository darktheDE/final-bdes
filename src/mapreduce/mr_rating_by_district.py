import json
import os
import sys

from mrjob.job import MRJob

# location_utils.py must be distributed to YARN workers via --file.
# Attempt import; define inline fallback so the job fails clearly if missing.
try:
    from location_utils import extract_admin_area
except ImportError:
    # Add the directory of this script to sys.path as a fallback
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    try:
        from location_utils import extract_admin_area
    except ImportError:
        def extract_admin_area(*args):
            return "Unknown"


def _extract_district(*location_parts: str) -> str:
    """Normalize location labels for consistent district/ward grouping."""
    return extract_admin_area(*location_parts)


class MRRatingByDistrict(MRJob):
    """Computes the average restaurant rating and review count by area."""

    def mapper(self, _, line):
        try:
            data = json.loads(line)
            rating = data.get("rating")
            if rating is None:
                return

            district = data.get("district_parsed") or _extract_district(
                data.get("district"),
                data.get("address"),
                data.get("city"),
            )
            if not district or district == "Unknown":
                return

            yield district, (float(rating), 1)
        except Exception:
            pass

    def combiner(self, district, ratings):
        total_rating = 0.0
        total_count = 0
        for rating, count in ratings:
            total_rating += rating
            total_count += count
        yield district, (total_rating, total_count)

    def reducer(self, district, ratings):
        total_rating = 0.0
        total_count = 0
        for rating, count in ratings:
            total_rating += rating
            total_count += count
        if total_count > 0:
            yield district, {
                "avg_rating": round(total_rating / total_count, 2),
                "restaurant_count": total_count,
            }


if __name__ == "__main__":
    MRRatingByDistrict.run()
