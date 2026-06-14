from mrjob.job import MRJob
import json

class MRRatingBucket(MRJob):
    """Classifies restaurants into rating buckets (1-2 Stars, 3 Stars, 4-5 Stars)."""
    
    def mapper(self, _, line):
        try:
            data = json.loads(line)
            rating = data.get('rating')
            if rating is not None:
                try:
                    r_val = float(rating)
                    if r_val >= 4.0:
                        bucket = "4-5 Stars"
                    elif r_val >= 3.0:
                        bucket = "3 Stars"
                    else:
                        bucket = "1-2 Stars"
                    yield bucket, 1
                except ValueError:
                    yield "Unknown", 1
            else:
                yield "Unknown", 1
        except Exception:
            pass

    def combiner(self, bucket, counts):
        yield bucket, sum(counts)

    def reducer(self, bucket, counts):
        yield bucket, sum(counts)

if __name__ == '__main__':
    MRRatingBucket.run()
