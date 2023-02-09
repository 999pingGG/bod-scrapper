import scrapy
from urllib.parse import urlparse
from urllib.parse import parse_qs

from .utils import get_max_page, process_comments, get_timestamp_from_script


class Games(scrapy.Spider):
    name = 'games'

    def start_requests(self):
        url = 'http://bike.toyspring.com/game.php?cp=0&g='

        for i in range(1, 1000000):
            yield scrapy.Request(url=url+str(i))

    def parse(self, response):
        parsed_url = urlparse(response.url)

        if not response.meta.get('game'):
            game = {}

            if response.xpath('//div[@class = "mainview"]/text()[2]').get() == 'Bad game link':
                return

            game['id'] = int(parse_qs(parsed_url.query).get('g')[0])

            game_details = response.xpath('//div[h3[text() = "Game Details"]]')
            player_id = game_details.xpath('table/tr/td/a[starts-with(@href, "player.php")]/@href').get()
            if player_id and len(player_id) > 13:
                game['player_id'] = int(player_id[13:])

            player_comment = {}
            process_comments(game_details.xpath('table[@cellpadding = "0"]'), player_comment, response)
            player_comment = player_comment.get('comments')
            if player_comment and len(player_comment) > 0:
                game['player_comment'] = player_comment[0]['content']

            monstruous_td = response.xpath('//td[@class = "leftnavi"]')

            level_id = monstruous_td.xpath('a[starts-with(@href, "view.php?l=")]/@href').get()
            if level_id:
                game['level_id'] = int(level_id[11:])

            game['time'] = monstruous_td.xpath('b/text()').get()[6:]
            if monstruous_td.xpath('text()[contains(., "Completed")]').get():
                game['result'] = 'completed'
            elif monstruous_td.xpath('text()[contains(., "Failed")]').get():
                game['result'] = 'failed'
            elif monstruous_td.xpath('text()[contains(., "Aborted")]').get():
                game['result'] = 'aborted'
            else:
                game['result'] = 'unknown'

            game['submitted'] = get_timestamp_from_script(monstruous_td.xpath('script/text()').get())

            related_games = monstruous_td.xpath('ul/li/a[starts-with(@href, "game.php?g=")]/@href').getall()
            if len(related_games) > 0:
                ids = []
                for game_link in related_games:
                    ids.append(int(game_link[11:]))
                game['related_games'] = ids
        else:
            game = response.meta.get('game')

        process_comments(response.xpath('//div[@class = "mainview"]/table[not(@class)]/tr[td/table]'), game, response)

        current_page = int(parse_qs(parsed_url.query).get('cp')[0])

        max_page = get_max_page(response.xpath('//div[@class = "pages"]/div'))
        if current_page == max_page:
            # Max page reached, now proceed to download the movie.
            movie = response.xpath('//div[@class = "bod-replay"]/@replay-url').get()
            if movie:
                yield scrapy.Request(response.urljoin(movie), self.parse_movie, meta={'game': game}, errback=self.movie_error_handler, cb_kwargs=dict(game=game))
            else:
                if response.xpath('//td[@class = "mainview"]/div[@class = "mainview"]/center[contains(text(), "marked private")]').get():
                    game['attributes'] = ['private']
                yield game
        else:
            yield scrapy.Request('http://bike.toyspring.com/game.php?cp=' + str(current_page + 1) + '&g=' + str(game['id']), self.parse, meta={'game': game})

    def parse_movie(self, response, game):
        game['movie'] = response.body.decode()
        yield game

    def movie_error_handler(self, failure):
        yield failure.request.cb_kwargs['game']
