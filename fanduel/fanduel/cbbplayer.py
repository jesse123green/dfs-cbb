import numpy as np
import time,pickle
from datetime import datetime,date,timedelta
import csv, sys, json
from sklearn import preprocessing,decomposition
from sklearn.ensemble import RandomForestRegressor as RF
from sklearn.ensemble import ExtraTreesClassifier,AdaBoostClassifier,GradientBoostingClassifier
from sklearn.cross_validation import StratifiedKFold as KFold
from sklearn import cross_validation
from sklearn.linear_model import LinearRegression,SGDRegressor
from sklearn.metrics import mean_squared_error
import pylab as plt
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.decomposition import PCA
from sklearn.tree import DecisionTreeClassifier
import MySQLdb
from scipy.misc import comb

import warnings
warnings.filterwarnings("ignore")

class Player():

  def __init__(self,pid,tid,home,oppid,model_thresh,model_loss,model):
    self.db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")
    self.pid = pid
    self.tid = tid
    self.home = home
    self.oppid = oppid
    self.clf = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data/model_5all_%i_%s_%s.p'%(model_thresh,model_loss,model),'rb'))

  def load_all_data(self):
    X = []
    X = self.load_player_stats(X)
    X.append(self.home)
    X = self.add_team_rankings(X)
    X = self.player_last_n_games(X,5)
    X = self.add_team_averages(X,0)
    X = self.add_team_averages(X,1)
    # X = self.modulate_features(X)

    return X

  def load_player_stats(self,X):
    c = self.db.cursor()

    c.execute("SELECT (avg(pts)+avg(reb)*1.2+avg(ast)*1.5+avg(blk)*2+avg(stl)*2-avg(turnovers)) fph,avg(fgm),avg(fga),avg(tpm),avg(tpa),avg(ftm),avg(fta),avg(oreb),avg(dreb),avg(reb),avg(ast),avg(stl),avg(blk),avg(turnovers),avg(pf),avg(pts) FROM playerstats WHERE pid = %s GROUP BY pid",
    (self.pid,))

    result = c.fetchone()
    for x in result:
      X.append(x)

    return X

  def modulate_features(self,X):
    features_start = len(X)

    new_fea_num = int(comb(features_start,2))

    for k in range(features_start-1):
      for j in range(k+1,features_start):
        X.append(float(X[k])*float(X[j]))

    return X

  def add_team_averages(self,X,isopp):

    c = self.db.cursor()

    if isopp == 0:
      teamid = self.tid
    else:
      teamid = self.oppid

    c.execute("SELECT sum(fgm)/count(DISTINCT(gid)) avg_fgm,sum(fga)/count(DISTINCT(gid)) avg_fga,sum(tpm)/count(DISTINCT(gid)) avg_tpm,sum(tpa)/count(DISTINCT(gid)) avg_tpa,sum(ftm)/count(DISTINCT(gid)) avg_ftm,sum(fta)/count(DISTINCT(gid)) avg_fta,sum(oreb)/count(DISTINCT(gid)) avg_oreb,sum(dreb)/count(DISTINCT(gid)) avg_dreb,sum(reb)/count(DISTINCT(gid)) avg_reb,sum(ast)/count(DISTINCT(gid)) avg_ast,sum(stl)/count(DISTINCT(gid)) avg_stl,sum(blk)/count(DISTINCT(gid)) avg_blk,sum(turnovers)/count(DISTINCT(gid)) avg_turnovers,sum(pf)/count(DISTINCT(gid)) avg_pf,sum(pts)/count(DISTINCT(gid)) avg_pts FROM playerstats,players WHERE players.pid = playerstats.pid and players.tid = %s",\
    (teamid,))
    result = c.fetchone()
    for x in result:
      X.append(x)
    return X


  def add_team_rankings(self,X):

    c = self.db.cursor()
    c2 = self.db.cursor()

    c.execute("SELECT rank FROM rankings WHERE tid=%s and rankdate >= %s order by rankdate asc",(self.tid,date.today()))
    c2.execute("SELECT rank FROM rankings WHERE tid=%s and rankdate >= %s order by rankdate asc",(self.oppid,date.today()))
    teamresults = c.fetchone()
    oppresults = c2.fetchone()

    X.append(teamresults[0])
    X.append(oppresults[0])
    X.append(float(teamresults[0])-float(oppresults[0]))


    return X

  def player_last_n_games(self,X,n=5):

    c = self.db.cursor()
    c2 = self.db.cursor()
    k = 0
    feature_headers = []


    stats = []
    c.execute("SELECT tid,home,away,date(games.time),fgm,fga,tpm,tpa,ftm,fta,oreb,dreb,reb,ast,stl,blk,turnovers,pf,pts FROM games,players,playerstats WHERE playerstats.pid = %s and players.pid = playerstats.pid and games.gid=playerstats.gid order by games.time desc LIMIT %s",(self.pid,n))
    result = c.fetchall()
    for game in result:
      if game[0] == game[1]:
        home = 1
        opp = game[2]
      else:
        home = 0
        opp = game[1]
      # print opp
      c2.execute("SELECT rank FROM rankings where tid=%s and rankdate >= %s order by rankdate asc",(opp,game[3]))
      game2 = list(game[4:])
      game2.append(home)

      _rank = c2.fetchone()
      if _rank == None:
        rank = 10
      else:
        rank = _rank[0]
      game2.append(rank)
      stats.append(game2)

    if len(stats) < 5:
      print 'LESS THAN 5 DATA POINTS'
      all_stats = np.zeros((17*n,))
    else:
      all_stats = np.reshape(stats,(17*n,))
    # print '-'*50
    # print self.pid
    # print all_stats

    for s in all_stats:
      X.append(s)

    return X

  def predict(self,X):
    ## Train model clf, predict probabilities, and determine best threshold

    return self.clf.predict(X)

if __name__ == "__main__":

  ## Load features to use from file
  # features = json.load(open('../data/features.json','rb'))
  t = time.time()
  ti= time.time()
  P = Player(66256,99,1,2542)

  print 'Loading intial data...'
  X = P.load_all_data()
  print X
  print "Predicted fantasy score of %.2f"%P.predict(X)
  print 'Finished after %.2f mins\n'%((time.time()-t)/60.)
