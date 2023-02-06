import re
import scrapy
from urllib.parse import urlparse
from urllib.parse import parse_qs

from .utils import get_max_page, get_timestamp_from_script


# Replace smileys' HTML with the original text.
# Also, use regex to replace things like player mentions and external links.
comment_replacements = [
    {
        'old': '<img src="smiley/1.gif">',
        'new': ':)',
    },
    {
        'old': '<img src="smiley/2.gif">',
        'new': ':(',
    },
    {
        'old': '<img src="smiley/3.gif">',
        'new': '>:(',
    },
    # What happened to the smiley #4??
    {
        'old': '<img src="smiley/5.gif">',
        'new': '>:)',
    },
    {
        'old': '<img src="smiley/6.gif">',
        'new': ':p',
    },
    {
        'old': '<img src="smiley/7.gif">',
        'new': ':]',
    },
    {
        'old': '<img src="smiley/8.gif">',
        'new': ';)',
    },
    {
        'old': '<img src="smiley/9.gif">',
        'new': ":'(",
    },
    {
        'old': '<img src="smiley/10.gif">',
        'new': ':l',
    },
    #  What about smiley #11?
    {
        'old': '<img src="smiley/12.gif">',
        'new': ':D',
    },
    {
        'old': '\r<br>',
        'new': '\n',
    },
    {
        # I can't believe I finally understand regex!! Many thanks to https://regex101.com/

        # Replace player mentions' HTML which includes flag pic, profile pic and profile link
        # with a simple pattern containing just the player's ID.
        'regex': re.compile("<img src=\"flags/[a-zA-Z_-]*?\.gif\" align=\"absmiddle\">.*?<a href=\"player\.php\?p=([0-9]*?)\"><img src=\"pic/(\\1|empty)\.(gif|jpg|png)\" align=\"absmiddle\" width=\"24\" height=\"24\">[^<]*?</a>", re.S),
        'pre': '[player](',
        'group': 1,
        'post': ')',
    },
    {
        # Ideally, we should replace all the anchors where the href matches the inner text, but we have to match
        # .*?http.*? (inner text also starts with http) instead of .*?//1.*? (inner text matches href)
        # just because some links' inner text contains a space...
        'regex': re.compile("<a href=\"(\\S+)?\" target=\"_blank\"><img src=\"img/extlink.gif\" border=\"0\">.*?http.*?</a>", re.S),
        'pre': '[link](',
        'group': 1,
        'post': ')',
    },
]


class LevelpacksSpider(scrapy.Spider):
    name = "levelpacks"

    def start_requests(self):
        url = 'http://bike.toyspring.com/levels.php?cp=0&p='

        for i in range(1, 1000):
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

        # Grab comments.
        comments = levelpack.get('comments') or []
        pinned_comments = levelpack.get('pinned_comments') or []
        # "cp" stands for "comments page".
        current_page = int(parse_qs(parsed_url.query).get('cp')[0])

        # Get all the tr's that contain a td with a table, to filter out an empty row which appears
        # when there's a pinned comment.
        for row in response.xpath('//div[@class = "mainview"]/table[not(@class)]/tr[td/table]'):
            comment_selector = row.xpath('descendant::td[@class = "bubble"]')

            # Pinned comments have the "bubble_pin" class instead of "bubble". If "bubble" is not found,
            # look for "bubble_pin" and take it as a pinned comment.
            pinned = False
            if not comment_selector:
                comment_selector = row.xpath('descendant::td[@class = "bubble_pin"]')
                pinned = True

            comment_id = comment_selector.xpath('a/@name').get()
            if comment_id and comment_id[0] == 'c':
                comment_id = int(comment_id[1:])

                # Check for duplicated comment. I assume this only ever happens for some
                # of the lasts comments, which appear in both the last and the second last pages;
                # and for the pinned comment(s), which appear at the top of every page.
                if pinned and any(comment["comment_id"] == comment_id for comment in pinned_comments):
                    continue
                elif not pinned and any(comment["comment_id"] == comment_id for comment in comments):
                    continue
            else:
                self.logger.error('Comment has no ID!')
                continue

            comment = {}

            player_id = row.xpath('substring(td/a[starts-with(@href, "player.php?p=")]/@href, 14)').get()
            if player_id:
                comment['player_id'] = int(player_id)

            date = row.xpath('td/table/tr/td/div[@class = "stamp"]/script/text()').get()
            if date:
                comment['date'] = get_timestamp_from_script(date)

            content = ''.join(comment_selector.xpath('node()').getall())

            comment['comment_id'] = comment_id
            # Strip the anchor with the comment ID from the HTML, which I assume is always the first anchor.
            content = content[content.find('"></a>') + 6:]

            if date:
               # Strip the div which contains the timestamp script.
                content = content[0:content.find('<div class="stamp">')]

            for replacement in comment_replacements:
                if replacement.get('old'):
                    # This is a simple replacement.
                    content = content.replace(replacement['old'], replacement['new'])
                else:
                    # This replacement uses regex.
                    content = replacement['regex'].sub(
                        lambda match: replacement['pre'] + match.group(replacement['group']) + replacement['post'],
                        content
                    )

            comment['content'] = content
            # Download every image that might remain after the replacements.
            for img in scrapy.Selector(text=content).xpath('//img/@src').getall():
                levelpack['file_urls'].append(response.urljoin(img))

            if pinned:
                pinned_comments.append(comment)
            else:
                comments.append(comment)

        if len(comments) > 0:
            levelpack['comments'] = comments
        if len(pinned_comments) > 0:
            levelpack['pinned_comments'] = pinned_comments

        max_page = get_max_page(response.xpath('//div[@class = "pages"]/div'))
        if current_page == max_page:
            # Max page reached, we're done.
            yield levelpack
        else:
            yield scrapy.Request('http://bike.toyspring.com/levels.php?cp=' + str(current_page + 1) + '&p=' + str(levelpack['id']), self.parse, meta={'levelpack': levelpack})
