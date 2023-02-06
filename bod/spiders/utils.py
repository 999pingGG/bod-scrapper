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
