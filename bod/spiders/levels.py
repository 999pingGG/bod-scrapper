import scrapy
from urllib.parse import urlparse
from urllib.parse import parse_qs

from .utils import get_max_page, process_comments


class Levels(scrapy.Spider):
    name = 'levels'

    def start_requests(self):
        url = 'http://bike.toyspring.com/level.php?cp=0&l='

        for i in range(1, 5000):
            yield scrapy.Request(url=url+str(i), callback=self.parse)

    def parse(self, response):
        parsed_url = urlparse(response.url)

        if not response.meta.get('level'):
            level = {}

            if response.xpath('//body/p/text()').get() == 'unknown level':
                return

            # "l" stands for "level".
            level['id'] = int(parse_qs(parsed_url.query).get('l')[0])
            level['name'] = response.xpath('//b[@class="title"]/text()').get().strip()
            best_time = response.xpath('//table[@width = "100%"]/tr/td/a[starts-with(@href, "view.php?c=")]/text()').get()
            if best_time:
                level['best_time'] = best_time.strip()

            level_svg = response.xpath('//img[@class = "lvsvg"]/@src').get()
            if level_svg:
                level['svg'] = response.urljoin(level_svg)
                level['file_urls'] = level.get('file_urls') or []
                level['file_urls'].append(level['svg'])

            rating = 0
            for i in range(1, 6):
                if response.xpath('//div[@class = "mainview"]/table[@width = "100%"]/tr/td/img[@src="img/greendot' + str(i) + '.gif"]'):
                    rating += i
                    break
            for i in range(1, 4):
                if response.xpath('//div[@class = "mainview"]/table[@width = "100%"]/tr/td/img[@src="img/greendot1q' + str(i) + '.gif"]'):
                    rating += i * 0.25
                    break
            if rating > 0:
                level['rating'] = rating

            difficulty = 0
            for i in range(1, 6):
                if response.xpath('//div[@class = "mainview"]/table[@width = "100%"]/tr/td/img[@src="img/reddot' + str(i) + '.gif"]'):
                    difficulty += i
                    break
            for i in range(1, 4):
                if response.xpath('//div[@class = "mainview"]/table[@width = "100%"]/tr/td/img[@src="img/reddot1q' + str(i) + '.gif"]'):
                    difficulty += i * 0.25
                    break
            if difficulty > 0:
                level['difficulty'] = difficulty

            size = 0
            for i in range(1, 6):
                if response.xpath('//div[@class = "mainview"]/table[@width = "100%"]/tr/td/img[@src="img/amberdot' + str(i) + '.gif"]'):
                    size += i
                    break
            for i in range(1, 4):
                if response.xpath('//div[@class = "mainview"]/table[@width = "100%"]/tr/td/img[@src="img/amberdot1q' + str(i) + '.gif"]'):
                    size += i * 0.25
                    break
            if size > 0:
                level['size'] = size
        else:
            level = response.meta['level']

        process_comments(response.xpath('//div[@class = "mainview"]/table[not(@class)]/tr[td/table]'), level, response)

        # "cp" stands for "comments page".
        current_page = int(parse_qs(parsed_url.query).get('cp')[0])

        max_page = get_max_page(response.xpath('//div[@class = "pages"]/div'))
        if current_page == max_page:
            # Max page reached, we're done.
            yield level
        else:
            yield scrapy.Request('http://bike.toyspring.com/level.php?cp=' + str(current_page + 1) + '&l=' + str(level['id']), self.parse, meta={'level': level})
