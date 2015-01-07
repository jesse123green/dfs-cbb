# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import MySQLdb

class CbbDataPipeline(object):

  db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")

  def process_item(self, item, spider):
    c = self.db.cursor()
    c.execute("""UPDATE games SET home=%s, away=%s,time=%s WHERE gid=%s""",
              (item['hometeamid'], item['awayteamid'],item['gametime'],item['gameid'])
               )
    c.execute("""INSERT IGNORE INTO players (pid,name,tid) VALUES (%s, %s,%s)""",
              (item['playerid'], item['playername'], item['teamid'])
               )
    c.execute("""INSERT IGNORE INTO teams (tid,name) VALUES (%s, %s)""",
              (item['hometeamid'], item['hometeamname'])
               )
    c.execute("""INSERT IGNORE INTO teams (tid,name) VALUES (%s, %s)""",
              (item['awayteamid'], item['awayteamname'])
               )

    c.execute("""INSERT IGNORE INTO playerstats (pid,gid,pos,min,fgm,fga,tpm,tpa,ftm,fta,oreb,dreb,reb,ast,stl,blk,turnovers,pf,pts) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
              (item['playerid'], item['gameid'],item['pos'], item['min'],item['fgm'], item['fga'],item['tpm'], item['tpa'],item['ftm'], item['fta'],item['oreb'], item['dreb'],item['reb'], item['ast']\
               ,item['stl'], item['blk'],item['to'], item['pf'],item['pts'])
               )

    self.db.commit()

    return item
