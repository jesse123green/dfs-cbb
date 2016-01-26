# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class FanduelItem(scrapy.Item):
	# define the fields for your item here like:
	name = scrapy.Field()
	fppg = scrapy.Field()
	team = scrapy.Field()
	salary = scrapy.Field()
	opp = scrapy.Field()
	home = scrapy.Field()
	position = scrapy.Field()
	indicator = scrapy.Field()
	fid = scrapy.Field()
	gameid = scrapy.Field()
	contestday = scrapy.Field()
	pass
