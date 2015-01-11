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

import warnings
warnings.filterwarnings("ignore")

class Player():

  def __init__(self,pid,tid,home,oppid):
    self.db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")
    self.pid = pid
    self.tid = tid
    self.home = home
    self.oppid = oppid

  def load_all_data(self):
    X = []
    X = self.load_player_stats(X)
    X.append(self.home)
    X = self.add_team_rankings(X)
    X = self.add_team_averages(X,0)
    X = self.add_team_averages(X,1)

    return X

  def load_player_stats(self,X):
    c = self.db.cursor()

    c.execute("SELECT (avg(pts)+avg(reb)*1.2+avg(ast)*1.5+avg(blk)*2+avg(stl)*2-avg(turnovers)) fph,avg(fgm),avg(fga),avg(tpm),avg(tpa),avg(ftm),avg(fta),avg(oreb),avg(dreb),avg(reb),avg(ast),avg(stl),avg(blk),avg(turnovers),avg(pf),avg(pts) FROM playerstats WHERE pid = %s GROUP BY pid",
    (self.pid,))

    result = c.fetchone()
    for x in result:
      X.append(x)

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

  def predict(self,X):
    ## Train model clf, predict probabilities, and determine best threshold
    clf = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data/model.p','rb'))
    return clf.predict(X)

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
