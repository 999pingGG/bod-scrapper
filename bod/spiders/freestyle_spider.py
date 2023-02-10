import scrapy

from .utils import get_max_page, process_comments, process_user_text


class Freestyle(scrapy.Spider):
    name = 'freestyle'

    def start_requests(self):
        yield scrapy.Request(url='http://bike.toyspring.com/view.php?cp=0&c=201', cb_kwargs=dict(
            category=201,
            comments_page=0,
            freestyle=dict(title='Freestyle Parade', games=[], comments=[]))
        )
        yield scrapy.Request(url='http://bike.toyspring.com/view.php?cp=0&c=238', cb_kwargs=dict(
            category=238,
            comments_page=0,
            freestyle=dict(title='One Wheel Fun', games=[], comments=[]))
        )
        yield scrapy.Request(url='http://bike.toyspring.com/view.php?cp=0&c=203', cb_kwargs=dict(
            category=203,
            comments_page=0,
            freestyle=dict(title='Bike or Die 2 Intro', games=[], comments=[]))
        )
        yield scrapy.Request(url='http://bike.toyspring.com/view.php?cp=0&c=200', cb_kwargs=dict(
            category=200,
            comments_page=0,
            freestyle=dict(title='Old Freestyle', games=[], comments=[]))
        )
        yield scrapy.Request(url='http://bike.toyspring.com/view.php?cp=0&c=220', cb_kwargs=dict(
            category=220,
            comments_page=0,
            freestyle=dict(title='Final Frontier', games=[], comments=[]))
        )
        yield scrapy.Request(url='http://bike.toyspring.com/view.php?cp=0&c=202', cb_kwargs=dict(
            category=202,
            comments_page=0,
            freestyle=dict(title='Testing Freestyle', games=[], comments=[]))
        )

    def parse(self, response, category, comments_page, freestyle):
        status_div = response.xpath('//td[@class = "mainview"]/div[@class = "mainview"]/div[starts-with(@class, "catstatus")]')
        if status_div.xpath('contains(b/text(), "Accepting")').get() == '0':
            freestyle['closure'] = status_div.xpath('text()').get()[3:]

        process_comments(response.xpath('//td[@class = "mainview"]/div[@class = "mainview"]/table[not(@class)]/tr'), freestyle, response)

        freestyle['rules'] = process_user_text(''.join(response.xpath('//div[@class = "fsrules"]/node()').getall()))

        max_page = get_max_page(response.xpath('//div[@class = "pages"]/div'))
        if comments_page == max_page:
            # Max comments page reached, proceed to gather submitted games.
            yield scrapy.Request('http://bike.toyspring.com/view.php?hp=0&c=' + str(category), self.parse_games, cb_kwargs=dict(
                category=category,
                games_page=0,
                freestyle=freestyle,
            ))
        else:
            comments_page += 1
            yield scrapy.Request('http://bike.toyspring.com/view.php?cp=' + str(comments_page) + '&c=' + str(category), self.parse, cb_kwargs=dict(
                category=category,
                comments_page=comments_page,
                freestyle=freestyle,
            ))

    def parse_games(self, response, category, games_page, freestyle):
        games = freestyle['games'] or []

        for row in response.xpath('//table[@class = "fsrate"]/tr'):
            game = {
                'id': int(row.xpath('td[@class = "first"]/center/small/a/@href').get()[11:]),
                'rank': int(row.xpath('td[@class = "first"]/center/div[@class = "fsscore"]/span[@class = "fsrank"]/text()').get()[1:]),
                'score': ''.join(row.xpath('td[@class = "first"]/center/div[@class = "fsscore"]/span[@class = "pts"]/descendant-or-self::text()').getall()),
                'player_id': int(row.xpath('td[@class = "first"]/center/a[starts-with(@href, "player.php?p=")]/@href').get()[13:]),
                'level_id': int(row.xpath('td[@class = "first"]/center/a[starts-with(@href, "level.php?l=")]/@href').get()[12:]),
            }
            movie_id = row.xpath('td[not(@class)]/div[@replay-url]/@replay-url').get()
            game['movie_id'] = movie_id[12:movie_id.find('&')]
            games.append(game)

        freestyle['games'] = games

        max_page = get_max_page(response.xpath('//div[@class = "pages" and not(/div)]'))
        if games_page == max_page:
            # Max games page reached, we're done.
            yield freestyle
        else:
            games_page += 1
            yield scrapy.Request('http://bike.toyspring.com/view.php?hp=' + str(games_page) + '&c=' + str(category), self.parse_games, cb_kwargs=dict(
                category=category,
                games_page=games_page,
                freestyle=freestyle,
            ))
