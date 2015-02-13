import numpy as np
import cPickle as pickle
import sys
import pylab as pl
from math import sqrt
from sklearn import preprocessing
from sklearn.cross_validation import train_test_split
from sklearn.metrics import mean_squared_error as MSE
from sklearn.neural_network.multilayer_perceptron import MultilayerPerceptronRegressor
from sklearn.utils.testing import assert_raises, assert_greater, assert_equal

X = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/dataX_5all.p','rb'))
y = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/datay_5all.p','rb'))

i1  = (X[:,0]>8)

y = y[i1]
X = X[i1,:]

X_train, X_valid_train, y_train, y_valid_train = train_test_split(X, y, test_size=0.25, random_state=5)
X_test, X_valid, y_test, y_valid = train_test_split(X_valid_train, y_valid_train, test_size=0.5, random_state=91)

### SCALE
scaler = preprocessing.StandardScaler()
scaler.fit(X_train)
X_train = scaler.transform(X_train)
X_valid = scaler.transform(X_valid)

X_avg = X_test[:,0]
X_test = scaler.transform(X_test)


### TRAIN DATA
y_train = y_train.reshape( -1, 1 )

print X_train.shape
print y_train.shape

input_size = X_train.shape[1]
target_size = y_train.shape[1]


####### VALID DATA

y_valid = y_valid.reshape( -1, 1 )


####### TEST DATA

y_test = y_test.reshape( -1, 1 )
y_test_dummy = np.zeros( y_test.shape )


#### PARAMETERS


hidden_size = 250
epochs = 1000
continue_epochs = 3
validation_proportion = 0.25

learningrate = .00001
momentum = 0.

print 'Learning rate:',learningrate
print 'Momentum:',momentum

ACTIVATION_TYPES = ["logistic", "tanh"]

mlp = MultilayerPerceptronRegressor(
    algorithm='sgd',
    eta0=.00005,
    n_hidden=1200,
    max_iter=400,
    alpha=0.1,
    shuffle=True,
    random_state=11,
    activation="tanh",
    verbose=True)

mlp.fit(X_train, y_train, X_valid,y_valid)

# for k in range(1,150):
#   mlp.max_iter = k
#   p = mlp.predict(X_test)
#   print 'Accuracy score for iter %i: %.2f\n'%(k,MSE( y_test, p ))

print 'Accuracy score for test set: %.2f'%(MSE( y_test, mlp.predict(X_test )))
print "Accuracy using unweighted fp mean: %.2f"%MSE(X_avg,y_test)


# Plot results

# pl.plot(error)
# pl.xlabel('Epoch number')
# pl.ylabel('Train error')
# pl.grid()
# pl.show()


#
# sys.exit()
#
# pickle.dump( net, open( '/Users/jesseg/Documents/fantasy/cbb/data_time_series/nn.p', 'wb' ))
