# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import MySQLdb,csv
from datetime import date
from cbbplayer import Player


class FanduelPipeline(object):

  model_thresh = 8
  model_loss = 'l1'
  model = 'en'

  db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")
  fout = open('/Users/jesseg/Documents/fantasy/cbb/data/predictions%i_%s_%s.csv'%(model_thresh,model_loss,model),'wb')

  fout.write('Position,Player,Team,Opponent,isHome,AVGPoints,PredictedPoints,Cost\n')
  fskipped = open('/Users/jesseg/Documents/fantasy/cbb/data/skipped.csv','wb')
  k = 0

  def gather_player_data(self, pid, item):
    c = self.db.cursor()
    c.execute("""SELECT tid FROM teams where fanduel = %s""",(item['team'],))
    tid = c.fetchone()[0]
    c.execute("""SELECT tid FROM teams where fanduel = %s""",(item['opp'],))
    oppid = c.fetchone()[0]
    P = Player(pid,tid,item['home'],oppid,self.model_thresh,self.model_loss,self.model)
    X = P.load_all_data()
    prediction = P.predict(X)
    self.fout.write('%s,"%s",%s,%s,%i,%.2f,%.2f,"%s"\n'%(item['position'],item['name'],item['team'],item['opp'],item['home'],X[0],prediction,item['salary']))
    print 'gathering player data'


  def process_item(self, item, spider):
    today = date.today()

    c = self.db.cursor()
    print item

    ## Check if player has been processed
    c.execute("""SELECT pid,players.tid FROM players,teams WHERE players.fanduel =%s and teams.fanduel=%s and players.tid = teams.tid""",\
              (item['name'],item['team']))
    result = c.fetchone()
    if (result is not None) and (item['isEligible']):
      self.gather_player_data(result[0],item)
    else:
      query = """SELECT pid,tid FROM players WHERE name LIKE '%%%s%%' OR name LIKE '%%%s%%' """%(item['name'],item['name'].replace('.','').replace(',',''))
      print query
      c.execute(query)
      result = c.fetchall()
      print result
      if not(item['isEligible']):
        reason = 'Not Eligible'
      elif len(result) == 0:
        print 'NO MATCH',item['name'],item['team']
        reason = 'No match'
      elif len(result) == 1:
        reason = 'Not Yet Processed'
        c.execute("""UPDATE players SET fanduel = %s WHERE pid = %s""",(item['name'],result[0][0]))
        c.execute("""UPDATE teams SET fanduel = %s WHERE tid = %s""",(item['team'],result[0][1]))
      else:
        print 'MULTIPLE MATCHES',item['name'],item['team']
        reason = 'Multiple'

      self.fskipped.write('"%s",%s,%s,%s\n'%(item['name'],item['fppg'],item['team'],reason))
      self.db.commit()
