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
from sklearn.metrics import mean_squared_error,mean_absolute_error
import pylab as plt
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC,SVR
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.decomposition import PCA
from sklearn.tree import DecisionTreeClassifier
import MySQLdb
from scipy.misc import comb
# import warnings
# warnings.filterwarnings("ignore")

class CBB():

  def __init__(self):
    self.db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")
    self.pre_processors = {}
    self.feature_headers = []
    # self.transformations = transformations
    # self.yheader = 'customer_cancelation_date'


  def daterange(self,start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

  def combine_features(self,X,xnew):
    xnew = np.array(xnew,dtype=float)
    if len(xnew.shape) == 1:
      xnew = xnew.reshape(xnew.shape[0], 1)
    return np.concatenate((X,xnew),axis=1)

  def load_data(self,min_games=6):
    c = self.db.cursor()
    X = []
    y = []
    c.execute("""SELECT DATE(MIN(time)),DATE(MAX(time)) from games WHERE gid != '-1'""")
    days = c.fetchone()

    k = 0
    for aday in self.daterange(days[1]-timedelta(31),days[1]+timedelta(1)):
    # for aday in self.daterange(days[0],days[1]+timedelta(1)):
      # c.execute("SELECT today.pid,today.gid,(today.pts+today.reb*1.2+today.ast*1.5+today.blk*2+today.stl*2-today.turnovers) fp,hist.avg_fgm,hist.avg_fga,hist.avg_tpm,hist.avg_tpa,hist.avg_ftm,hist.avg_fta,hist.avg_oreb,hist.avg_dreb,hist.avg_reb,hist.avg_ast,hist.avg_stl,hist.avg_blk,hist.avg_turnovers,hist.avg_pf,hist.avg_pts FROM (select pid,avg(fgm) avg_fgm,avg(fga) avg_fga,avg(tpm) avg_tpm,avg(tpa) avg_tpa,avg(ftm) avg_ftm,avg(fta) avg_fta,avg(oreb) avg_oreb,avg(dreb) avg_dreb,avg(reb) avg_reb,avg(ast) avg_ast,avg(stl) avg_stl,avg(blk) avg_blk,avg(turnovers) avg_turnovers,avg(pf) avg_pf,avg(pts) avg_pts from playerstats,games WHERE games.gid=playerstats.gid AND time < %s group by pid having count(pid) > 5) AS hist,(SELECT games.gid,pid,pts,reb,ast,blk,stl,turnovers FROM playerstats,games WHERE games.gid=playerstats.gid and date(time) = %s) AS today WHERE hist.pid = today.pid order by today.gid,today.pid;",
      # (aday,aday))
      c.execute("SELECT today.pid,today.gid,(today.pts+today.reb*1.2+today.ast*1.5+today.blk*2+today.stl*2-today.turnovers) fp,\
      (hist.avg_pts+hist.avg_reb*1.2+hist.avg_ast*1.5+hist.avg_blk*2+hist.avg_stl*2-hist.avg_turnovers) fph,hist.avg_fgm,hist.avg_fga,hist.avg_tpm,hist.avg_tpa,hist.avg_ftm,hist.avg_fta,hist.avg_oreb,hist.avg_dreb,hist.avg_reb,hist.avg_ast,hist.avg_stl,hist.avg_blk,hist.avg_turnovers,hist.avg_pf,hist.avg_pts FROM (select pid,avg(fgm) avg_fgm,avg(fga) avg_fga,avg(tpm) avg_tpm,avg(tpa) avg_tpa,avg(ftm) avg_ftm,avg(fta) avg_fta,avg(oreb) avg_oreb,avg(dreb) avg_dreb,avg(reb) avg_reb,avg(ast) avg_ast,avg(stl) avg_stl,avg(blk) avg_blk,avg(turnovers) avg_turnovers,avg(pf) avg_pf,avg(pts) avg_pts from playerstats,games WHERE games.gid=playerstats.gid AND time < %s group by pid having count(pid) > %s) AS hist,(SELECT games.gid,pid,pts,reb,ast,blk,stl,turnovers FROM playerstats,games WHERE games.gid=playerstats.gid and date(time) = %s) AS today WHERE hist.pid = today.pid order by today.gid,today.pid;",
      (aday,min_games,aday))
      #
      # c.execute("SELECT today.pid,today.gid,(today.pts+today.reb*1.2+today.ast*1.5+today.blk*2+today.stl*2-today.turnovers) fp,(hist.avg_pts+hist.avg_reb*1.2+hist.avg_ast*1.5+hist.avg_blk*2+hist.avg_stl*2-hist.avg_turnovers) fph FROM (select pid,avg(fgm) avg_fgm,avg(fga) avg_fga,avg(tpm) avg_tpm,avg(tpa) avg_tpa,avg(ftm) avg_ftm,avg(fta) avg_fta,avg(oreb) avg_oreb,avg(dreb) avg_dreb,avg(reb) avg_reb,avg(ast) avg_ast,avg(stl) avg_stl,avg(blk) avg_blk,avg(turnovers) avg_turnovers,avg(pf) avg_pf,avg(pts) avg_pts from playerstats,games WHERE games.gid=playerstats.gid AND time < %s group by pid having count(pid) > 5) AS hist,(SELECT games.gid,pid,pts,reb,ast,blk,stl,turnovers FROM playerstats,games WHERE games.gid=playerstats.gid and date(time) = %s) AS today WHERE hist.pid = today.pid order by today.gid,today.pid;",
      # (aday,aday))
      for d in c.fetchall():
        self.feature_headers.append(d[:2])
        X.append(d[3:])
        y.append(d[2])

    return np.array(X,dtype=float),np.array(y,dtype=float)

  def home_away(self,X,y):
    c = self.db.cursor()
    homeaway = []
    X_trim = []
    y_trim = []
    feature_headers = []
    k = 0
    for row in self.feature_headers:
      c.execute("SELECT tid,home,away FROM games,players WHERE games.gid = %s and players.pid = %s",(row[1],row[0]))
      result = c.fetchone()
      if result[0] == result[1]:
        X_trim.append(X[k,:])
        y_trim.append(y[k])
        homeaway.append(1)
        feature_headers.append(row)
      elif result[0] == result[2]:
        X_trim.append(X[k,:])
        y_trim.append(y[k])
        homeaway.append(0)
        feature_headers.append(row)
      else:
        pass
      k += 1
    X_trim = np.array(X_trim,dtype=float)
    self.feature_headers = feature_headers
    return self.combine_features(X_trim,homeaway),np.array(y_trim,dtype=float)

  def opp_hist_rank(self,X):
    c = self.db.cursor()
    c2 = self.db.cursor()
    hist_ranks = []

    for row in self.feature_headers:
      c.execute("SELECT tid,home,away,gid FROM games,players,(SELECT time from games WHERE gid = %s) as curr_game WHERE (games.home = players.tid or games.away = players.tid) and players.pid = %s and games.time < curr_game.time",(row[1],row[0]))
      ranks = []
      for result in c.fetchall():
        if result[0] == result[1]:
          team = result[2]
        else:
          team = result[1]
        # print '* '*50
        # print team,result[3]
        c2.execute("SELECT rank from rankings,games where tid = %s and gid = %s and rankings.rankdate >= date(games.time) order by rankings.rankdate asc limit 1",(team,result[3]))
        rank = c2.fetchone()
        if rank:
          ranks.append(rank[0])
        else:
          ranks.append(20)
      # print '-------------->',ranks,np.mean(ranks)
      hist_ranks.append(np.mean(ranks))

    return self.combine_features(X,hist_ranks)


  def add_team_averages(self,X,y,isopp):

    c = self.db.cursor()
    feature_headers = []
    teamstats = []
    y_trim = []
    X_trim = []
    k = 0
    for row in self.feature_headers:
      c.execute("SELECT tid,home,away FROM games,players WHERE games.gid = %s and players.pid = %s",(row[1],row[0]))
      result = c.fetchone()
      if result[0] == result[1]:
        team = result[0]
        opp = result[2]
      elif result[0] == result[2]:
        team = result[0]
        opp = result[1]
      else:
        continue

      if isopp == 0:
        teamid = team
      else:
        teamid = opp

      c.execute("SELECT sum(fgm)/count(DISTINCT(histgames.gid)) avg_fgm,sum(fga)/count(DISTINCT(histgames.gid)) avg_fga,sum(tpm)/count(DISTINCT(histgames.gid)) avg_tpm,sum(tpa)/count(DISTINCT(histgames.gid)) avg_tpa,sum(ftm)/count(DISTINCT(histgames.gid)) avg_ftm,sum(fta)/count(DISTINCT(histgames.gid)) avg_fta,sum(oreb)/count(DISTINCT(histgames.gid)) avg_oreb,sum(dreb)/count(DISTINCT(histgames.gid)) avg_dreb,sum(reb)/count(DISTINCT(histgames.gid)) avg_reb,sum(ast)/count(DISTINCT(histgames.gid)) avg_ast,sum(stl)/count(DISTINCT(histgames.gid)) avg_stl,sum(blk)/count(DISTINCT(histgames.gid)) avg_blk,sum(turnovers)/count(DISTINCT(histgames.gid)) avg_turnovers,sum(pf)/count(DISTINCT(histgames.gid)) avg_pf,sum(pts)/count(DISTINCT(histgames.gid)) avg_pts  FROM  (SELECT gid FROM games,(SELECT time from games where gid = %s) as gametime WHERE games.time < gametime.time) as histgames,playerstats,players WHERE playerstats.pid = players.pid and histgames.gid = playerstats.gid and players.tid=%s",\
      (row[1],teamid))
      # print row[0],row[1],teamid,c.fetchone()
      result = c.fetchone()
      if result[0] is not None:
        X_trim.append(X[k,:])
        y_trim.append(y[k])

        teamstats.append(list(result))
        feature_headers.append(row)
      else:
        pass
      k += 1
    X_trim = np.array(X_trim,dtype=float)
    self.feature_headers = feature_headers
    return self.combine_features(X_trim,teamstats),np.array(y_trim,dtype=float)


  def add_team_rankings(self,X,y):

    c = self.db.cursor()
    c2 = self.db.cursor()
    teamrankings = []
    homeaway = []
    X_trim = []
    y_trim = []
    k = 0
    feature_headers = []

    for row in self.feature_headers:
      c.execute("SELECT tid,home,away,time FROM games,players WHERE games.gid = %s and players.pid = %s",(row[1],row[0]))
      result = c.fetchone()
      if result[0] == result[1]:
        team = result[0]
        opp = result[2]
      elif result[0] == result[2]:
        team = result[0]
        opp = result[1]
      else:
        continue
      c.execute("SELECT rank FROM rankings WHERE tid=%s and rankdate >= %s order by rankdate asc",(team,result[3]))
      c2.execute("SELECT rank FROM rankings WHERE tid=%s and rankdate >= %s order by rankdate asc",(opp,result[3]))
      teamresults = c.fetchone()
      oppresults = c2.fetchone()
      if (teamresults is not None and oppresults is not None):
        teamrankings.append([teamresults[0],oppresults[0],float(teamresults[0])-float(oppresults[0])])
        X_trim.append(X[k,:])
        y_trim.append(y[k])
        feature_headers.append(row)
      k += 1
    self.feature_headers = feature_headers
    return self.combine_features(X_trim,teamrankings),np.array(y_trim,dtype=float)


  def player_last_n_games(self,X,n=6):

    c = self.db.cursor()
    c2 = self.db.cursor()
    all_stats = []
    k = 0
    feature_headers = []

    for row in self.feature_headers:
      stats = []
      c.execute("SELECT tid,home,away,date(cgame.time),fgm,fga,tpm,tpa,ftm,fta,oreb,dreb,reb,ast,stl,blk,turnovers,pf,pts FROM games,players,playerstats,(SELECT time from games where gid = %s) as cgame WHERE games.time < cgame.time and playerstats.pid = %s and players.pid = playerstats.pid and games.gid=playerstats.gid order by games.time desc LIMIT %s",(row[1],row[0],n))
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
      #   print game2
      # print row
      # print '-'*50
      all_stats.append(np.reshape(stats,(17*n,)))

    return self.combine_features(X,all_stats)

  def date_weekday(self,X): # Extracts integer weekday from date (0-6)
    X_transformed = []
    for k in range(len(X)):
      dto = datetime.strptime(X[k],"%Y-%m-%d %H:%M:%S")
      X_transformed.append(dto.weekday())

    return np.array(X_transformed)

  def date_hour(self,X): # Extracts integer hour from datetime
    X_transformed = []
    for k in range(len(X)):
      dto = datetime.strptime(X[k],"%Y-%m-%d %H:%M:%S")
      X_transformed.append(dto.hour)

    return np.array(X_transformed)

  def daydiff(self,X1,X2): # Difference in days between two dates
    X_transformed = []
    for k in range(len(X1)):
      d1 = datetime.strptime(X1[k],"%Y-%m-%d %H:%M:%S")
      d2 = datetime.strptime(X2[k],"%Y-%m-%d %H:%M:%S")
      X_transformed.append((d1-d2).days)
    return np.array(X_transformed)

  def modulate_features(self,X):
    features_start = X.shape[1]

    new_fea_num = int(comb(features_start,2)) + features_start
    Xnew = np.zeros((X.shape[0],new_fea_num),dtype=float)

    Xnew[:,:features_start] = X
    i = features_start
    for k in range(features_start-1):
      for j in range(k+1,features_start):
        Xnew[:,i] = X[:,k]*X[:,j]
        i += 1
    return Xnew

  def train_predict(self,clf,X,y,cv):
    ## Train model clf, predict probabilities, and determine best threshold

    all_scores = []
    for train, test in cv:
        X_train, X_test, y_train, y_test = X[train,:], X[test,:], y[train], y[test]

        # all_scores.append(mean_squared_error(y_test,X_test[:,-1]))
        # continue

        clf.fit(X_train, y_train)
        # y_pred = np.exp(clf.predict(X_test))
        # y_test = np.exp(y_test)

        y_pred = clf.predict(X_test)
        # all_scores.append(mean_squared_error(y_test,y_pred))
        all_scores.append(mean_absolute_error(y_test,y_pred))


    return np.mean(all_scores)

if __name__ == "__main__":

  ## Load features to use from file
  # features = json.load(open('../data/features.json','rb'))
  t = time.time()
  ti= time.time()
  H = CBB()

  print 'Loading intial data...'
  X,y = H.load_data()
  print 'Finished after %.2f mins\n'%((time.time()-t)/60.)
  ti= time.time()

  print 'Adding home/away...'
  X,y = H.home_away(X,y)
  print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
  ti= time.time()

  print 'Adding team rankings...'
  X,y = H.add_team_rankings(X,y)
  print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
  ti= time.time()

  print 'Adding player game stats...'
  X = H.player_last_n_games(X,5)
  print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
  ti= time.time()

  print 'Adding team stats...'
  X,y = H.add_team_averages(X,y,0)
  print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
  ti= time.time()
  #
  print 'Adding opponent stats...'
  X,y = H.add_team_averages(X,y,1)
  print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
  ti= time.time()

  # print 'Adding opponent historical rank avg...'
  # X = H.opp_hist_rank(X)
  # print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
  # ti= time.time()

  # print 'Modulating features'
  # X = H.modulate_features(X)
  # print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
  # ti= time.time()

  print 'Total time: %.2f mins\n'%((time.time()-t)/60.)
  ti= time.time()

  print 'Train data shape:',X.shape
  print "Accuracy using unweighted fp mean: %.2f"%mean_squared_error(X[:,0],y)

  pickle.dump(X,open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/dataX_5all_2.p','wb'))
  pickle.dump(y,open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/datay_5all_2.p','wb'))

  sys.exit()
  ## Random Forest Model
  # clf = RF(n_estimators=250, n_jobs=3,bootstrap=False,min_samples_leaf=1, min_samples_split=4, criterion='entropy', max_features=30, max_depth=None)
  # clf = RF(n_estimators = 250, n_jobs = 3,max_features=30)
  # clf = LinearRegression()

  clf = Pipeline([
  ('scale', preprocessing.StandardScaler()),
  ('classification', SVR())
  ])

  cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=1,test_size=0.2,random_state=18)

  score = H.train_predict(clf,X,y,cv)


  print 'Accuracy score: %.2f\n'%(score)
