import numpy as np
from datetime import datetime,date,timedelta
import csv, sys, json
from sklearn import preprocessing,decomposition
from sklearn.ensemble import RandomForestRegressor as RF
from sklearn.ensemble import ExtraTreesClassifier,AdaBoostClassifier,GradientBoostingClassifier
from sklearn.cross_validation import StratifiedKFold as KFold
from sklearn import cross_validation
from sklearn.linear_model import LogisticRegression
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

class Handy():

  def __init__(self):
    self.db = MySQLdb.connect("localhost","root","purplepants123","cbb",charset="utf8")
    self.pre_processors = {}
    self.feature_headers = []
    # self.transformations = transformations
    # self.yheader = 'customer_cancelation_date'


  def daterange(self,start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


  def load_data(self):
    c = self.db.cursor()
    X = []
    y = []
    c.execute("""SELECT DATE(MIN(time)),DATE(MAX(time)) from games""")
    days = c.fetchone()
    print days
    for aday in self.daterange(days[0],days[1]+timedelta(1)):
      c.execute("SELECT (today.pts+today.reb*1.2+today.ast*1.5+today.blk*2+today.stl*2-today.turnovers) fp, hist.avg_fgm,hist.avg_fga,hist.avg_tpm,hist.avg_tpa,hist.avg_ftm,hist.avg_fta,hist.avg_oreb,hist.avg_dreb,hist.avg_reb,hist.avg_ast,hist.avg_stl,hist.avg_blk,hist.avg_turnovers,hist.avg_pf,hist.avg_pts,(hist.avg_pts+hist.avg_reb*1.2+hist.avg_ast*1.5+hist.avg_blk*2+hist.avg_stl*2-hist.avg_turnovers) hist_fp FROM (select pid,avg(fgm) avg_fgm,avg(fga) avg_fga,avg(tpm) avg_tpm,avg(tpa) avg_tpa,avg(ftm) avg_ftm,avg(fta) avg_fta,avg(oreb) avg_oreb,avg(dreb) avg_dreb,avg(reb) avg_reb,avg(ast) avg_ast,avg(stl) avg_stl,avg(blk) avg_blk,avg(turnovers) avg_turnovers,avg(pf) avg_pf,avg(pts) avg_pts from playerstats,games WHERE games.gid=playerstats.gid AND time < %s group by pid having count(pid) > 5) AS hist, (SELECT pid,pts,reb,ast,blk,stl,turnovers FROM playerstats,games WHERE games.gid=playerstats.gid and date(time) = %s) AS today WHERE hist.pid = today.pid",
      (aday,aday))
      for d in c.fetchall():
        X.append(d[1:])
        y.append(d[0])
    return np.array(X,dtype=float),np.array(y,dtype=float)

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

  def pre_process(self,X,headers): # Pre-process categorical and custom variables
    self.feature_headers = []

    for feature in sorted(self.transformations):
      if self.transformations[feature]['type'] != None:

        D = X[:,headers[self.transformations[feature]['data']]]

        if self.transformations[feature]['type'] == 'categorical':
          lb = preprocessing.LabelBinarizer()
          lb.fit(D)
          self.pre_processors[feature] = lb
          for label in lb.classes_:
            self.feature_headers.append('_'.join([feature,label]))

        elif self.transformations[feature]['type'] == 'date_day':
          D = self.date_weekday(D)
          lb = preprocessing.LabelBinarizer()
          lb.fit(D)
          self.pre_processors[feature] = lb
          for label in lb.classes_:
            self.feature_headers.append('_'.join([feature,str(label)]))

        elif self.transformations[feature]['type'] == 'date_hour':
          D = self.date_hour(D)
          lb = preprocessing.LabelBinarizer()
          lb.fit(D)
          self.pre_processors[feature] = lb
          for label in lb.classes_:
            self.feature_headers.append('_'.join([feature,str(label)]))

        else:
          self.pre_processors[feature] = None
          self.feature_headers.append(feature)

    self.feature_headers = np.array(self.feature_headers)

    return self.transform(X,headers)


  def transform(self,X,headers):

    ## Tranform cancel dates to binary class
    if headers.has_key(self.yheader):
      D = X[:,headers[self.yheader]]
      Y = np.zeros(D.shape)
      for k in range(len(D)):
        if D[k] == 'NULL':
          Y[k] = 0
        else:
          Y[k] = 1
    else:
      Y = None

    ## Transform features
    X_transformed = []

    for feature in sorted(self.transformations):

      D = X[:,headers[self.transformations[feature]['data']]]

      if self.transformations[feature]['type'] != None:

        if self.transformations[feature]['type'] == 'numerical':
          x_row = np.array(D,dtype=float)
        elif self.transformations[feature]['type'] == 'categorical':
          x_row = self.pre_processors[feature].transform(D)
        elif self.transformations[feature]['type'] == 'date_day':
          x_row = self.pre_processors[feature].transform(self.date_weekday(D))
        elif self.transformations[feature]['type'] == 'date_hour':
          x_row = self.pre_processors[feature].transform(self.date_hour(D))
        elif self.transformations[feature]['type'] == 'booking_ratio':
          D = np.array(D,dtype=float)
          D[D == 0] = 1
          x_row = 1.0*np.array(X[:,headers['user_cancelled_bookings_count']],dtype=int)/D
        elif self.transformations[feature]['type'] == 'days_booked_ahead':
          x_row = self.daydiff(D,X[:,headers['date_added']])
        else:
          continue

        if len(x_row.shape) == 1:
          x_row = x_row.reshape(x_row.shape[0], 1)

        if len(X_transformed) == 0:
          X_transformed = x_row

        else:
          X_transformed = np.concatenate((X_transformed,x_row),axis=1)

    return X_transformed,Y

  def predict(self,y,threshold):
    return [0 if val < threshold else 1 for val in y]

  def train_predict(self,clf,X,y,cv):
    ## Train model clf, predict probabilities, and determine best threshold

    all_scores = []
    for train, test in cv:
        X_train, X_test, y_train, y_test = X[train,:], X[test,:], y[train], y[test]

        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        all_scores.append(mean_squared_error(y_test,y_pred))


    return np.mean(all_scores)

if __name__ == "__main__":

  ## Load features to use from file
  # features = json.load(open('../data/features.json','rb'))

  H = Handy()

  X,y = H.load_data()

  print 'Train data shape:',X.shape

  ## Random Forest Model
  # clf = RF(n_estimators=250, n_jobs=3,bootstrap=False,min_samples_leaf=1, min_samples_split=4, criterion='entropy', max_features=30, max_depth=None)
  clf = RF(n_estimators = 100, n_jobs = 3)
  cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=3,test_size=0.2,random_state=18)
  score = H.train_predict(clf,X,y,cv)
  print 'Accuracy score: %.2f\n'%(score)
  sys.exit()

  ## Fit training set and predict for test set

  D_test,headers = H.load_data('../data/handy_bookings_test.csv')
  X_test,y_test = H.transform(D_test,headers)
  clf.fit(X,y)

  ## Plot important features

  feaI = np.argsort(clf.feature_importances_)[::-1]
  num_to_show = 20
  feature_importances = clf.feature_importances_[feaI[:num_to_show]]
  feature_names = H.feature_headers[feaI[:num_to_show]]
  print '\n\n***********\n\n'.join(feature_names)

  fig = plt.figure(figsize=(12,8))
  plt.bar(range(num_to_show),feature_importances)
  plt.xticks(range(num_to_show),feature_names,rotation=70,ha='center')
  plt.subplots_adjust(bottom=.2)
  plt.title('Top feature importance')
  plt.show()


  ## Predict test data and write output file
  y_pred = H.predict(clf.predict_proba(X_test)[:,1],probability_threshold)

  row_id = D_test[:,headers['row_id']]
  fout = open('../data/cusomer_cancellation_predictions.csv','wb')
  fout.write("row_id,customer_will_cancel\n")
  for k in range(len(y_pred)):
    fout.write("%s,%i\n"%(row_id[k],y_pred[k]))
