import scrapy,re,sys
from allgames.items import AllgamesItem
from datetime import datetime,date,timedelta
import MySQLdb

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

class allgamesSpider(scrapy.Spider):
    name = "allgames"
    allowed_domains = ["espn.go.com"]


    # db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")
    # c = db.cursor()
    # c.execute("""SELECT MAX(time) from games""")
    # startdate = c.fetchone()[0].date()
    startdate = date.today()-timedelta(1)
    stopdate = date(2015,3,18)

    start_urls = []

    for adate in daterange(startdate,stopdate):
      start_urls.append("http://espn.go.com/mens-college-basketball/schedule?date="+adate.strftime('%Y%m%d'))

    def parse(self, response):
      print '* '*50
      item = AllgamesItem()
      item['gameday'] = datetime.strptime(response.url.split('=')[-1],'%Y%m%d')
      for sel in response.xpath("//tr[contains(@class, 'evenrow')]"):
        links = sel.xpath("td/a[contains(@href, 'mens-college-basketball/team')]/@href").extract()
        print links
        item['away'] = links[0].split('/')[-2]
        item['home'] = links[1].split('/')[-2]
        yield item
      for sel in response.xpath("//tr[contains(@class, 'oddrow')]"):
        links = sel.xpath("td/a[contains(@href, 'mens-college-basketball/team')]/@href").extract()
        print links
        item['away'] = links[0].split('/')[-2]
        item['home'] = links[1].split('/')[-2]
        yield item
