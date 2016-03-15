# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql

class RankingsPipeline(object):
  dbc = json.load(open('../../../credentials/db.json','rb'))
  live = dbc[dbc['live']]
  db = pymysql.connect(live['host'],live['user'],live['pw'],live['db'],charset="utf8",cursorclass=pymysql.cursors.DictCursor)


  def process_item(self, item, spider):
    c = self.db.cursor()
    c.execute("""INSERT IGNORE INTO rankings (team,rank,rankdate) VALUES (%s, %s, %s)""",
              (item['team'],item['ranking'],item['day'])
               )
    self.db.commit()
    return item
