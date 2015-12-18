# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import MySQLdb

class RankingsPipeline(object):
  db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")

  def process_item(self, item, spider):
    c = self.db.cursor()
    c.execute("""INSERT IGNORE INTO rankings (tid,rank,rankdate) VALUES (%s, %s, %s)""",
              (item['team'],item['ranking'],item['day'])
               )
    self.db.commit()
    return item
