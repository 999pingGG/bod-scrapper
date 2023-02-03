import scrapy
from urllib.parse import urlparse
from urllib.parse import parse_qs


class LevelpacksSpider(scrapy.Spider):
    name = "levelpacks"

    def start_requests(self):
        url = 'http://bike.toyspring.com/levels.php?cp=0&p='

        for i in range(1, 10000):
            yield scrapy.Request(url=url+str(i), callback=self.parse)

    # start_urls = [
    #     'http://bike.toyspring.com/levels.php?cp=0&p=1',
    #     'http://bike.toyspring.com/levels.php?cp=0&p=4',
    #     'http://bike.toyspring.com/levels.php?cp=0&p=5',
    #     'http://bike.toyspring.com/levels.php?cp=0&p=16',
    #     'http://bike.toyspring.com/levels.php?cp=0&p=200',
    #     'http://bike.toyspring.com/levels.php?cp=0&p=202',
    # ]

    def parse(self, response):
        levelpack = {}

        parsed_url = urlparse(response.url)
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
        if bool(response.xpath('//table[@class="lpinfo"]/tr/td/font').get()):
            attributes.append('builtin')
        if bool(response.xpath('//img[@src="img/vng.gif"]')):
            attributes.append('enhaced_graphics')
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
            creators = response.xpath('//table[@class="lpinfo"]/tr/td[starts-with(text(), "Created by")]/text()').getall()
            if creators and len(creators) > 1:
                levelpack['creators'] = creators[1]
            else:
                levelpack['creator'] = response.xpath('//table[@class="lpinfo"]/tr/td[starts-with(text(), "Created by")]/a/text()').get()

        # Ugh, the rating and difficulty code can be merged into a method.
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
        if difficulty > 0:
            levelpack['difficulty'] = difficulty

        dates = response.xpath('//table[@class="lpinfo"]/tr/td[starts-with(text(), "Since")]/text()').getall()
        if dates:
            levelpack['uploaded'] = dates[0][7:]
            if len(dates) > 1:
                levelpack['updated'] = dates[1][9:] + ' ' + dates[2]

        if response.xpath('//img[@src="img/v14.gif"]'):
            levelpack['bod_version'] = '1.4'
        if response.xpath('//img[@src="img/v15.gif"]'):
            levelpack['bod_version'] = '1.5'
        if response.xpath('//img[@src="img/v16.gif"]'):
            levelpack['bod_version'] = '1.6'
        if not levelpack.get('bod_version'):
            levelpack['bod_version'] = '1.0'

        yield levelpack
