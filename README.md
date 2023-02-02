# bike.toyspring.com scrapper

A program to scrape the Bike or Die website data for preservation purposes, in anticipation of a permanent shutdown.
Currently, only player profile downloading is (partially) supported.

## How to use

1. Clone the repo.
2. Make sure that you have `python3` and `pip` installed. This was tested on Debian 11.
3. Install [Scrapy](https://docs.scrapy.org/en/latest/intro/install.html).
4. Run `scrapy crawl players -O players.json`. Wait for completion.

Disclaimer: I'm currently a Python and XPath n00b, this code could probably be improved but it seems to work as it is right now. I'm open to suggestions and useful advice!

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
