from pylab import plt
import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier as RF
from sklearn.feature_selection import SelectKBest, f_classif, chi2
from sklearn.metrics import mean_squared_error
from sklearn import cross_validation
from sklearn.linear_model import SGDRegressor,ElasticNet
import numpy as np
from sklearn.svm import SVC,SVR
from sklearn.grid_search import GridSearchCV
from time import time
from operator import itemgetter

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


X = pickle.load(open('../data_time_series/dataX_5all.p','rb'))
y = pickle.load(open('../data_time_series/datay_5all.p','rb'))


# i1  = (X[:,0]>8)
# i2 = (y >= 1)
#
# y = y[i1]
# X = X[i1,:]

print 'Train data shape:',X.shape

clf = Pipeline([
('scale', preprocessing.StandardScaler()),
('classification', ElasticNet(max_iter=2000))
])

param_grid = [
  {'classification__alpha': np.arange(.05,1,.05), 'classification__l1_ratio': np.arange(.05,1,.05)}
 ]

start = time()

cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=10,test_size=0.2, random_state=12)
# grid_search = GridSearchCV(clf, param_grid=param_grid,cv=cv,scoring='mean_squared_error')
grid_search = GridSearchCV(clf, param_grid=param_grid,cv=cv,scoring='mean_absolute_error')
grid_search.fit(X,y)

print("GridSearchCV took %.2f seconds for %d candidate parameter settings."
      % (time() - start, len(grid_search.grid_scores_)))
report(grid_search.grid_scores_)
