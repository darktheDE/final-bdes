from mrjob.job import MRJob
import json
import re

class MRDeliveryAnalysis(MRJob):
    """Compares average rating/sentiment for delivery-friendly vs dine-in-only restaurants."""
    
    DELIVERY_KEYWORDS = {
        "delivery", "deliver", "ship", "takeaway", "carryout", "grab", 
        "shopeefood", "gojek", "foody", "mang ve", "giao hang", "shipment"
    }
    
    def mapper(self, _, line):
        try:
            data = json.loads(line)
            rating = data.get('rating')
            if rating is None:
                return
                
            # Check comments for delivery mentions
            is_delivery = False
            for r in data.get('reviews', []):
                comment = r.get('comment', '')
                if comment:
                    comment_lower = comment.lower()
                    if any(kw in comment_lower for kw in self.DELIVERY_KEYWORDS):
                        is_delivery = True
                        break
                        
            label = "Delivery-Friendly" if is_delivery else "Dine-In-Only"
            yield label, (float(rating), 1)
        except Exception:
            pass

    def combiner(self, label, ratings):
        total_rating = 0.0
        total_count = 0
        for rating, count in ratings:
            total_rating += rating
            total_count += count
        yield label, (total_rating, total_count)

    def reducer(self, label, ratings):
        total_rating = 0.0
        total_count = 0
        for rating, count in ratings:
            total_rating += rating
            total_count += count
        if total_count > 0:
            yield label, {
                'avg_rating': round(total_rating / total_count, 2),
                'restaurant_count': total_count
            }

if __name__ == '__main__':
    MRDeliveryAnalysis.run()
