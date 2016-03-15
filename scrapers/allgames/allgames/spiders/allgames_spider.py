# -*- coding: utf-8 -*-
import scrapy,re,sys
from allgames.items import AllgamesItem
from datetime import datetime,date,timedelta
import pymysql

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

class allgamesSpider(scrapy.Spider):
    name = "allgames"
    allowed_domains = ["espn.go.com"]


    dbc = json.load(open('../../../../credentials/db.json','rb'))
    live = dbc[dbc['live']]
    db = pymysql.connect(live['host'],live['user'],live['pw'],live['db'],charset="utf8",cursorclass=pymysql.cursors.DictCursor)

    c = db.cursor()
    c.execute("""SELECT MAX(gametime) time from games""")
    startdate = c.fetchone()[0].date()
    stopdate = date.today()
    # startdate = date.today()-timedelta(1)
    # stopdate = date.today()

    start_urls = []

    for adate in daterange(startdate,stopdate):
      start_urls.append("http://espn.go.com/mens-college-basketball/schedule?date="+adate.strftime('%Y%m%d'))
    print '!!!!!!'
    print start_urls
    print '!!!!!!'

    def parse(self, response):
      print '* '*50
      item = AllgamesItem()
      item['gameday'] = datetime.strptime(response.url.split('=')[-1],'%Y%m%d')
      for sel in response.xpath("//tr[contains(@class, 'even')]"):
        links = sel.xpath("td/a[contains(@href, 'gameId=')]/@href").extract()
        print links
        item['gid'] = links[0].split('=')[-1]
        yield item
      for sel in response.xpath("//tr[contains(@class, 'odd')]"):
        links = sel.xpath("td/a[contains(@href, 'gameId=')]/@href").extract()
        print links
        item['gid'] = links[0].split('=')[-1]
        yield item
