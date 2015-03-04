from pylab import plt
import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor as RF
from sklearn.feature_selection import SelectKBest, f_classif, chi2
from sklearn.metrics import mean_squared_error,mean_absolute_error
from sklearn import cross_validation
from sklearn.linear_model import SGDRegressor,Lasso,ElasticNet,LinearRegression
import numpy as np
from sklearn.svm import SVC,SVR
from sklearn.grid_search import GridSearchCV
from time import time
from operator import itemgetter
from sklearn.neural_network.multilayer_perceptron import MultilayerPerceptronRegressor as MPR
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


X = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/dataX_5posopp_Mar1.p','rb'))
y = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/datay_5posopp_Mar1.p','rb'))

i1  = (X[:,0]>8)

y = y[i1]
X = X[i1,:]

X_avg = X[:,0]

# X = X[:,0:20]

# y = y[-10000:]
# X = X[-10000:,:]

# plt.hist(y,bins=50)
# plt.show()

print 'Train data shape:',X.shape

max_iter = 200
eta0 = .0001

clf = Pipeline([
('scale', preprocessing.StandardScaler()),
# ('classification', SVR(kernel='linear',C=.003)),
# ('classification', SVR(kernel='rbf',C=3,gamma=.001)),
# ('classification', RF(n_estimators=250,n_jobs=3))
('classification', ElasticNet(alpha=.05,l1_ratio=.1,max_iter=5000))
# ('classification', MPR(algorithm='sgd',eta0=eta0,n_hidden=2500,max_iter=max_iter,shuffle=True,random_state=11,activation="tanh",verbose=True))
])

print 'max_iter:',max_iter
print 'eta0:',eta0

start = time()

C = CBB()

cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=50,test_size=0.2, random_state=12)


score = C.train_predict(clf,X,y,cv)


print 'Accuracy score: %.2f\n'%(score)
print "Accuracy using unweighted fp mean: %.2f"%mean_squared_error(X_avg,y)
