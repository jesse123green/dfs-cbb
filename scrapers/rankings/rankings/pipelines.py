# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql

class RankingsPipeline(object):
  db = pymysql.connect("localhost","cbb","","cbb",charset="utf8")

  def process_item(self, item, spider):
    c = self.db.cursor()
    c.execute("""INSERT IGNORE INTO rankings (team,rank,rankdate) VALUES (%s, %s, %s)""",
              (item['team'],item['ranking'],item['day'])
               )
    self.db.commit()
    return item
