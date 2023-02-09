import scrapy
from urllib.parse import urlparse
from urllib.parse import parse_qs

from .utils import get_max_page, process_comments


class LevelpacksSpider(scrapy.Spider):
    name = 'levelpacks'

    def start_requests(self):
        url = 'http://bike.toyspring.com/levels.php?cp=0&p='

        for i in range(1, 1000):
            yield scrapy.Request(url=url+str(i))

    # start_urls = [
    #     'http://bike.toyspring.com/levels.php?cp=0&p=1',
    #     'http://bike.toyspring.com/levels.php?cp=0&p=4',
    #     'http://bike.toyspring.com/levels.php?cp=0&p=5',
    #     'http://bike.toyspring.com/levels.php?cp=0&p=16',
    #     'http://bike.toyspring.com/levels.php?cp=0&p=200',
    #     'http://bike.toyspring.com/levels.php?cp=0&p=202',
    # ]

    def parse(self, response):
        parsed_url = urlparse(response.url)

        if not response.meta.get('levelpack'):
            levelpack = {}

            # "p" stands for "pack".
            levelpack['id'] = int(parse_qs(parsed_url.query).get('p')[0])

            name = response.xpath('//b[@class="title"]/text()').get()
            if name:
                levelpack['name'] = name.strip()
            else:
                # Just a sanity check.
                # We suppose that, if the levelpack has no name, then it is invalid and should have "All levels" as title.
                if not response.xpath('//b[text()="All levels"]'):
                    self.logger.error('The levelpack ' + response.url + ' has no name but it doesn\'t contain "All levels" either!')
                return

            attributes = []
            if response.xpath('//table[@class="lpinfo"]/tr/td/font').get():
                attributes.append('builtin')
            if response.xpath('//img[@src="img/vng.gif"]').get():
                attributes.append('enhaced_graphics')
            if response.xpath('//table[@class = "lpinfo"]/tr/td/a[starts-with(@href, "view.php?c=") and contains(text(), "Hall of Fame")]').get():
                attributes.append('hof')
            if len(attributes) > 0:
                levelpack['attributes'] = attributes

            levelpack['file_urls'] = []

            download_url = response.xpath('//a[starts-with(@href, "levels/")]/@href').get()
            if download_url:
                levelpack['file_urls'].append(response.urljoin(download_url))

            hits = response.xpath('//table[@class="lpinfo"]/tr/td/div/text()').get()
            if hits:
                levelpack['hits'] = int(hits.split()[0])

            creator = response.xpath('//table[@class="lpinfo"]/tr/td/a[starts-with(@href, "player.php?p=")]/@href').get()
            if creator and len(creator) > 13:
                levelpack['creator'] = int(creator[13:])
            else:
                creator = response.xpath('//table[@class="lpinfo"]/tr/td[starts-with(text(), "Created by")]/text()').getall()
                if creator and len(creator) > 1:
                    levelpack['creator'] = creator[1]
                else:
                    levelpack['creator'] = response.xpath('//table[@class="lpinfo"]/tr/td[starts-with(text(), "Created by")]/a/text()').get()

            rating = 0
            for i in range(1, 6):
                if response.xpath('//table[@class="lpinfo"]/tr/td/img[@src="img/greendot' + str(i) + '.gif"]'):
                    rating += i
                    break
            for i in range(1, 4):
                if response.xpath('//table[@class="lpinfo"]/tr/td/img[@src="img/greendot1q' + str(i) + '.gif"]'):
                    rating += i * 0.25
                    break
            if rating > 0:
                levelpack['rating'] = rating

            difficulty = 0
            for i in range(1, 6):
                if response.xpath('//table[@class="lpinfo"]/tr/td/img[@src="img/reddot' + str(i) + '.gif"]'):
                    difficulty += i
                    break
            for i in range(1, 4):
                if response.xpath('//table[@class="lpinfo"]/tr/td/img[@src="img/reddot1q' + str(i) + '.gif"]'):
                    difficulty += i * 0.25
                    break
            if difficulty > 0:
                levelpack['difficulty'] = difficulty

            dates = response.xpath('//table[@class="lpinfo"]/tr/td[starts-with(text(), "Since")]/text()').getall()
            if dates:
                levelpack['uploaded'] = dates[0][7:]
                if len(dates) > 1:
                    levelpack['updated'] = dates[1][9:] + ' ' + dates[2]

            if response.xpath('//img[@src="img/v14.gif"]'):
                levelpack['bod_version'] = '1.4'
            elif response.xpath('//img[@src="img/v15.gif"]'):
                levelpack['bod_version'] = '1.5'
            elif response.xpath('//img[@src="img/v16.gif"]'):
                levelpack['bod_version'] = '1.6'
            else:
                levelpack['bod_version'] = '1.0'
        else:
            levelpack = response.meta['levelpack']

        process_comments(response.xpath('//div[@class = "mainview"]/table[not(@class)]/tr[td/table]'), levelpack, response)

        # "cp" stands for "comments page".
        current_page = int(parse_qs(parsed_url.query).get('cp')[0])

        max_page = get_max_page(response.xpath('//div[@class = "pages"]/div'))
        if current_page == max_page:
            # Max page reached, we're done.
            yield levelpack
        else:
            yield scrapy.Request('http://bike.toyspring.com/levels.php?cp=' + str(current_page + 1) + '&p=' + str(levelpack['id']), self.parse, meta={'levelpack': levelpack})
