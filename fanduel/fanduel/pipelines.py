# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import MySQLdb,csv
from datetime import date
from cbbplayer import Player

class FanduelPipeline(object):
  db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")
  fout = open('/Users/jesseg/Documents/fantasy/cbb/data/predictions.csv','wb')
  fout.write('Position,Player,AVGPoints,PredictedPoints,Cost\n')

  fskipped = open('/Users/jesseg/Documents/fantasy/cbb/data/skipped.csv','wb')

  def gather_player_data(self, pid, item):
    c = self.db.cursor()
    c.execute("""SELECT tid FROM teams where fanduel = %s""",(item['team'],))
    tid = c.fetchone()[0]
    c.execute("""SELECT tid FROM teams where fanduel = %s""",(item['opp'],))
    oppid = c.fetchone()[0]
    P = Player(pid,tid,item['home'],oppid)
    X = P.load_all_data()
    prediction = P.predict(X)

    self.fout.write('%s,"%s",%.2f,%.2f,"%s"\n'%(item['position'],item['name'],X[0],prediction,item['salary']))
    print 'gathering player data'


  def process_item(self, item, spider):
    today = date.today()

    c = self.db.cursor()
    print item

    ## Check if player has been processed
    c.execute("""SELECT pid,players.tid FROM players,teams WHERE players.fanduel =%s and teams.fanduel=%s and players.tid = teams.tid""",\
              (item['name'],item['team']))
    result = c.fetchone()
    if result is not None:
      self.gather_player_data(result[0],item)
    else:
      self.fskipped.write('"%s",%s\n'%(item['name'],item['fppg']))
      c.execute("""SELECT pid,tid FROM players WHERE name LIKE "%s" OR name LIKE "%s" """%(item['name'],item['name'].replace('.','').replace(',','')))
      result = c.fetchall()
      print result
      if len(result) == 0:
        print 'NO MATCH',item['name'],item['team']
      elif len(result) == 1:
        c.execute("""UPDATE players SET fanduel = %s WHERE pid = %s""",(item['name'],result[0][0]))
        c.execute("""UPDATE teams SET fanduel = %s WHERE tid = %s""",(item['team'],result[0][1]))
      else:
        print 'MULTIPLE MATCHES',item['name'],item['team']

      self.db.commit()
