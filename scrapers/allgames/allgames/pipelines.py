# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql

class AllgamesPipeline(object):

    dbc = json.load(open('../../../credentials/db.json','rb'))
    live = dbc[dbc['live']]
    db = pymysql.connect(live['host'],live['user'],live['pw'],live['db'],charset="utf8",cursorclass=pymysql.cursors.DictCursor)


    def process_item(self, item, spider):
      c = self.db.cursor()
      print item
      print '* '*50
      c.execute("""INSERT IGNORE INTO games (gameid,gametime) VALUES (%s,%s)""",
                (item['gid'],item['gameday'])
                 )
      c.execute("""UPDATE games set season=2015 WHERE gametime > '2015-07-01' and gametime < '2016-07-01'""")
      self.db.commit()
      return item
