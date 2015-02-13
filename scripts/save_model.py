from pylab import plt
import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier as RF
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
from sklearn.neural_network.multilayer_perceptron import MultilayerPerceptronRegressor as MPR

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


X = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/dataX_5minavg_Feb12.p','rb'))
y = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/datay_5minavg_Feb12.p','rb'))

# i1  = (X[:,0]>8)

# y = y[i1]
# X = X[i1,:]


'''
## l1 loss
>8: l1_ratio = .1, alpha = .05
>0: l1_ratio = .1, alpha = .05
## l2 loss
>8: l1_ratio = .05, alpha = .05
>0: l1_ratio = .1, alpha = .05
'''

print 'Train data shape:',X.shape

clf = Pipeline([
('scale', preprocessing.StandardScaler()),
('classification', SVR(kernel='rbf',C=3,gamma=.001)),
# ('classification', MPR(algorithm='sgd',eta0=.0001,n_hidden=2500,max_iter=200,shuffle=True,random_state=15,activation="tanh",verbose=True))
# ('classification', ElasticNet(alpha=.05,l1_ratio=.1,max_iter=100000))
])

start = time()

clf.fit(X,y)
pickle.dump(clf,open('/Users/jesseg/Documents/fantasy/cbb/data/models/model_5all_8_l1_svr.p','wb'))
