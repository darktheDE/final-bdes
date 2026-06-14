from mrjob.job import MRJob
import json
import re

class MRSentimentAnalysis(MRJob):
    """Calculates sentiment scores and averages per restaurant based on user review comments."""
    
    POSITIVE_WORDS = {
        "good", "excellent", "delicious", "tasty", "friendly", "great", "nice", 
        "amazing", "best", "perfect", "love", "wonderful", "satisfied", "clean", 
        "beautiful", "fresh", "helpful", "like", "awesome", "fantastic", "deliciously"
    }
    
    NEGATIVE_WORDS = {
        "bad", "slow", "poor", "dirty", "rude", "expensive", "worst", "cold", 
        "average", "disappointed", "terrible", "horrible", "overpriced", "dislike", 
        "angry", "hate", "unfriendly", "waste", "soggy"
    }
    
    def mapper(self, _, line):
        try:
            data = json.loads(line)
            name = data.get('name')
            reviews = data.get('reviews', [])
            if not name or not reviews:
                return
                
            for review in reviews:
                comment = review.get('comment', '')
                if not comment:
                    continue
                
                # Tokenize and normalize
                words = re.findall(r'\b\w+\b', comment.lower())
                pos_count = sum(1 for w in words if w in self.POSITIVE_WORDS)
                neg_count = sum(1 for w in words if w in self.NEGATIVE_WORDS)
                
                score = pos_count - neg_count
                yield name, (score, 1)
        except Exception:
            pass

    def combiner(self, name, scores):
        total_score = 0
        total_count = 0
        for score, count in scores:
            total_score += score
            total_count += count
        yield name, (total_score, total_count)

    def reducer(self, name, scores):
        total_score = 0
        total_count = 0
        for score, count in scores:
            total_score += score
            total_count += count
        if total_count > 0:
            yield name, {
                'avg_sentiment_score': round(total_score / total_count, 3),
                'reviews_analyzed': total_count
            }

if __name__ == '__main__':
    MRSentimentAnalysis.run()
