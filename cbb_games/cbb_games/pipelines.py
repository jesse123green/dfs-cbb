# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import re,sys,datetime
import MySQLdb

class CbbGamesPipeline(object):

  # fout = open('game_links_' + datetime.date.today().strftime('%Y%m%d') + '.csv', 'wb')
  db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")

  def process_item(self, item, spider):
    # self.fout.write('%s\n'%item['id'])
    c = self.db.cursor()
    c.execute("""INSERT IGNORE INTO games (gid,time) VALUES (%s, %s)""",
              (item['id'],item['gameday'])
               )
    self.db.commit()
    return item
