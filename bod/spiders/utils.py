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


def process_comments(comments_table, comments_container, response):
    comments = comments_container.get('comments') or []
    pinned_comments = comments_container.get('pinned_comments') or []
    file_urls = comments_container.get('file_urls') or []

    # Get all the tr's that contain a td with a table, to filter out an empty row which appears
    # when there's a pinned comment.
    for row in comments_table:
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
            print('Comment has no ID!')
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
        for img in Selector(text=content).xpath('//img/@src').getall():
            file_urls.append(response.urljoin(img))

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
