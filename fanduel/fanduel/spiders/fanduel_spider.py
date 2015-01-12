import scrapy,re,sys
from fanduel.items import FanduelItem
from datetime import datetime,date,timedelta
import MySQLdb

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

class fanduelSpider(scrapy.Spider):
    name = "fanduel"
    allowed_domains = ["fanduel.com"]

    start_urls = ["https://www.fanduel.com/e/Game/11425?tableId=9662658&fromLobby=true"]

    def parse(self, response):

      item = FanduelItem()
      for sel in response.xpath("//tr[@data-role='player']"):
        print '* '*50
        for d in sel.xpath('.//td[@class="player-name"]'):
          item['name'] = d.xpath('div/text()').extract()[0]
        for d in sel.xpath('.//td[@class="player-fppg"]'):
          item['fppg'] = d.xpath('text()').extract()[0]
        for d in sel.xpath('.//td[@class="player-fixture"]'):
          opp = d.xpath('text()').extract()[0]
          if re.match('@',opp):
            item['home'] = 0
          else:
            item['home'] = 1
          item['opp'] = opp.replace('@','')
          item['team'] = d.xpath('b/text()').extract()[0].replace('@','')
        for d in sel.xpath('.//td[@class="player-salary"]'):
          item['salary'] = d.xpath('text()').extract()[0]
        for d in sel.xpath('.//td[@class="player-position"]'):
          item['position'] = d.xpath('text()').extract()[0]
        yield item
