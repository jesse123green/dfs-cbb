from pylab import plt
import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier as RF
from sklearn.feature_selection import SelectKBest, f_classif, chi2
from sklearn.metrics import mean_squared_error,mean_absolute_error
from sklearn import cross_validation
from sklearn.linear_model import SGDRegressor
import numpy as np
from sklearn.svm import SVC
from sklearn.grid_search import GridSearchCV
from time import time
from operator import itemgetter
from sklearn.decomposition import PCA

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


P = pickle.load(open('../../data/train/P_fd_118a.p','rb'))

# X = np.hstack((np.array(P.X)[:,:-45],np.array(P.X)[:,-15:]))
X = np.array(P.X)
y = np.array(P.y)
start_size = X.shape[1]

X_fp = X[:,0]
print "Accuracy using unweighted fp mean: %.3f"%mean_absolute_error(X_fp,y)
print 'Train data shape:',X.shape
sys.exit()
clf = Pipeline([
('pca',PCA(n_components = X.shape[1])),
('scale', preprocessing.StandardScaler()),
('regression', SGDRegressor(n_iter=50,random_state=14))
])
# Parameters: {'regression__epsilon': 1.5, 'regression__alpha': 0.002, 'regression__eta0': 0.005, 'regression__loss': 'epsilon_insensitive', 'regression__l1_ratio': 0.85, 'regression__penalty': 'elasticnet'}


param_grid = [
  {'regression__penalty': ['l1'],'regression__l1_ratio':[.85],'regression__epsilon':[1.5],\
   'regression__loss': ['epsilon_insensitive'],'regression__alpha':[.003],\
   'regression__eta0':[.003],'pca__n_components':[47,46,45,44,43,42]}
 ]

start = time()

cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=45,test_size=0.2, random_state=524)
grid_search = GridSearchCV(clf, param_grid=param_grid,cv=cv,scoring='mean_absolute_error',n_jobs=8,verbose=1)
grid_search.fit(X,y)

print("GridSearchCV took %.2f seconds for %d candidate parameter settings."
      % (time() - start, len(grid_search.grid_scores_)))
report(grid_search.grid_scores_)
