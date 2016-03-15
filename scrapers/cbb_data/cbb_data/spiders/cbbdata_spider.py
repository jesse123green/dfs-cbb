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

    dbc = json.load(open('../../../../credentials/db.json','rb'))
    live = dbc[dbc['live']]
    db = pymysql.connect(live['host'],live['user'],live['pw'],live['db'],charset="utf8",cursorclass=pymysql.cursors.DictCursor)

    c = db.cursor()
    c.execute("""SELECT gameid from games WHERE home is null""")

    start_urls = ["http://espn.go.com/ncb/boxscore?id=" + str(game[0]) for game in c.fetchall()]

    print start_urls

    def parse(self, response):
      print '* '*50

      item = CbbDataItem()
      k = 0
      for sel in response.xpath("//div[@class='team-info']"):
        if k == 0:
          item['awayteamid'] = sel.xpath(".//a/@href").extract()[0].split('/')[-1]
          item['awayteamname'] = sel.xpath(".//a/span/text()").extract()[0]
        else:
          item['hometeamid'] = sel.xpath(".//a/@href").extract()[0].split('/')[-1]
          item['hometeamname'] = sel.xpath(".//a/span/text()").extract()[0]
        k +=1
      # for sel in response.xpath("//div[@class='team-info']"):
      #   item['hometeamid'] = sel.xpath(".//a/@href").extract()[0].split('/')[-1]
      #   item['hometeamname'] = sel.xpath(".//a/span/text()").extract()[0]
      # datestr = response.xpath("//div[@class='game-time-location']/p/text()").extract()[0]
      # if datestr[1] == ':':
      #   datestr = '0' + datestr
      # if datestr[-8] == ' ':
      #   datestr = datestr.replace(datestr[-7:],'0' + datestr[-7:])
      # datestr = datestr.replace('ET,','')
      # item['gametime'] = datetime.strptime(datestr,'%I:%M %p  %B %d, %Y')
      item['gameid'] = response.url.split('=')[-1]
      item['gametime'] = ''
      teamid_k = 0
      for game in response.xpath(".//div[@id='gamepackage-box-score']"):
        for sel in game.xpath(".//table[@class='mod-data']"):
          if teamid_k == 0:
            item['teamid'] = item['awayteamid']
          else:
            item['teamid'] = item['hometeamid']
          teamid_k += 1
          for section in sel.xpath("tbody"):
            for aplayer in section.xpath("tr"):

              player = aplayer.xpath("td/a/text()").extract()

              k += 1
              

              if len(player) == 0: # check if team stat line
                # item['teamid'] = item['hometeamid']
                continue           
              else:
                player = player[0]

              # print aplayer.xpath(".//td[@class='name']/a/text()").extract()[0]
              item['playername'] = aplayer.xpath(".//td[@class='name']/a/text()").extract()[0]
              # print '-'*30
              # print player
              try:
                item['playerid'] = int(aplayer.xpath(".//td[@class='name']/a/@href").extract()[0].split('/')[-1])
              except:
                print 'playerid error',player
                continue
              
              try:
                item['min'] = int(aplayer.xpath(".//td[@class='min']")[0].xpath("text()").extract()[0])
              except:
                item['min'] = None
              try:
                item['pos'] = aplayer.xpath(".//td[@class='name']/span[@class='position']/text()").extract()[0]
              except:
                item['pos'] = 'NA'

              try:
                item['fgm'] = int(aplayer.xpath(".//td[@class='fg']")[0].xpath("text()").extract()[0].split('-')[0])
                item['fga'] = int(aplayer.xpath(".//td[@class='fg']")[0].xpath("text()").extract()[0].split('-')[1])
                item['tpm'] = int(aplayer.xpath(".//td[@class='3pt']")[0].xpath("text()").extract()[0].split('-')[0])
                item['tpa'] = int(aplayer.xpath(".//td[@class='3pt']")[0].xpath("text()").extract()[0].split('-')[1])
                item['ftm'] = int(aplayer.xpath(".//td[@class='ft']")[0].xpath("text()").extract()[0].split('-')[0])
                item['fta'] = int(aplayer.xpath(".//td[@class='ft']")[0].xpath("text()").extract()[0].split('-')[1])
                item['oreb'] = int(aplayer.xpath(".//td[@class='oreb']")[0].xpath("text()").extract()[0])
                item['dreb'] = int(aplayer.xpath(".//td[@class='dreb']")[0].xpath("text()").extract()[0])
                item['reb'] = int(aplayer.xpath(".//td[@class='reb']")[0].xpath("text()").extract()[0])
                item['ast'] = int(aplayer.xpath(".//td[@class='ast']")[0].xpath("text()").extract()[0])
                item['stl'] = int(aplayer.xpath(".//td[@class='stl']")[0].xpath("text()").extract()[0])
                item['blk'] = int(aplayer.xpath(".//td[@class='blk']")[0].xpath("text()").extract()[0])
                item['to'] = int(aplayer.xpath(".//td[@class='to']")[0].xpath("text()").extract()[0])
                item['pf'] = int(aplayer.xpath(".//td[@class='pf']")[0].xpath("text()").extract()[0])
                item['pts'] = int(aplayer.xpath(".//td[@class='pts']")[0].xpath("text()").extract()[0])
              except:
                print 'stat error',player
                continue
              print item
              yield item
