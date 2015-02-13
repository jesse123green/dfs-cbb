import scrapy,re,sys
from cbb_games.items import CbbGamesItem
from datetime import datetime,date,timedelta
import MySQLdb

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

class cbbgamesSpider(scrapy.Spider):
    name = "cbbgames"
    allowed_domains = ["espn.go.com"]


    db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")
    c = db.cursor()
    c.execute("""SELECT MAX(time) from games WHERE gid != '-1'""")

    result = c.fetchone()
    if len(result) == 0:
      startdate = date(2014,11,1)
    else:
      startdate = result[0].date() + timedelta(1)
    stopdate = date.today()

    start_urls = []

    for adate in daterange(startdate,stopdate):
      start_urls.append("http://espn.go.com/mens-college-basketball/schedule?date="+adate.strftime('%Y%m%d'))

    def parse(self, response):
      print '* '*50
      item = CbbGamesItem()
      item['gameday'] = datetime.strptime(response.url.split('=')[-1],'%Y%m%d')
      for sel in response.xpath("//tr[contains(@class, 'evenrow')]"):
        links = sel.xpath("td/a[contains(@href, 'boxscore')]/@href").extract()
        for link in links:
          item['id'] = link.split('=')[-1]
          yield item


      for sel in response.xpath("//tr[contains(@class, 'oddrow')]"):
        links = sel.xpath("td/a[contains(@href, 'boxscore')]/@href").extract()
        for link in links:
          item['id'] = link.split('=')[-1]
          yield item
