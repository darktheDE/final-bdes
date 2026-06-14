from mrjob.job import MRJob
import json

class MRTopReviewed(MRJob):
    """Outputs the top 10 restaurants sorted by review count."""
    
    def mapper(self, _, line):
        try:
            data = json.loads(line)
            name = data.get('name')
            review_count = data.get('review_count')
            if name and review_count is not None:
                if isinstance(review_count, str):
                    import re
                    digits = re.sub(r'\D', '', review_count)
                    review_count = int(digits) if digits else 0
                else:
                    review_count = int(review_count)
                yield None, (review_count, name)
        except Exception:
            pass

    def reducer(self, _, values):
        # Collect all, sort descending by review count, take top 10
        sorted_restaurants = sorted(values, key=lambda x: x[0], reverse=True)
        for review_count, name in sorted_restaurants[:10]:
            yield name, review_count

if __name__ == '__main__':
    MRTopReviewed.run()
