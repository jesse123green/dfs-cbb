import numpy as np
import cPickle as pickle
import sys
import pylab as plt
from math import sqrt
from pybrain.datasets.supervised import SupervisedDataSet as SDS
from pybrain.tools.shortcuts import buildNetwork
from pybrain.supervised.trainers import BackpropTrainer
from sklearn import preprocessing
from sklearn.cross_validation import train_test_split
from sklearn.metrics import mean_squared_error as MSE
from pybrain.tools.neuralnets import NNregression

X = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/dataX_5all.p','rb'))
y = pickle.load(open('/Users/jesseg/Documents/fantasy/cbb/data_time_series/datay_5all.p','rb'))

i1  = (X[:,0]>8)

y = y[i1]
X = X[i1,:]

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

ds = SDS( input_size, target_size )
ds.setField( 'input', X_train )
ds.setField( 'target', y_train )

####### VALID DATA

y_valid = y_valid.reshape( -1, 1 )

ds_valid = SDS( input_size, target_size )
ds_valid.setField( 'input', X_valid )
ds_valid.setField( 'target', y_valid )

####### TEST DATA

y_test = y_test.reshape( -1, 1 )
y_test_dummy = np.zeros( y_test.shape )

ds_test = SDS( input_size, target_size )
ds_test.setField( 'input', X_test )
ds_test.setField( 'target', y_test )

#### PARAMETERS


hidden_size = 250
epochs = 1000
continue_epochs = 3
validation_proportion = 0.25

learningrate = .0001
momentum = 0.

print 'Learning rate:',learningrate
print 'Momentum:',momentum
# init and train

net = NNregression( ds, hidden=hidden_size, TDS= ds_test, VDS = ds_valid )

# trainer = BackpropTrainer( net, ds, learningrate=learningrate, momentum=momentum)
# trainer = BackpropTrainer( net, ds )
net.initGraphics()
net.setupNN()
net.runTraining(convergence=1000)
# train_mse, validation_mse = trainer.trainUntilConvergence( verbose = True, validationProportion = validation_proportion,
# 	maxEpochs = epochs, continueEpochs = continue_epochs )

# for i in range( epochs ):
#   mse = trainer.train()
#   rmse = sqrt( mse )
#   p = net.activateOnDataset( ds_test )
#   print p.shape
#   print p[:5],y_test[:5]
#   print "training MSE, epoch %i: %.2f"%( i + 1, mse )
#   print "test MSE:",(MSE( y_test, p ))




# print "Accuracy using unweighted fp mean: %.2f"%MSE(X_avg,y_test)
# print 'Accuracy score: %.2f\n'%(MSE( y_test, p ))
#
# sys.exit()
#
# pickle.dump( net, open( '/Users/jesseg/Documents/fantasy/cbb/data_time_series/nn.p', 'wb' ))
