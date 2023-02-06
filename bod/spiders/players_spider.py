import scrapy
from urllib.parse import urlparse
from urllib.parse import parse_qs

from .utils import get_max_page, get_timestamp_from_script


class PlayersSpider(scrapy.Spider):
    name = "players"

    def start_requests(self):
        url = 'http://bike.toyspring.com/player.php?p='
        for i in range(1, 30000):
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
            player['id'] = int(player['id'][0])
        else:   # Just a sanity check.
            self.logger.error('Invalid URL!!')
            return

        player['name'] = response.css('div.plname::text').get()
        if not player['name']:  # This is an invalid player link, skip this.
            return

        # This name has to be 'file_urls' to enable the file download pipeline.
        player['file_urls'] = []

        pic_url = response.css('img#plpic::attr(src)').get()
        if pic_url:
            player['pic_url'] = response.urljoin(pic_url)
            player['file_urls'].append(player['pic_url'])

        flag_url = response.xpath('//img[starts-with(@src, "flags")]/@src').get()
        if flag_url:
            player['flag_url'] = response.urljoin(flag_url)
            player['file_urls'].append(player['flag_url'])

        # lmao
        monstruous_div = response.xpath('//td[@class="leftnavi"]/div[not(@class)]')

        if (response.xpath('//img[starts-with(@src, "flags")]')):
            player['location'] = monstruous_div.xpath('text()')[1].get().strip()

        email = monstruous_div.xpath('substring(a[starts-with(@href, "mailto:")]/@href, 8)').get()
        if email:
            player['email'] = email

        homepage = monstruous_div.xpath('//img[@src="img/extlink.gif"]//parent::a/@href').get()
        if homepage:
            player['homepage'] = homepage

        timestamp_scripts = monstruous_div.xpath('script/text()').getall()

        contains_last_seen = bool(monstruous_div.xpath('text()[contains(., "Last seen")]'))
        contains_last_submission = bool(monstruous_div.xpath('text()[contains(., "Last submission")]'))
        if contains_last_seen:
            player['last_seen'] = get_timestamp_from_script(timestamp_scripts[0])
        if contains_last_submission:
            if contains_last_seen:
                player['last_submission'] = get_timestamp_from_script(timestamp_scripts[1])
            else:
                player['last_submission'] = get_timestamp_from_script(timestamp_scripts[0])

        best_rank_ever = monstruous_div.xpath('b[starts-with(text(), "#")]/text()').get()
        if best_rank_ever:
            player['best_rank_ever'] = {
                'rank': int(best_rank_ever[1:]),
            }
            time = monstruous_div.xpath('text()[contains(., "(for")]').get()
            if time:
                tokens = time.split()
                player['best_rank_ever']['duration'] = int(tokens[1])
                if len(tokens) > 3:
                    player['best_rank_ever']['months_ago'] = int(tokens[3])

        ranking_url = response.xpath('//a[starts-with(@title, "CSV file")]/@href').get()
        if ranking_url:
            player['ranking_url'] = response.urljoin(ranking_url)
            player['file_urls'].append(player['ranking_url'])

        # The 'pt' param is the "player tab". In this case, tab 1 is the "online games" tab.
        # The 's' param is the page number.
        yield scrapy.Request(response.url + '&pt=1&s=0', self.parse_games_online, meta={'player': player})

    def parse_games_online(self, response):
        player = response.meta['player']

        player['games'] = []
        rows = response.xpath('//table[@id="games"]/tr')
        for row in rows:
            submitted = get_timestamp_from_script(row.xpath('descendant::script/text()').get())
            level_id = int(row.xpath('td[position()=2]/a/@href').get()[11:])
            time = row.xpath('td[position()=3]/text()').get()
            # This is just a work variable.
            replay = row.xpath('td[position()=4]/a')
            game_id = int(replay.xpath('@href').get()[11:])
            attributes = []
            if replay.xpath('img[@src="img/view.gif"]'):
                attributes.append('public')
            if replay.xpath('img[@src="img/noview.gif"]'):
                attributes.append('private')
            if replay.xpath('img[@src="img/hof.gif"]'):
                attributes.append('hof')
            if replay.xpath('img[@src="img/minifreestyle.gif"]'):
                attributes.append('freestyle')
            if replay.xpath('img[@src="img/fscompo.gif"]'):
                attributes.append('competition')

            player['games'].append({
                'game_id': game_id,
                'submitted': submitted,
                'level_id': level_id,
                'time': time,
                'attributes': attributes,
            })

        parsed_url = urlparse(response.url)
        current_page = int(parse_qs(parsed_url.query).get('s')[0])

        max_page = get_max_page(response.css('div.pages'))
        if current_page == max_page:
            # Max page reached, now proceed to gather their uploads.
            # Tab 2 is the "uploads" tab.
            yield scrapy.Request('http://bike.toyspring.com/player.php?p=' + str(player['id']) + '&pt=2', self.parse_uploads, meta={'player': player})
            return

        yield scrapy.Request('http://bike.toyspring.com/player.php?p=' + str(player['id']) + '&pt=1&s=' + str(current_page + 1), self.parse_games_online, meta=response.meta)

    def parse_uploads(self, response):
        player = response.meta['player']

        rows = response.xpath('//table[@class="main"]/tr')
        if rows:
            player['levelpacks'] = []

            # I don't think anyone has uploaded so many levels as to require pagination.
            # If that ever happens, just signal it here and continue.
            if response.css('div.pages'):
                player['has_many_levelpacks'] = True

            for row in rows:
                levelpack = {}

                levelpack_id = row.xpath('td/a[starts-with(@href, "levels.php?p=")]/@href').get()
                if levelpack_id and len(levelpack_id) > 13:
                    levelpack['id'] = int(levelpack_id[13:])

                anchor = row.xpath('td/a[starts-with(@href, "getfile.php?f=")]')

                levelpack_name = anchor.xpath('text()').get().strip()
                if levelpack_name:
                    levelpack['name'] = levelpack_name

                file_id = anchor.xpath('@href').get()
                if file_id and len(file_id) > 14:
                    levelpack['file_id'] = int(file_id[14:])

                uploaded = row.xpath('td/script/text()').get()
                if uploaded:
                    levelpack['uploaded'] = get_timestamp_from_script(uploaded)

                player['levelpacks'].append(levelpack)

        # Finished gathering uploads, process finished.
        yield player
