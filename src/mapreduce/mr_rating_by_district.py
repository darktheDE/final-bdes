import json

from mrjob.job import MRJob

from location_utils import extract_admin_area


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
