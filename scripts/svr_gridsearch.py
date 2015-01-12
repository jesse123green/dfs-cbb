from pylab import plt
import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier as RF
from sklearn.feature_selection import SelectKBest, f_classif, chi2
from sklearn.metrics import mean_squared_error
from sklearn import cross_validation
from sklearn.linear_model import SGDRegressor
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


X = pickle.load(open('../data/dataX.p','rb'))
y = pickle.load(open('../data/datay.p','rb'))

print 'Train data shape:',X.shape

clf = Pipeline([
('scale', preprocessing.StandardScaler()),
('classification', SVR())
])

param_grid = [
  {'classification__C': [1, 10, 100, 1000], 'classification__kernel': ['linear']},
  # {'classification__C': [1, 10, 100, 1000], 'classification__gamma': [0.1, 0.01, .001, .0001], 'classification__kernel': ['rbf']},
 ]

start = time()

cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=5 ,test_size=0.2, random_state=12)
grid_search = GridSearchCV(clf, param_grid=param_grid,cv=cv,scoring='mean_squared_error')
grid_search.fit(X,y)

print("GridSearchCV took %.2f seconds for %d candidate parameter settings."
      % (time() - start, len(grid_search.grid_scores_)))
report(grid_search.grid_scores_)
