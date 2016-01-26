import scrapy,re,sys
from rankings.items import RankingsItem
from datetime import datetime,date,timedelta

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

class allgamesSpider(scrapy.Spider):
    name = "rankings"
    allowed_domains = ["espn.go.com"]


    # db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")
    # c = db.cursor()
    # c.execute("""SELECT MAX(time) from games""")
    # startdate = c.fetchone()[0].date()

    start_urls = ['http://espn.go.com/mens-college-basketball/bpi']

    def parse(self, response):
      print '* '*50
      item = RankingsItem()
      item['day'] = date.today()
      for sel in response.xpath("//tr[contains(@class, 'evenrow')]"):
        item['team'] = sel.xpath("td[position()=2]/a/@href").extract()[0].split('/')[-1]
        item['ranking'] = sel.xpath("td[position()=4]/text()").extract()
        yield item
      for sel in response.xpath("//tr[contains(@class, 'oddrow')]"):
        item['team'] = sel.xpath("td[position()=2]/a/@href").extract()[0].split('/')[-1]
        item['ranking'] = sel.xpath("td[position()=4]/text()").extract()
        yield item
