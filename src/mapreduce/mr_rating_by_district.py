import re
from mrjob.job import MRJob
import json

def _extract_district(address_or_district: str) -> str:
    """Extract district name from a raw address string."""
    if not address_or_district or str(address_or_district).strip().lower() in ('', 'null', 'none', 'unknown'):
        return 'Unknown'
    s = str(address_or_district).strip()
    match = re.search(r'(Qu[aậ]n\s+\d+|Qu[aậ]n\s+[A-Za-zÀ-ỹ\s]+|Huy[eệ]n\s+[A-Za-zÀ-ỹ\s]+|Th[aà]nh\s+ph[oố]\s+[A-Za-zÀ-ỹ\s]+)', s, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r'Q\.\s*([A-Za-zÀ-ỹ0-9\s]+)', s)
    if match:
        return f"Quận {match.group(1).strip()}"
    match = re.search(r'District\s+(\d+|[A-Za-z\s]+)', s, re.IGNORECASE)
    if match:
        return f"District {match.group(1).strip()}"
    if len(s) <= 50:
        return s
    return 'Unknown'

class MRRatingByDistrict(MRJob):
    """Computes the average restaurant rating and review count by district."""
    
    def mapper(self, _, line):
        try:
            data = json.loads(line)
            district_raw = data.get('district')
            rating = data.get('rating')
            if district_raw and rating is not None:
                district = _extract_district(district_raw)
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
                'avg_rating': round(total_rating / total_count, 2),
                'restaurant_count': total_count
            }

if __name__ == '__main__':
    MRRatingByDistrict.run()
