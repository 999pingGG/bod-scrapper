import scrapy
from urllib.parse import urlparse
from urllib.parse import parse_qs


class PlayersSpider(scrapy.Spider):
    name = "players"

    def start_requests(self):
        url = 'http://bike.toyspring.com/player.php?p='
        # We don't want to miss any single player. This should be enough.
        # Unless Sz has hidden something in a ridiculously large ID.
        for i in range(1, 100000):
            yield scrapy.Request(url=url+str(i), callback=self.parse)

    # start_urls = [
    #     'http://bike.toyspring.com/player.php?p=4379',
    #     'http://bike.toyspring.com/player.php?p=8270',
    #     'http://bike.toyspring.com/player.php?p=20470',
    # ]

    def parse(self, response):
        player = {}

        parsed_url = urlparse(response.url)
        player['id'] = parse_qs(parsed_url.query).get('p')

        if player['id']:
            player['id'] = player['id'][0]
        else:   # Just a sanity check.
            self.logger.error('Invalid URL!!')
            return

        player['name'] = response.css('div.plname::text').get()
        if not player['name']:  # This is an invalid player link, skip this.
            yield player
            return

        # This name has to be 'file_urls' to enable the file download pipeline.
        player['file_urls'] = []

        pic_url = response.css('img#plpic::attr(src)').get()
        if pic_url:
            player['pic'] = response.urljoin(pic_url)
            player['file_urls'].append(player['pic'])

        flag_url = response.xpath('//img[starts-with(@src, "flags")]/@src').get()
        if flag_url:
            player['flag'] = response.urljoin(flag_url)
            player['file_urls'].append(player['flag'])

        # lmao
        monstruous_div = response.xpath('//td[@class="leftnavi"]/div[not(@class)]')

        player['location'] = monstruous_div.xpath('text()')[1].get().strip()

        email = monstruous_div.xpath('substring(a[starts-with(@href, "mailto:")]/@href, 8)').get()
        if email:
            player['email'] = email

        homepage = monstruous_div.xpath('//img[@src="img/extlink.gif"]//parent::a/@href').get()
        if homepage:
            player['homepage'] = homepage

        # The 'pt' param is the "online games" tab.
        # The 's' param is the page number.
        yield scrapy.Request(response.url + '&pt=1&s=0', self.parse_games_online, meta={'player': player})

    def parse_games_online(self, response):
        player = response.meta['player']

        player['games'] = []
        rows = response.xpath('//table[@id="games"]/tr')
        for row in rows:
            timestamp = row.xpath('descendant::script/text()').get()
            timestamp = int(timestamp[4:timestamp.find(')')])

            level_id = int(row.xpath('td[position()=2]/a/@href').get()[11:])

            time = row.xpath('td[position()=3]/text()').get()

            # This is just a work variable.
            replay = row.xpath('td[position()=4]/a')

            game_id = int(replay.xpath('@href').get()[11:])

            flags = []
            if replay.xpath('img[@src="img/view.gif"]'):
                flags.append('public')
            if replay.xpath('img[@src="img/noview.gif"]'):
                flags.append('private')
            if replay.xpath('img[@src="img/hof.gif"]'):
                flags.append('hof')
            if replay.xpath('img[@src="img/minifreestyle.gif"]'):
                flags.append('freestyle')
            if replay.xpath('img[@src="img/fscompo.gif"]'):
                flags.append('competition')

            player['games'].append({
                'game_id': game_id,
                'timestamp': timestamp,
                'level_id': level_id,
                'time': time,
                'flags': flags,
            })

        parsed_url = urlparse(response.url)
        current_page = int(parse_qs(parsed_url.query).get('s')[0])

        if response.meta.get('max_page') and current_page == response.meta['max_page']:
            # Max page reached: End of the process.
            yield player
            return
        else:
            # Some black magic *uckery to get all the a (anchor) and b (bold) elements contained by the pagination div.
            #   - The anchors are the clickable buttons, including navigation buttons and pages buttons.
            #   - The bold element is not a button, it indicates the current page.
            # From all those, get the maximum value.
            # The pagination div is not even present when there's only one page.
            page_numbers = response.css('div.pages').xpath('a/text()[number(.) = .] | b/text()[number(.) = .]').getall()
            page_numbers = [int(i) for i in page_numbers]
            if page_numbers:
                response.meta['max_page'] = max(page_numbers) - 1
            else:
                # This player has a single page of games, process finished.
                yield player
                return

        yield scrapy.Request('http://bike.toyspring.com/player.php?p=' + player['id'] + '&pt=1&s=' + str(current_page + 1), self.parse_games_online, meta=response.meta)
