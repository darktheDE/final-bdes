from mrjob.job import MRJob
import json

class MRCuisineCount(MRJob):
    """Counts cuisine/category occurrences and yields a sorted frequency distribution."""
    
    def mapper(self, _, line):
        try:
            data = json.loads(line)
            category = data.get('category')
            area = data.get('area')
            if category:
                yield category.strip(), 1
            if area:
                yield area.strip(), 1
        except Exception:
            pass

    def combiner(self, tag, counts):
        yield tag, sum(counts)

    def reducer(self, tag, counts):
        yield tag, sum(counts)

if __name__ == '__main__':
    MRCuisineCount.run()
