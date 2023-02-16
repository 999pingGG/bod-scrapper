# bike.toyspring.com scrapper

A program to scrape the Bike or Die website data for preservation purposes, in anticipation of a permanent shutdown. The ultimate goal is to be able to clone the website along with its publicly available data and host it myself. This project focuses on downloading all the available data as JSON, even if there's some redundancy between the different endpoints used and even if some "stray" data is obtained; for example, game replays without an associated player. In order to be able to fully clone the website it is necessary to dump the JSONs into a proper database, download the original site's HTML pages to adapt and use them as templates (or remaster them), and make a proper backend and frontend.

Disclaimer: I'm currently a Python and XPath n00b, this code can be improved but it works as it is right now. I'm open to suggestions and useful advice!

## How to use

1. Clone the repo.
2. Make sure that you have `python3` and `pip` installed. This was tested on Debian 11.
3. Install [Scrapy](https://docs.scrapy.org/en/latest/intro/install.html) and [Psycopg](https://www.psycopg.org/docs/install.html).
4. `cd` into the repo directory.
5. Run `scrapy crawl <spider> [PostgreSQL connection] -O <json file>`. Wait for completion.

You can optionally dump the data into a PostgreSQL database by providing a few settings in the form `-a <setting>=<value>`. If you don't provide them, no problem, the data will be saved as JSON in all cases. A SQL Script is included to automatically setup the required database. The scrapper will overwrite existing data.

The settings are as follows:

| Setting    | Default     | Required |
| ---------- | ----------- | -------- |
| `host`     | `localhost` | No       |
| `port`     | `5432`      | No       |
| `dbname`   | None        | Yes      |
| `user`     | None        | Yes      |
| `password` | None        | Yes      |

Example:

`scrapy crawl players -a host="192.168.1.117" -a dbname="sitedata" -a user="admin" -a password="somethingsomething" -O data.json`

## Available spiders

1. `players` (completed)
2. `levelpacks` (completed)
3. `levels` (completed)
4. `games` (completed)
5. `movies` (completed)
6. `hof` (completed)
7. `freestyle` (completed)
8. `forum` (completed)

## Standalone scripts

### scrap_files.py

This script bruteforces `getfile.php`. Use it simply with `python3 scrap_files.py`. This should, in theory, download every existent levelpack, but apparently some of them are available only under `levels/` through their exact name. The levelpack spider should be able to grab every levelpack.

## Known issues

- The `hof`, `freestyle` and `forum` spiders have hardcoded data to save dev time on something that is very unlikely to change in the future. Unless, you know, Sz performs a comeback... Please Sz, come back home.
- The following levelpack's name seems to break Scrapy or its underlying XML parser library, yielding a whitespace name: `http://bike.toyspring.com/levels.php?p=65`. I wonder whether other stuff breaks like this and goes unnoticed...?

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
