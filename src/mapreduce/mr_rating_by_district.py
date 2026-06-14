from mrjob.job import MRJob
import json

class MRRatingByDistrict(MRJob):
    """Computes the average restaurant rating and review count by district."""
    
    def mapper(self, _, line):
        try:
            data = json.loads(line)
            district = data.get('district')
            rating = data.get('rating')
            if district and rating is not None:
                yield district.strip(), (float(rating), 1)
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
