from pylab import plt
import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor as RF
from sklearn.feature_selection import SelectKBest, f_classif, chi2, f_regression
from sklearn.metrics import mean_squared_error
from sklearn import cross_validation
from sklearn.linear_model import SGDRegressor,Lasso,ElasticNet, LinearRegression
import numpy as np
from sklearn.svm import SVC,SVR
from sklearn.grid_search import GridSearchCV
from time import time
from operator import itemgetter
from cbb import CBB
from scipy.misc import comb

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


X = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/dataX_5all_2.p','rb'))
y = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/datay_5all_2.p','rb'))


i1  = (X[:,0]>8)

y = y[i1]
X = X[i1,:]

clf = Pipeline([
('scale', preprocessing.StandardScaler()),
# ('classification', SVR(kernel='linear'))
# ('classification', RF(n_estimators=250,n_jobs=2))
('selection',SelectKBest(score_func=f_regression,k=10)),
# ('selection',PCA(n_components=1000)),
('classification', ElasticNet(alpha=.05,l1_ratio=.05))
# ('classification', Lasso())
])

start = time()

C = CBB()

cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=30,test_size=0.2, random_state=12)

# features_start = X.shape[1]
# new_fea_num = int(comb(features_start,2)) + features_start
# Xnew = np.zeros((X.shape[0],new_fea_num))
#
# Xnew[:,:features_start] = X
#
# i = features_start
# for k in range(features_start-1):
#   for j in range(k+1,features_start):
#     Xnew[:,i] = X[:,k]*X[:,j]
#     i += 1

print 'Train data shape:',X.shape


all_scores = []

for k in np.arange(1,136,5):
  clf.set_params(selection__k=k)
  score = C.train_predict(clf,X,y,cv)
  all_scores.append(score)
  print 'Accuracy score for %i features: %.2f\n'%(k,score)

plt.plot(all_scores)
plt.show()
