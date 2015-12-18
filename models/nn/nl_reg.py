import numpy as np
import cPickle as pickle
import sys
import pylab as pl
from math import sqrt
from sklearn import preprocessing
from sklearn.cross_validation import train_test_split
from sklearn.metrics import mean_squared_error as MSE
import neurolab as nl

X = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/dataX_5all.p','rb'))
y = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/datay_5all.p','rb'))

i1  = (X[:,0]>8)

y = y[i1][-2000:]
X = X[i1,:][-2000:]
X = X[:,:1]

X_train, X_valid_train, y_train, y_valid_train = train_test_split(X, y, test_size=0.3, random_state=4)
X_test, X_valid, y_test, y_valid = train_test_split(X_valid_train, y_valid_train, test_size=0.5, random_state=9)

### SCALE
scaler = preprocessing.StandardScaler()
scaler.fit(X_train)
X_train = scaler.transform(X_train)
X_valid = scaler.transform(X_valid)
X_avg = X_test[:,0]
# X_test = scaler.transform(X_test)


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

learningrate = .0001
momentum = 0.

print 'Learning rate:',learningrate
print 'Momentum:',momentum


input_min_max = []
for k in range(X_train.shape[1]):
  input_min_max.append([np.min(X_train[:,k]),np.max(X_train[:,k])])

print input_min_max

net = nl.net.newff(input_min_max,[5, 1],transf=[nl.trans.LogSig()]*2)

# Train network
error = net.train(X_train, y_train, epochs=500, show=10, goal=0.65)
print error
# Plot results

pl.plot(error)
pl.xlabel('Epoch number')
pl.ylabel('Train error')
pl.grid()
pl.show()

# print "Accuracy using unweighted fp mean: %.2f"%MSE(X_avg,y_test)
# print 'Accuracy score: %.2f\n'%(MSE( y_test, p ))
#
# sys.exit()
#
# pickle.dump( net, open( '/Users/jesseg/Documents/fantasy/cbb/data_time_series/nn.p', 'wb' ))
