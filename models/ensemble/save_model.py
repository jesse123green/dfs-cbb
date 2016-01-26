from sklearn.utils import shuffle
from pylab import plt
import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error,mean_absolute_error
from sklearn import cross_validation
from sklearn.linear_model import SGDRegressor,ElasticNet,Ridge,Lasso,LassoLars,BayesianRidge
import numpy as np
from sklearn.grid_search import GridSearchCV
from time import time
from operator import itemgetter
from sklearn.kernel_ridge import KernelRidge
from sklearn.svm import LinearSVR
import gc
import multiprocessing as mp
from sklearn.ensemble import GradientBoostingRegressor as GBR
from sklearn.ensemble import RandomForestRegressor as RFR

class CBB():

  def __init__(self):
    self.pre_processors = {}
    self.feature_headers = []
    self.X = []
    self.y = []


def run_iter(clf,X,y,train,test):
  X_train, X_test, y_train, y_test = X[train,:], X[test,:], y[train], y[test]
  clf.fit(X_train, y_train)
  y_pred = clf.predict(X_test)
  return mean_absolute_error(y_test,y_pred)

def train_predict(clf,X,y,cv):
  ## Train model clf, predict probabilities, and determine best threshold
  all_scores = []
  k = 0
  for train, test in cv:
    # print X.shape,y.shape
    score = run_iter(clf,X,y,train,test)
    all_scores.append(score)
    print 'Iteration: %i, MSE: %.4f, Avg. MSE: %.6f'%(k,score,np.mean(all_scores))
    k += 1
    gc.collect()
  return np.mean(all_scores)

def train_predict_parallel(clf,X,y,cv):
  pool = mp.Pool(processes=2)
  results = [pool.apply_async(run_iter, args=(clf,X,y,train,test)) for train,test in cv]
  output = [p.get() for p in results]
  pool.close()
  pool.terminate()
  pool.join()
  return output



def modulate_features_subset(X,ind):
  num_fea = X.shape[1]

  mod = []
  k = 0
  for i in range(num_fea):
    if k in ind:
      mod.append(X[:,k])
    k += 1
  for i in range(num_fea):
    for j in range(i,num_fea):
      if k in ind:
        mod.append(X[:,i]*X[:,j])
      k += 1

  mod = np.array(mod,dtype=float)
  return mod.transpose()

def feature_is_selected(X,ind):
  num_fea = X.shape[1]

  k = 0
  for i in range(num_fea):
    if (k in ind) and (k in np.arange(190,211)):
      print k
    k += 1
  for i in range(num_fea):
    for j in range(i,num_fea):
      if ((k in ind) and (i in np.arange(190,211)) and (j not in np.arange(190,211))):
        print i,j
      k += 1

  return 

def trim_duplicates(X,ind):
  num_fea = X.shape[1]
  print num_fea
  for i in range(num_fea-1):
    for j in range(i+1,num_fea):
      if mean_squared_error(X[:,i],X[:,j]) == 0.:
        print ind[i],ind[j],'duplicate!'

# Utility function to report best scores
def report(grid_scores, n_top=3):
    top_scores = sorted(grid_scores, key=itemgetter(1), reverse=True)[:n_top]
    for i, score in enumerate(top_scores):
        print("Model with rank: {0}".format(i + 1))
        print("Mean validation score: {0:.3f} (std: {1:.3f})".format(
              score.mean_validation_score,
              np.std(score.cv_validation_scores)))
        print("Parameters: {0}".format(score.parameters))
        print("")


###########################################
############## FANDUEL ####################
###########################################


############ PLAYERS ############ MAE: 5.593 (420)
P = pickle.load(open('../../data/train/P_fd_000.p','rb'))
n_estimators = 420
params = {'n_estimators': n_estimators, 'max_depth': 4, 'min_samples_split': 5,'subsample':.5,
'learning_rate': 0.025, 'loss': 'lad', 'random_state':91}
#######################################


###########################################
############## DRAFT KINGS ################
###########################################

# n_sample = 30000

X = np.array(P.X)
start_size = X.shape[1]
y = np.array(P.y)

print 'Train data shape:',X.shape



start = time()
reg = GBR(**params)


# reg = Pipeline([
# ('scale', preprocessing.StandardScaler()),
# ('regression', RFR(max_depth=10,max_features=.2,n_estimators=500,min_samples_split=10,n_jobs=-1,random_state=2))
# ])

reg.fit(X, y)

## Define model
model = {}
model['reg'] = reg
reg.fit(X,y)

pickle.dump(model,open('../../data/models/model_fd_GBR_000.p','wb'))