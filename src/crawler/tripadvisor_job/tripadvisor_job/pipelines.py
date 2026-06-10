# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
import re
from itemadapter import ItemAdapter

class TripadvisorMongoPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI', 'mongodb://localhost:27017/'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'sentiment_db')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def extract_float(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        match = re.search(r'(\d+(\.\d+)?)', str(value))
        if match:
            return float(match.group(1))
        return None

    def extract_int(self, value):
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        digits = re.sub(r'\D', '', str(value))
        if digits:
            return int(digits)
        return 0

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        rest = adapter.asdict()
        
        # Clean data directly in pipeline
        rest['rating'] = self.extract_float(rest.get('rating'))
        rest['review_count'] = self.extract_int(rest.get('review_count'))
        
        if not rest.get('district'):
            rest['district'] = "Unknown"
        if not rest.get('city'):
            rest['city'] = "Unknown"
            
        cleaned_reviews = []
        for r in rest.get('reviews', []):
            r_rating = self.extract_float(r.get('rating'))
            r_comment = str(r.get('comment', '')).strip()
            r_user = str(r.get('user', '')).strip()
            
            if not r_user and not r_comment and r_rating is None:
                continue
                
            cleaned_reviews.append({
                "user": r_user if r_user else "Anonymous",
                "rating": r_rating,
                "comment": r_comment if r_comment else None
            })
            
        rest['reviews'] = cleaned_reviews

        # Upsert document into MongoDB using _id
        self.db['restaurants'].update_one(
            {'_id': rest['_id']},
            {'$set': rest},
            upsert=True
        )
        
        return item
