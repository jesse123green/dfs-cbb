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
from sklearn.decomposition import PCA


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


############ PLAYERS ############ 
fname = '../../data/train/P_fd_004_6.p'
P = pickle.load(open(fname,'rb'))
n_estimators = 2000
params = {'n_estimators': n_estimators, 'max_depth': 4, 'min_samples_leaf': 20,'subsample':.3,
'learning_rate': 0.01, 'loss': 'lad', 'random_state':91}

print fname
print params
#######################################


###########################################
############## DRAFT KINGS ################
###########################################

# n_sample = 30000

X = np.array(P.X)
start_size = X.shape[1]
y = np.array(P.y)

# idx = np.random.permutation(y.size)
# X = X[idx][:n_sample,:]
# y = y[idx][:n_sample]

X_fp = X[:,0]
gc.collect()

print 'Train data shape:',X.shape


start = time()
all_scores = []
cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=15,test_size=0.2, random_state=524)
for train,test in cv:

  ###############################################################################
  # Load data
  X_train, X_test, y_train, y_test = X[train,:], X[test,:], y[train], y[test]
  # X_train = scaler.fit_transform(X_train)
  # X_test = scaler.transform(X_test)
  ###############################################################################
  # Fit regression model


  clf = GBR(**params)

  clf.fit(X_train, y_train)
  mae = mean_absolute_error(y_test, clf.predict(X_test))
  print("MAE: %.4f" % mae)

  ###############################################################################
  # Plot training deviance

  # compute test set deviance
  test_score = np.zeros((params['n_estimators'],), dtype=np.float64)

  for i, y_pred in enumerate(clf.staged_decision_function(X_test)):
      test_score[i] = clf.loss_(y_test, y_pred)
  all_scores.append(test_score)
  print "Minimum average MAE: %.5f"%np.min(np.mean(all_scores,axis=0))
  print "At feature: %i"%np.argmin(np.mean(all_scores,axis=0))


plt.figure(figsize=(12, 6))
# plt.subplot(1, 2, 1)
plt.title('Deviance')
# plt.plot(np.arange(params['n_estimators']) + 1, clf.train_score_, 'b-',
#          label='Training Set Deviance')
for k in range(len(all_scores)):
  plt.plot(np.arange(n_estimators) + 1, all_scores[k], 'r-')

plt.plot(np.arange(n_estimators) + 1, np.mean(all_scores,axis=0), 'b-', linewidth=4) 
# plt.legend(loc='upper right')
plt.xlabel('Boosting Iterations')
plt.ylabel('Deviance')

###############################################################################
# Plot feature importance
# feature_importance = clf.feature_importances_
# # make importances relative to max importance
# feature_importance = 100.0 * (feature_importance / feature_importance.max())
# sorted_idx = np.argsort(feature_importance)[-20:]
# pos = np.arange(sorted_idx.shape[0]) + .5
# plt.subplot(1, 2, 2)
# plt.barh(pos, feature_importance[sorted_idx], align='center')
# plt.yticks(pos, sorted_idx)
# plt.xlabel('Relative Importance')
# plt.title('Variable Importance')
plt.show()

print "Accuracy using unweighted fp mean: %.3f"%mean_absolute_error(X_fp,y)