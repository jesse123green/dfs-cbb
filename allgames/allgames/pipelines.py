# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import MySQLdb

class AllgamesPipeline(object):

    db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")

    def process_item(self, item, spider):
      c = self.db.cursor()
      print item
      print '* '*50
      c.execute("""INSERT IGNORE INTO games (home,away,time) VALUES (%s, %s, %s)""",
                (item['home'],item['away'],item['gameday'])
                 )
      self.db.commit()
      return item
