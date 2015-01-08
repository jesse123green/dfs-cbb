# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class RankingsItem(scrapy.Item):
    # define the fields for your item here like:
    day = scrapy.Field()
    team = scrapy.Field()
    ranking = scrapy.Field()
    pass
