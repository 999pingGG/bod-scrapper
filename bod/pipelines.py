import psycopg2


def init_db(self, spider):
    if hasattr(spider, 'host'):
        host = spider.host
    else:
        host = 'localhost'

    if hasattr(spider, 'port'):
        port = spider.port
    else:
        port = '5432'

    if not hasattr(spider, 'dbname') or not hasattr(spider, 'user') or not hasattr(spider, 'password'):
        print("Data saving to database is disabled because you didn't pass the required arguments.")
        return

    self.connection = psycopg2.connect(host=host, port=port, dbname=spider.dbname, user=spider.user, password=spider.password)
    self.cursor = self.connection.cursor()


class PlayersPipeline:
    def open_spider(self, spider):
        init_db(self, spider)

    def process_item(self, item, spider):
        if self.cursor:
            pic_file_extension = item['pic_url']
            if pic_file_extension == 'http://bike.toyspring.com/pic/empty.jpg':
                pic_file_extension = None
            else:
                pic_file_extension = pic_file_extension[-3:]

            self.cursor.execute(
                'INSERT INTO player (id_player, name, pic_file_extension, id_country, city, email, homepage, last_seen) ' +
                'VALUES (%s, %s, %s, (SELECT id_country FROM country WHERE name = %s), %s, %s, %s, %s) ' +
                'ON CONFLICT (id_player) DO UPDATE SET ' +
                'name = excluded.name, ' +
                'pic_file_extension = excluded.pic_file_extension, ' +
                'id_country = excluded.id_country, ' +
                'city = excluded.city, ' +
                'email = excluded.email, ' +
                'homepage = excluded.homepage, ' +
                'last_seen = excluded.last_seen',
                (item['id'], item['name'], pic_file_extension, item.get('country'), item.get('city'), item.get('email'), item.get('homepage'), item.get('last_seen'))
            )
        return item

    def close_spider(self, spider):
        if self.connection:
            self.connection.commit()
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


month_equivalence = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12',
}


class LevelpacksPipeline:
    def open_spider(self, spider):
        init_db(self, spider)

    def process_item(self, item, spider):
        # The "levelpack" with ID 0 is a pseudo-levelpack, only used to hold the levelpack explorer comments.
        if self.cursor and item['id'] != 0:
            prc_name = item['file_urls'][0][33:-4]

            hits = item.get('hits') or 0

            creator = item.get('creator')
            if creator:
                # The creator(s) may be a player ID or a string.
                creator = str(creator)

            rating = item.get('rating')
            if rating:
                rating = rating * 4

            difficulty = item.get('difficulty')
            if difficulty:
                difficulty = difficulty * 4

            uploaded = item.get('uploaded').split()
            uploaded = uploaded[2] + '-' + month_equivalence[uploaded[1]] + '-' + uploaded[0]

            self.cursor.execute(
                'INSERT INTO levelpack (id_levelpack, name, prc_name, hits, creator, rating, difficulty, uploaded, bod_version) ' +
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ' +
                'ON CONFLICT (id_levelpack) DO UPDATE SET ' +
                'name = excluded.name, ' +
                'prc_name = excluded.prc_name, ' +
                'hits = excluded.hits, ' +
                'creator = excluded.creator, ' +
                'rating = excluded.rating, ' +
                'difficulty = excluded.difficulty, ' +
                'uploaded = excluded.uploaded, ' +
                'bod_version = excluded.bod_version',
                (item['id'], item['name'], prc_name, hits, creator, rating, difficulty, uploaded, item['bod_version'])
            )

        return item

    def close_spider(self, spider):
        if self.connection:
            self.connection.commit()
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
