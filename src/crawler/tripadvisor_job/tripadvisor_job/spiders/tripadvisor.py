import scrapy
from tripadvisor_job.items import TripadvisorJobItem

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_playwright.page import PageMethod

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
            yield scrapy.Request(
                url, 
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        # Wait up to 2 minutes for the real page to load so you can solve CAPTCHA
                        PageMethod('wait_for_selector', '#lithium-root', timeout=120000)
                    ]
                }
            )

    def use_playwright(self, request, response):
        request.meta['playwright'] = True
        request.meta['playwright_page_methods'] = [
            PageMethod('wait_for_selector', '#lithium-root', timeout=120000)
        ]
        return request

    def parse_restaurant(self, response):
        self.logger.info(f"Connection Status: {response.status}")
        self.logger.info(f"Page URL: {response.url}")
        
        # If this is a paginated review page, retrieve the existing item
        if 'restaurant_item' in response.meta:
            item = response.meta['restaurant_item']
            reviews = item['reviews']
            total_reviews = response.meta.get('total_reviews', 0)
        else:
            item = TripadvisorJobItem()
            item['_id'] = response.url
            item['name'] = response.xpath('//*[@id="lithium-root"]/main/div/div/div[2]/div[3]/div/div[1]/div[1]/span/h1/text()').get()
            
            rating = response.css('#lithium-root > main > div > div > div:nth-child(2) > div.SZXBR.cZRjG.xUqsL > div > div.CsAqy > span.HUMGB.CNLYa > span > div > div > span > div > span::text').get()
            if not rating:
                rating = response.css('#REVIEWS > div > div.WMQVi > div > div > div.wtCeG.f > div.egVMo > div > div.qymjm > div.biGQs._P.SewaP.WupKi::text').get()
            item['rating'] = float(rating) if rating else None
            
            review_count = response.css('#lithium-root > main > div > div > div:nth-child(2) > div.SZXBR.cZRjG.xUqsL > div > div.CsAqy > span.HUMGB.CNLYa > span > div > div > div > div > a > div > span::text').get()
            if not review_count:
                review_count = response.css('#REVIEWS > div > div.WMQVi > div > div > div.wtCeG.f > div.egVMo > div > div.qymjm > div.JbuXZ > div > div > div > div > div > span::text').get()
            item['review_count'] = review_count

            # Parse total reviews to prevent infinite pagination loops
            total_reviews = 0
            raw_count = item.get('review_count')
            if raw_count:
                import re
                digits = re.sub(r'\D', '', str(raw_count))
                if digits:
                    total_reviews = int(digits)

            address = response.xpath('//*[@id="lithium-root"]/main/div/div/div[3]/div[1]/div[1]/div[1]/div[2]/div[2]/button/span/text()').get()
            item['address'] = address
            
            item['district'] = None
            item['city'] = None
            if address:
                parts = [p.strip() for p in address.split(',')]
                item['city'] = parts[-1] if len(parts) > 0 else None
                item['district'] = parts[-2] if len(parts) > 1 else None
            
            reviews = []

        # Select individual review cards directly to automatically skip ads and prevent concatenated text
        review_blocks = response.css('div[data-automation="reviewCard"]')
        
        for block in review_blocks:
            # Extract user name (usually a link to their profile)
            user = block.xpath('.//a[contains(@href, "/Profile/")]/text()').get()
            if not user:
                user = block.css('div.mtJSe.f.k > div.hcVjp.f.u.o > div.QIHsu.Zb > span > a::text').get()
            
            # Extract rating (SVG with bubbles). Check attributes and child <title> tags.
            rating_val = None
            for svg in block.xpath('.//*[name()="svg"]'):
                val = svg.xpath('@title | @aria-label | title/text()').get()
                if val and 'bubble' in val.lower():
                    rating_val = val
                    break
            
            # Extract comment using relative XPath. Try explicit reviewText first, then fallback to span/div
            comment_nodes = block.xpath('.//span[@data-automation="reviewText"]//text()').getall()
            if not comment_nodes:
                comment_nodes = block.xpath('.//span/div/text()').getall()
            comment = "\n".join([c.strip() for c in comment_nodes if c.strip()]).strip()
            
            if user or comment:
                reviews.append({
                    "user": user,
                    "rating": rating_val,
                    "comment": comment if comment else None
                })
            
        item['reviews'] = reviews
        
        # Review pagination: dynamically generate the next page URL instead of relying on the button DOM
        # TripAdvisor pagination uses -or15-, -or30-, etc.
        import re
        
        # If we found at least 15 reviews on this page, there might be a next page
        if len(review_blocks) >= 15:
            current_url = response.url
            match = re.search(r'-Reviews-or(\d+)-', current_url)
            
            if match:
                current_offset = int(match.group(1))
                next_offset = current_offset + 15
                next_url = current_url.replace(f'-Reviews-or{current_offset}-', f'-Reviews-or{next_offset}-')
            else:
                current_offset = 0
                next_offset = 15
                next_url = current_url.replace('-Reviews-', '-Reviews-or15-')
                
            # Stop mathematically if we've requested an offset beyond the total review count
            # or if we've hit the representative sample limit (max 5 pages / 75 reviews per restaurant)
            MAX_REVIEWS = 75
            if (total_reviews > 0 and next_offset >= total_reviews) or next_offset >= MAX_REVIEWS:
                yield item
            else:
                yield response.follow(
                    next_url, 
                    callback=self.parse_restaurant, 
                    meta={
                        'playwright': True, 
                        'restaurant_item': item,
                        'total_reviews': total_reviews,
                        'playwright_page_methods': [
                            PageMethod('wait_for_selector', '#lithium-root', timeout=120000)
                        ]
                    }
                )
        else:
            yield item
