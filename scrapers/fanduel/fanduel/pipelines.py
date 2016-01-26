# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql,csv
from datetime import date, datetime

class FanduelPipeline(object):
	db = pymysql.connect("localhost","cbb","","cbb",charset="utf8")

	def process_item(self, item, spider):

		c = self.db.cursor()

		print item
		print '!@#'
		## Dump data
		c.execute("""INSERT IGNORE INTO fanduel_contests (gameid,fid,fppg,team,opp,home,indicator,name,position,salary) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",\
		(item['gameid'],item['fid'],item['fppg'],item['team'],item['opp'],item['home'],item['indicator'],item['name'],item['position'],item['salary']))

		
		self.db.commit()
