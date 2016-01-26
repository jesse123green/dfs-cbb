import scrapy,re,sys
from cbb_data.items import CbbDataItem
from datetime import datetime,date,timedelta
import pymysql

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

class cbbdataSpider(scrapy.Spider):
    name = "cbbdata"
    allowed_domains = ["espn.go.com"]

    db = pymysql.connect("localhost","cbb","","cbb",charset="utf8")
    c = db.cursor()
    c.execute("""SELECT gameid from games WHERE home is null""")

    start_urls = ["http://espn.go.com/ncb/boxscore?id=" + str(game[0]) for game in c.fetchall()]

    print start_urls

    def parse(self, response):
      print '* '*50

      item = CbbDataItem()
      for sel in response.xpath("//div[@class='team away']"):
        item['awayteamid'] = sel.xpath(".//a/@href").extract()[0].split('/')[-2]
        item['awayteamname'] = sel.xpath(".//a/text()").extract()[0]
      for sel in response.xpath("//div[@class='team home']"):
        item['hometeamid'] = sel.xpath(".//a/@href").extract()[0].split('/')[-2]
        item['hometeamname'] = sel.xpath(".//a/text()").extract()[0]
      datestr = response.xpath("//div[@class='game-time-location']/p/text()").extract()[0]
      if datestr[1] == ':':
        datestr = '0' + datestr
      if datestr[-8] == ' ':
        datestr = datestr.replace(datestr[-7:],'0' + datestr[-7:])
      datestr = datestr.replace('ET,','')
      item['gametime'] = datetime.strptime(datestr,'%I:%M %p  %B %d, %Y')
      item['gameid'] = response.url.split('=')[-1]

      # Player stats
      for row in ['even','odd']:
        item['teamid'] = item['awayteamid']
        for sel in response.xpath(".//tr[@class='%s']"%row):
          print '* '*30
          player = sel.xpath("td/a/text()").extract()
          if len(player) == 0: # check if team stat line
            item['teamid'] = item['hometeamid']
            continue
          else:
            player = player[0]
          item['playername'] = sel.xpath("td/a/text()").extract()[0]
          item['playerid'] = sel.xpath("td/a/@href").extract()[0].split('/')[-2]

          if (len(sel.xpath("td[position()=2]/text()").extract()[0].split('-')) == 1):
            i = 1
            item['min'] = sel.xpath("td[position()=%i]/text()"%(i+1)).extract()[0]
          else:
            item['min'] = None
            i = 0

          item['pos'] = sel.xpath("td[position()=1]/text()").extract()[0].replace(',','').strip()
          item['fgm'] = sel.xpath("td[position()=%i]/text()"%(i+2)).extract()[0].split('-')[0]
          item['fga'] = sel.xpath("td[position()=%i]/text()"%(i+2)).extract()[0].split('-')[1]
          item['tpm'] = sel.xpath("td[position()=%i]/text()"%(i+3)).extract()[0].split('-')[0]
          item['tpa'] = sel.xpath("td[position()=%i]/text()"%(i+3)).extract()[0].split('-')[1]
          item['ftm'] = sel.xpath("td[position()=%i]/text()"%(i+4)).extract()[0].split('-')[0]
          item['fta'] = sel.xpath("td[position()=%i]/text()"%(i+4)).extract()[0].split('-')[1]
          item['oreb'] = sel.xpath("td[position()=%i]/text()"%(i+5)).extract()[0]
          item['dreb'] = sel.xpath("td[position()=%i]/text()"%(i+6)).extract()[0]
          item['reb'] = sel.xpath("td[position()=%i]/text()"%(i+7)).extract()[0]
          item['ast'] = sel.xpath("td[position()=%i]/text()"%(i+8)).extract()[0]
          item['stl'] = sel.xpath("td[position()=%i]/text()"%(i+9)).extract()[0]
          item['blk'] = sel.xpath("td[position()=%i]/text()"%(i+10)).extract()[0]
          item['to'] = sel.xpath("td[position()=%i]/text()"%(i+11)).extract()[0]
          item['pf'] = sel.xpath("td[position()=%i]/text()"%(i+12)).extract()[0]
          item['pts'] = sel.xpath("td[position()=%i]/text()"%(i+13)).extract()[0]

          yield item
