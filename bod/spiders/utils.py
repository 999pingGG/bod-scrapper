import re
from scrapy import Selector


def get_max_page(pages_div):
    # Some black magic tr*ckery to get all the texts which are numbers from a (anchor) and b (bold) elements
    # contained by the pagination div.
    #   - The anchors are the clickable buttons, including navigation buttons and pages buttons.
    #   - The bold element is not a button, it indicates the current page.
    # From all those, get the maximum value.
    # The pagination div is not even present when there's only one page.
    page_numbers = pages_div.xpath('a/text()[number(.) = .] | b/text()[number(.) = .]').getall()
    page_numbers = [int(i) for i in page_numbers]
    if page_numbers and len(page_numbers) > 0:
        return max(page_numbers) - 1
    else:
        return 0


def get_timestamp_from_script(script_content):
    return int(script_content[4:script_content.find(')')])


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
        'old': '<br>',
        'new': '\n',
    },
    # I can't believe I finally understand regex!! Many thanks to https://regex101.com/

    # !!! IT'S VERY IMPORTANT TO PUT THE REGEXES IN THE RIGHT ORDER !!!
    # That is, more specific regexes first, more general regexes last. For example, if we have a regex for replacing general <a> elements
    # before <a> elements linking to, say, a player profile, the general one will do the replacement first when the second one would be better.
    {
        # Take out the timestamp.
        'regex': re.compile("<div class=\"stamp\"><script>tim\(\d+?\)</script>.*?</div>", re.S),
        'lambda': lambda match: '',
    },
    {
        # Replace player mentions' HTML which includes flag pic, profile pic and profile link
        # with a simple pattern containing just the player's ID.
        'regex': re.compile("<img src=\"flags/[a-zA-Z_-]*?\.gif\" align=\"absmiddle\">.*?<a href=\"player\.php\?p=([0-9]*?)\"><img src=\"pic/(\\1|empty)\.(gif|jpg|png)\" align=\"absmiddle\" width=\"24\" height=\"24\">[^<]*?</a>", re.S),
        'lambda': lambda match: '<player[' + match.group(1) + ']>()',
    },
    {
        # Replace game replay links.
        'regex': re.compile("<a href=\"game\.php\?g=(\d+?)\"><img src=\"img/minibikeicon\.gif\">(.*?)</a>", re.S),
        'lambda': lambda match: '<game[' + match.group(1) + ']>(' + match.group(2) + ')',
    },
    {
        # Replace HoF links.
        'regex': re.compile("<a href=\"view\.php\?c=(\d+?)\"><img src=\"img/hof\.gif\" border=\"0\">(.*?)</a>", re.S),
        'lambda': lambda match: '<hof[' + match.group(1) + ']>(' + match.group(2) + ')',
    },
    {
        # Replace email links.
        'regex': re.compile("<a href=\"mailto:(.*?)\"><img src=\"img/mail\.gif\" border=\"0\">(.*?)</a>", re.S),
        'lambda': lambda match: '<email[' + match.group(1) + ']>(' + match.group(2) + ')',
    },
    {
        # Replace external links.
        'regex': re.compile("<a href=\"http[s]?://(\\S+)?\" target=\"_blank\"><img src=\"img/extlink.gif\" border=\"0\">(.*?)</a>", re.S),
        'lambda': lambda match: '[' + match.group(1) + '](' + match.group(2) + ')',
    },
    {
        # Replace another form of external links.
        'regex': re.compile("<a href=\"http[s]?://(\\S+)?\">(.*?)</a>", re.S),
        'lambda': lambda match: '[' + match.group(1) + '](' + match.group(2) + ')',
    },
    {
        # At this point any remaining link is relative to http://bike.toyspring.com/ and is probably a file, convert it to absolute path in order to enable download.
        'regex': re.compile("<a href=\"(\\S+)?\">(.*?)</a>", re.S),
        'lambda': lambda match: '[http://bike.toyspring.com/' + match.group(1) + '](' + match.group(2) + ')',
    },
]

bod_file_regex = re.compile('\[(http://bike\.toyspring\.com/.*?)\]', re.S)


def process_user_text(user_text):
    for replacement in comment_replacements:
        if replacement.get('old'):
            # This is a simple replacement.
            user_text = user_text.replace(replacement['old'], replacement['new'])
        else:
            # This replacement uses regex.
            user_text = replacement['regex'].sub(
                replacement['lambda'],
                user_text
            )

    return user_text


def process_comments(comments_table_rows, comments_container, response):
    comments = comments_container.get('comments') or []
    pinned_comments = comments_container.get('pinned_comments') or []
    file_urls = comments_container.get('file_urls') or []

    for row in comments_table_rows:
        comment_selector = row.xpath('descendant::td[@class = "bubble"]')

        # Pinned comments have the "bubble_pin" class instead of "bubble". If "bubble" is not found,
        # look for "bubble_pin" and take it as a pinned comment.
        pinned = False
        if not comment_selector:
            comment_selector = row.xpath('descendant::td[@class = "bubble_pin"]')
            pinned = True

        if not comment_selector:
            # This is an empty row used as spacer.
            continue

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

        comment = {}
        if comment_id:
            comment['comment_id'] = comment_id

        player_id = row.xpath('substring(td/a[starts-with(@href, "player.php?p=")]/@href, 14)').get()
        if player_id:
            comment['player_id'] = int(player_id)

        content = ''.join(comment_selector.xpath('node()').getall())

        if content.find('<a name="c') > -1:
            # Strip the anchor with the comment ID from the HTML, which I assume is always the first anchor.
            content = content[content.find('"></a>') + 6:]

        # descendant-or-self is used because there's an edge case where the content includes <li> elements
        # and the timestamp script is included in the last of them for whatever reason.
        date = row.xpath('descendant-or-self::div[@class = "stamp"]/script/text()').get()
        if date:
            comment['date'] = get_timestamp_from_script(date)

        content = process_user_text(content)

        comment['content'] = content
        # Download every image that might remain after the replacements.
        for img in Selector(text=content).xpath('//img/@src').getall():
            file_urls.append(response.urljoin(img))

        # Download files from the site.
        search_results = bod_file_regex.search(content)
        if search_results:
            for file in search_results.groups():
                file_urls.append(file)

        if pinned:
            pinned_comments.append(comment)
        else:
            comments.append(comment)

    if len(comments) > 0:
        comments_container['comments'] = comments
    if len(pinned_comments) > 0:
        comments_container['pinned_comments'] = pinned_comments
    if len(file_urls) > 0:
        comments_container['file_urls'] = file_urls
