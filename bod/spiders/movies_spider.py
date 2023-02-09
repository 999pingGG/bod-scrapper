import scrapy


class Movies(scrapy.Spider):
    name = 'movies'

    def start_requests(self):
        url = 'http://bike.toyspring.com/movie.php?o=1&f='

        for i in range(1, 1000):
            yield scrapy.Request(url=url+str(i), cb_kwargs=dict(id=i))

    def parse(self, response, id):
        yield {
            'id': id,
            'movie': response.body.decode(),
        }
