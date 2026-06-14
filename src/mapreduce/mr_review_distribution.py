from mrjob.job import MRJob
import json

class MRReviewDistribution(MRJob):
    """Returns distribution counts of review stars (1.0 to 5.0)."""
    
    def mapper(self, _, line):
        try:
            data = json.loads(line)
            reviews = data.get('reviews', [])
            for r in reviews:
                rating = r.get('rating')
                if rating is not None:
                    if isinstance(rating, str):
                        import re
                        match = re.search(r'(\d+(\.\d+)?)', rating)
                        rating = float(match.group(1)) if match else None
                    if rating is not None:
                        yield float(rating), 1
        except Exception:
            pass

    def combiner(self, rating, counts):
        yield rating, sum(counts)

    def reducer(self, rating, counts):
        yield rating, sum(counts)

if __name__ == '__main__':
    MRReviewDistribution.run()
