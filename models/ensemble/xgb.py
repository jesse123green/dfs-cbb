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
from time import time,sleep
from operator import itemgetter
from sklearn.kernel_ridge import KernelRidge
from sklearn.svm import LinearSVR
import gc
import multiprocessing as mp
from sklearn.ensemble import GradientBoostingRegressor as GBR
from sklearn.ensemble import RandomForestRegressor as RFR
from sklearn.decomposition import PCA
import xgboost as xgb
from scipy.stats import boxcox
from scipy.special import inv_boxcox
from sklearn.feature_selection import SelectFromModel

class CBB():

  def __init__(self):
    self.pre_processors = {}
    self.feature_headers = []
    self.X = []
    self.y = []

def run_iter(reg,X,y,train,test):
  X_train, X_test, y_train, y_test = X[train,:], X[test,:], y[train], y[test]
  reg.fit(X_train, y_train)
  y_pred = reg.predict(X_test)
  return mean_absolute_error(y_test,y_pred)

def train_predict(reg,X,y,cv):
  ## Train model reg, predict probabilities, and determine best threshold
  all_scores = []
  k = 0
  for train, test in cv:
    # print X.shape,y.shape
    score = run_iter(reg,X,y,train,test)
    all_scores.append(score)
    print 'Iteration: %i, MSE: %.4f, Avg. MSE: %.6f'%(k,score,np.mean(all_scores))
    k += 1
    gc.collect()
  return np.mean(all_scores)

def train_predict_parallel(reg,X,y,cv):
  pool = mp.Pool(processes=2)
  results = [pool.apply_async(run_iter, args=(reg,X,y,train,test)) for train,test in cv]
  output = [p.get() for p in results]
  pool.close()
  pool.terminate()
  pool.join()
  return output


def root_scale_down(X,_lambda):
  for k in range(len(X)):
    if X[k] > 0:
      X[k] = np.power(X[k],_lambda)
    elif X[k] < 0:
      X[k] = -1*np.power(np.abs(X[k]),_lambda)
  return X

def root_scale_up(X):
  for k in range(len(X)):
    if X[k] > 0:
      X[k] = np.power(X[k],1./_lambda)
    elif X[k] < 0:
      X[k] = -1*np.power(np.abs(X[k]),1./_lambda)
  return X

def boxcox_fit(y_train):
  y_min = np.min(y_train)-1
  y_train_boxcox,_lambda = boxcox(y_train-y_min)
  return y_train_boxcox,_lambda,y_min

def boxcox_transform(y_test,_lambda,y_min):
  y_test_boxcox = boxcox(y_test-y_min,_lambda)
  return y_test_boxcox

def boxcox_inverse(y_box,_lambda,y_min):
  return inv_boxcox(y_box,_lambda)+y_min

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


############ Players ############ MAE:
fname = '../../data/train/P_fd_117a.p'

P = pickle.load(open(fname,'rb'))
n_estimators = 1400
subsample = .45
params = {'n_estimators': n_estimators, 'max_depth': 4, 'subsample':subsample,'learning_rate': 0.01,'seed':88}
print fname
print params
#######################################


###########################################
############## DRAFT KINGS ################
###########################################

############ Players ############ MAE:  / 
# P = pickle.load(open('../../data/train/P_dk_001.p','rb'))
# n_estimators = 3000
# params = {'n_estimators': n_estimators, 'max_depth': 5, 'min_samples_split': 5,'subsample':.5,
# 'learning_rate': 0.01, 'loss': 'lad', 'random_state':91}
#######################################


X = np.array(P.X)
y = np.array(P.y)


# n_sample = 300
# idx = np.random.permutation(y.size)
# X = X[idx][:n_sample,:]
# y = y[idx][:n_sample]

X_fp = X[:,0]

gc.collect()
# eval_metric="mae",subsample=.5,n_estimators=100
print 'Train data shape:',X.shape

# fr = SGDRegressor(n_iter=50,random_state=14,epsilon=2,alpha=.003,eta0=.003,loss='epsilon_insensitive',penalty='l2')

# sfm = Pipeline([
# ('scale', preprocessing.StandardScaler()),
# ('sfm', SelectFromModel(fr, threshold=0.002))
# ])

reg_xgb = xgb.XGBRegressor(**params)

# sfm = SelectFromModel(fr, threshold=0.002)
# sfm.fit(X, y)
# print sfm.transform(X).shape[1]
# print reg.fit_transform(X,y)
# sys.exit()
_lambda = .4
print 'Lambda:',_lambda
print 'susample:',subsample
start = time()
all_scores = []
cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=20,test_size=0.2, random_state=12)
for train,test in cv:

  ###############################################################################
  # Load data
  X_train, X_test, y_train, y_test = X[train,:], X[test,:], y[train], y[test]

  ###############################################################################
  # Fit regression model
  __,_,y_min = boxcox_fit(y_train)
  y_train_boxcox = boxcox_transform(y_train,_lambda,y_min)
  # print 'Boxcox params:',_lambda,y_min
  # X_train_sfm = sfm.fit_transform(X_train,y_train)
  # print 'Reduced to %i features.'%X_train_sfm.shape[1]
  reg_xgb.fit(X_train, y_train_boxcox)
  mae = mean_absolute_error(y_test, boxcox_inverse(reg_xgb.predict(X_test),_lambda,y_min))
  # mae = mean_absolute_error(y_test, root_scale_up(reg.predict(X_test),_lambda))
  print("MAE: %.4f" % mae)

  ###############################################################################
  # Plot training deviance

  # compute test set deviance
  step_size = 20
  n_tree_values = np.arange(400,n_estimators+step_size,step_size)
  # print n_tree_values
  n_tree_length = len(n_tree_values)
  test_score = np.zeros((n_tree_length,), dtype=np.float64)

  for i in range(n_tree_length):
      y_transform = boxcox_inverse(reg_xgb.predict(X_test,ntree_limit = n_tree_values[i]),_lambda,y_min)
      # y_transform = root_scale_up(reg.predict(X_test,ntree_limit=n_tree_values[i]),_lambda)
      test_score[i] = mean_absolute_error(y_transform,y_test)
  all_scores.append(test_score)
  
  print "Minimum average MAE: %.5f"%np.min(np.mean(all_scores,axis=0))
  print "At feature: %i"%n_tree_values[np.argmin(np.mean(all_scores,axis=0))]


plt.figure(figsize=(12, 6))
# plt.subplot(1, 2, 1)
plt.title('Deviance')
# plt.plot(np.arange(params['n_estimators']) + 1, reg.train_score_, 'b-',
#          label='Training Set Deviance')
for k in range(len(all_scores)):
  plt.plot(n_tree_values, all_scores[k], 'r-')

plt.plot(n_tree_values, np.mean(all_scores,axis=0), 'b-', linewidth=4) 
# plt.legend(loc='upper right')
plt.xlabel('Boosting Iterations')
plt.ylabel('Deviance')

###############################################################################
# Plot feature importance
# feature_importance = reg.feature_importances_
# # make importances relative to max importance
# feature_importance = 100.0 * (feature_importance / feature_importance.max())
# sorted_idx = np.argsort(feature_importance)[-20:]
# pos = np.arange(sorted_idx.shape[0]) + .5
# plt.subplot(1, 2, 2)
# plt.barh(pos, feature_importance[sorted_idx], align='center')
# plt.yticks(pos, sorted_idx)
# plt.xlabel('Relative Importance')
# plt.title('Variable Importance')
# plt.show()

print "Accuracy using unweighted fp mean: %.3f"%mean_absolute_error(X_fp,y)