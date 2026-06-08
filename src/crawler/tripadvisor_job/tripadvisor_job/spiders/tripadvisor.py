import scrapy
from tripadvisor_job.items import TripadvisorJobItem

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class TripadvisorSpider(CrawlSpider):
    name = "tripadvisor"
    allowed_domains = ["tripadvisor.com"]
    
    # Start at the first page
    start_urls = ["https://www.tripadvisor.com/Restaurants-g293925-oa0-Ho_Chi_Minh_City.html"]

    rules = (
        # Rule for pagination: match URLs with -oa(number)-
        Rule(
            LinkExtractor(allow=r'-oa\d+-Ho_Chi_Minh_City\.html'), 
            follow=True, 
            process_request='use_playwright'
        ),
        
        # Rule for restaurant review pages
        Rule(
            LinkExtractor(allow=r'Restaurant_Review-g293925-d\d+-Reviews-'), 
            callback='parse_restaurant', 
            process_request='use_playwright'
        ),
    )

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, meta={'playwright': True})

    def use_playwright(self, request, response):
        request.meta['playwright'] = True
        return request

    def parse_restaurant(self, response):
        self.logger.info(f"Connection Status: {response.status}")
        self.logger.info(f"Page URL: {response.url}")
        
        item = TripadvisorJobItem()
        # TODO: Implement parsing logic and extract data according to TripadvisorJobItem schema
        
        yield item
