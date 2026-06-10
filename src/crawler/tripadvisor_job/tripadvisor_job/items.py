# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TripadvisorJobItem(scrapy.Item):
    _id = scrapy.Field()
    name = scrapy.Field()
    rating = scrapy.Field()
    review_count = scrapy.Field()
    address = scrapy.Field()
    district = scrapy.Field()
    city = scrapy.Field()
    reviews = scrapy.Field()
