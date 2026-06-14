from mrjob.job import MRJob
import json

class MRPriceSegment(MRJob):
    """Aggregates total restaurant count by price category/segment."""
    
    def mapper(self, _, line):
        try:
            data = json.loads(line)
            price_range = data.get('price_range')
            if price_range:
                yield price_range.strip(), 1
            else:
                yield 'Unknown', 1
        except Exception:
            pass

    def combiner(self, price_range, counts):
        yield price_range, sum(counts)

    def reducer(self, price_range, counts):
        yield price_range, sum(counts)

if __name__ == '__main__':
    MRPriceSegment.run()
