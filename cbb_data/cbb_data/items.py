# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CbbDataItem(scrapy.Item):
    # define the fields for your item here like:
    hometeamid = scrapy.Field()
    awayteamid = scrapy.Field()
    hometeamname = scrapy.Field()
    awayteamname = scrapy.Field()
    gameid = scrapy.Field()
    gametime = scrapy.Field()

    ##Player stats
    playerid = scrapy.Field()
    playername = scrapy.Field()
    teamid = scrapy.Field()
    pos = scrapy.Field()
    min = scrapy.Field()
    fgm = scrapy.Field()
    fga = scrapy.Field()
    tpm = scrapy.Field()
    tpa = scrapy.Field()
    ftm = scrapy.Field()
    fta = scrapy.Field()
    oreb = scrapy.Field()
    dreb = scrapy.Field()
    reb = scrapy.Field()
    ast = scrapy.Field()
    stl = scrapy.Field()
    blk = scrapy.Field()
    to = scrapy.Field()
    pf = scrapy.Field()
    pts = scrapy.Field()
