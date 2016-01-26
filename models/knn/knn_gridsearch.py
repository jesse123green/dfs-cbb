from pylab import plt
import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier as RF
from sklearn.feature_selection import SelectKBest, f_classif, chi2
from sklearn.metrics import mean_squared_error,mean_absolute_error
from sklearn import cross_validation
from sklearn.linear_model import SGDRegressor,ElasticNet
import numpy as np
from sklearn.svm import SVC,SVR
from sklearn.grid_search import GridSearchCV
from time import time
from operator import itemgetter
from sklearn import neighbors

class CBB():

  def __init__(self):
    self.pre_processors = {}
    self.feature_headers = []
    self.X = []
    self.y = []

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


P = pickle.load(open('../../data/train/P_fd_001.p','rb'))

X = np.array(P.X)
y = np.array(P.y)
start_size = X.shape[1]

X_fp = X[:,0]
print "Accuracy using unweighted fp mean: %.3f"%mean_absolute_error(X_fp,y)
print 'Train data shape:',X.shape

m = Pipeline([
('scale', preprocessing.StandardScaler()),
('regression', neighbors.KNeighborsRegressor(weights='uniform',n_neighbors=80))
])



param_grid = [
{'regression__n_neighbors':[10],'regression__weights':['uniform','distance']}
]


start = time()

cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=10,test_size=0.2, random_state=12)
grid_search = GridSearchCV(m, param_grid=param_grid,cv=cv,scoring='mean_absolute_error',verbose=1,n_jobs=-1)
grid_search.fit(X,y)

print("GridSearchCV took %.2f seconds for %d candidate parameter settings."
      % (time() - start, len(grid_search.grid_scores_)))
report(grid_search.grid_scores_)
