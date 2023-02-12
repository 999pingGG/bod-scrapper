import scrapy

from .utils import get_max_page, get_timestamp_from_script, process_comments, process_user_text, process_file_urls


class Forum(scrapy.Spider):
    name = 'forum'

    def start_requests(self):
        yield scrapy.Request(url='http://bike.toyspring.com/forum.php?th=1972&tp=0', cb_kwargs=dict(
            threads_page=0,
            category=1972,
        ))
        yield scrapy.Request(url='http://bike.toyspring.com/forum.php?th=1973&tp=0', cb_kwargs=dict(
            threads_page=0,
            category=1973,
        ))
        # The HoF category is redundant: We can rebuild it from HoF level's comments.

        # yield scrapy.Request(url='http://bike.toyspring.com/forum.php?th=1974&tp=0', cb_kwargs=dict(
        #     threads_page=0,
        #     category=1974,
        # ))
        yield scrapy.Request(url='http://bike.toyspring.com/forum.php?th=1975&tp=0', cb_kwargs=dict(
            threads_page=0,
            category=1975,
        ))
        yield scrapy.Request(url='http://bike.toyspring.com/forum.php?th=1976&tp=0', cb_kwargs=dict(
            threads_page=0,
            category=1976,
        ))
        # The levels category is redundant: We can rebuild it from the level's comments.

        # yield scrapy.Request(url='http://bike.toyspring.com/forum.php?th=1979&tp=0', cb_kwargs=dict(
        #     threads_page=0,
        #     category=1979,
        # ))

    def parse(self, response, threads_page, category):
        for row in response.xpath('//td[@class = "mainview"]/div[@class = "mainview"]/table/tr[not(@class)]'):
            thread_url = row.xpath('td/table/tr/td[@class = "bubble"]/a[starts-with(@href, "forum.php?th=")]/@href').get()
            if not thread_url:
                # Workaround for Mr. Pickle's "ghost thread" here lmao: http://bike.toyspring.com/forum.php?tp=6&th=1975
                print("Ghost thread at " + response.url)
                continue

            thread_id = int(thread_url[13:])
            thread_url = response.urljoin(thread_url)
            yield scrapy.Request(thread_url, callback=self.parse_thread, cb_kwargs=dict(
                comments_page=0,
                thread=dict(id=thread_id, category=category)
            ))

        max_page = get_max_page(response.xpath('//div[@class = "pages"]'))
        if threads_page == max_page:
            # Max page reached, done dispatching thread downloads for this forum category.
            return
        else:
            threads_page += 1
            yield scrapy.Request('http://bike.toyspring.com/forum.php?tp=' + str(threads_page) + '&th=' + str(category), self.parse, cb_kwargs=dict(
                threads_page=threads_page,
                category=category,
            ))

    def parse_thread(self, response, comments_page, thread):
        if comments_page == 0:
            thread_content = response.xpath('//td[@class = "mainview"]/div[@class = "mainview"]/table[@cellpadding = "8" and @width="100%"]/tr')

            player_id = thread_content.xpath('td[@align = "center"]/a[starts-with(@href, "player.php?p=")]/@href').get()
            if player_id:
                thread['player_id'] = int(player_id[13:])
            else:
                # If the thread has no player ID, assume Sz posted it because some news threads by Sz have no player ID...
                # I hope this doesn't happen with anyone else's threads.
                thread['player_id'] = 2

            thread['title'] = thread_content.xpath('td/h2/text()').get()
            thread['date'] = get_timestamp_from_script(thread_content.xpath('descendant-or-self::div[@class = "stamp"]/script/text()').get())

            thread_content = thread_content.xpath('td[not(@*)]/node()').getall()
            # Take out the title.
            thread_content.pop(0)
            thread_content = process_user_text(''.join(thread_content))
            thread['content'] = thread_content
            process_file_urls(thread_content, thread, response)

        process_comments(response.xpath('//td[@class = "mainview"]/div[@class = "mainview"]/table[not(@*)]/tr'), thread, response)

        max_page = get_max_page(response.xpath('//div[@class = "pages"]/div'))
        if comments_page == max_page:
            # Max page reached, we're done.
            yield thread
        else:
            comments_page += 1
            yield scrapy.Request('http://bike.toyspring.com/forum.php?tp=' + str(comments_page) + '&th=' + str(thread['id']), self.parse_thread, cb_kwargs=dict(
                comments_page=comments_page,
                thread=thread,
            ))
