from pylab import plt
import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor as RF
from sklearn.feature_selection import SelectKBest, f_classif, chi2
from sklearn.metrics import mean_squared_error
from sklearn import cross_validation
from sklearn.linear_model import SGDRegressor,Lasso,ElasticNet
import numpy as np
from sklearn.svm import SVC,SVR
from sklearn.grid_search import GridSearchCV
from time import time
from operator import itemgetter
from cbb import CBB

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


X = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data/dataX.p','rb'))
y = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data/datay.p','rb'))




clf = Pipeline([
('scale', preprocessing.StandardScaler()),
# ('classification', SVR(kernel='linear'))
# ('classification', RF(n_estimators=250,n_jobs=2))
('selection',SelectKBest(k=1000)),
# ('selection',PCA(n_components=1000)),
('classification', ElasticNet(alpha=.02,l1_ratio=.1))
# ('classification', Lasso())
])

start = time()

C = CBB()

cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=5,test_size=0.2, random_state=12)

Xnew = np.zeros((X.shape[0],1275))

Xnew[:,:50] = X

i = 50
for k in range(49):
  for j in range(k+1,50):
    Xnew[:,i] = X[:,k]*X[:,j]
    i += 1

print 'Train data shape:',Xnew.shape
all_scores = []

for k in np.arange(10,1000,20):
  clf.set_params(selection__k=k)
  score = C.train_predict(clf,Xnew,y,cv)
  all_scores.append(score)
  print 'Accuracy score for %i features: %.2f\n'%(k,score)

plt.plot(all_scores)
plt.show()
