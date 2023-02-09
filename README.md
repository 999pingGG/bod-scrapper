# bike.toyspring.com scrapper

A program to scrape the Bike or Die website data for preservation purposes, in anticipation of a permanent shutdown. The ultimate goal is to be able to clone the website along with its publicly available data and host it myself. This project focuses on downloading all the available data as JSON, even if there's some redundancy between the different endpoints used and even if some "stray" data is obtained; for example, game replays without an associated player. In order to be able to fully clone the website it is necessary to dump the JSONs into a proper database, download the original site's HTML pages to adapt and use them as templates (or remake them), and make a proper backend and frontend.

Disclaimer: I'm currently a Python and XPath n00b, this code could probably be improved but it seems to work as it is right now. I'm open to suggestions and useful advice!

## How to use

1. Clone the repo.
2. Make sure that you have `python3` and `pip` installed. This was tested on Debian 11.
3. Install [Scrapy](https://docs.scrapy.org/en/latest/intro/install.html).
4. `cd` into the repo directory.
5. Run `scrapy crawl <spider> -O <json file>`. Wait for completion.

## Available spiders

1. `players` (completed)
2. `levelpacks` (completed)
3. `levels` (completed)
4. `games` (completed)
5. `movies` (completed)

## Upcoming spiders

1. `forum`
2. `hof`
3. Anything else needed to clone the website.

## Standalone scripts

### scrap_files.py

This script bruteforces `getfile.php`. Use it simply with `python3 scrap_files.py`. This should, in theory, download every existent levelpack, but apparently some of them are available only under `levels/` through their exact name. The levelpack spider should be already able to grab every levelpack.

## Known issues

- There is an unhandled edge case where there can be links in a levelpack creator field. The link and everything that comes after it is ignored.

## License

          DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                      Version 2, December 2004

    Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>

    Everyone is permitted to copy and distribute verbatim or modified
    copies of this license document, and changing it is allowed as long
    as the name is changed.

              DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
      TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

    0. You just DO WHAT THE FUCK YOU WANT TO.
