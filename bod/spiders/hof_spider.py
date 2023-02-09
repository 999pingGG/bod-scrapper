import scrapy

from .utils import get_max_page, process_comments


class Hof(scrapy.Spider):
    name = 'hof'

    def start_requests(self):
        yield scrapy.Request(url='http://bike.toyspring.com/view.php?cp=0&c=0', cb_kwargs=dict(
            category=0,
            comments_page=0,
            hof=dict(title='Time Trial Champions', comments=[]))
        )
        yield scrapy.Request(url='http://bike.toyspring.com/view.php?cp=0&c=2', cb_kwargs=dict(
            category=2,
            comments_page=0,
            hof=dict(title='Medals by Country', comments=[]))
        )
        yield scrapy.Request(url='http://bike.toyspring.com/view.php?cp=0&c=116', cb_kwargs=dict(
            category=116,
            comments_page=0,
            hof=dict(title='Total Race', comments=[]))
        )
        yield scrapy.Request(url='http://bike.toyspring.com/view.php?cp=0&c=117', cb_kwargs=dict(
            category=117,
            comments_page=0,
            hof=dict(title='Golden Club', comments=[]))
        )

    def parse(self, response, category, comments_page, hof):
        process_comments(response.xpath('//td[@class = "mainview"]/div[@class = "mainview"]/table[not(@class)]/tr'), hof, response)

        max_page = get_max_page(response.xpath('//div[@class = "pages"]/div'))
        if comments_page == max_page:
            # Max page reached, we have finished.
            yield hof
        else:
            comments_page += 1
            yield scrapy.Request('http://bike.toyspring.com/view.php?cp=' + str(comments_page) + '&c=' + str(category), self.parse, cb_kwargs=dict(
                category=category,
                comments_page=comments_page,
                hof=hof
            ))
