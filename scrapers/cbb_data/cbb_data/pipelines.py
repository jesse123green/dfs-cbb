# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql

class CbbDataPipeline(object):

  db = pymysql.connect("localhost","cbb","","cbb",charset="utf8")

  def process_item(self, item, spider):
    c = self.db.cursor()

    print item['gametime']
    c.execute("""SELECT gametime FROM games where gameid=%s""",(item['gameid'],))
    gametime = c.fetchone()[0]

    c.execute("""UPDATE games SET home=%s,away=%s WHERE gameid=%s""",
              (item['hometeamid'],item['awayteamid'],item['gameid'])
               )
    c.execute("""INSERT IGNORE INTO players (pid,name) VALUES (%s, %s)""",
              (item['playerid'], item['playername'])
               )
    c.execute("""INSERT IGNORE INTO teams (team,name) VALUES (%s, %s)""",
              (item['hometeamid'], item['hometeamname'])
               )
    c.execute("""INSERT IGNORE INTO teams (team,name) VALUES (%s, %s)""",
              (item['awayteamid'], item['awayteamname'])
               )

    c.execute("""INSERT IGNORE INTO gamelog (pid,gameid,team,home,away,gametime,pos,min,fgm,fga,tpm,tpa,ftm,fta,oreb,dreb,reb,ast,stl,blk,tov,pf,pts) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
              (item['playerid'], item['gameid'],item['teamid'],item['hometeamid'],item['awayteamid'],gametime,item['pos'], item['min'],item['fgm'], item['fga'],item['tpm'], item['tpa'],item['ftm'], item['fta'],item['oreb'], item['dreb'],item['reb'], item['ast']\
               ,item['stl'], item['blk'],item['to'], item['pf'],item['pts'])
               )

    self.db.commit()

    return item
