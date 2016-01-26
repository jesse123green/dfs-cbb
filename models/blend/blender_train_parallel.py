from pylab import plt
import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error
from sklearn import cross_validation
from sklearn.linear_model import Ridge,Lasso,LinearRegression,SGDRegressor
import numpy as np
from time import time,sleep
from operator import itemgetter
from sklearn.svm import LinearSVR,SVR
import gc
from sklearn.ensemble import GradientBoostingRegressor as GBR
from sklearn.ensemble import RandomForestRegressor,ExtraTreesRegressor
import multiprocessing as mp
import pandas as pd
import itertools
from blend_models import load_blend_models

class CBB():
	def __init__(self):
		self.pre_processors = {}
		self.feature_headers = []
		self.X = []
		self.y = []

def train_fold(clf,X_train,y_train,train_1,test_1,i,logfit,X_test):
	print "Fold", i
	X_train_1 = X_train[train_1]
	y_train_1 = y_train[train_1]
	X_test_1 = X_train[test_1]
	y_test_1 = y_train[test_1]
	if logfit:
		y_min = np.min(y_train_1)
		y_log = np.log(y_train_1-y_min+1)
		clf.fit(X_train_1, y_log)
	else:
		clf.fit(X_train_1, y_train_1)
	
	if logfit:
		y_pred = np.exp(clf.predict(X_test_1))+y_min-1
		y_pred_test = np.exp(clf.predict(X_test))+y_min-1
	else:
		y_pred = clf.predict(X_test_1)
		y_pred_test = clf.predict(X_test)
	
	return tuple((test_1,y_pred,y_pred_test))

def train_predict(clf,X_train,y_train,logfit,skf,X_test):
	## Train model clf, predict probabilities, and determine best threshold
	all_scores = []
	k = 0
	for i, (train_1, test_1) in enumerate(skf):
		score = train_fold(clf,X_train,y_train,train_1,test_1,i,logfit,X_test)
		all_scores.append(score)
		# print 'Iteration: %i, MSE: %.4f, Avg. MSE: %.6f'%(k,score,np.mean(all_scores))
		k += 1
		gc.collect()
	return list(all_scores)


def train_predict_parallel(clf,X_train,y_train,logfit,skf,X_test):
	pool = mp.Pool(processes=8)
	results = [pool.apply_async(train_fold, args=(clf,X_train,y_train,train_1,test_1,i,logfit,X_test)) for i, (train_1, test_1) in enumerate(skf)]
	output = [p.get() for p in results]

	pool.close()
	pool.terminate()
	pool.join()

	return list(output)


if __name__ == '__main__':

	########### PLAYERS ############ 
	P = pickle.load(open('../../data/train/P_fd_001.p','rb'))
	clfs,logfits = load_blend_models()
	test_size = .15
	n_folds = 8
	n_iter = 10

	'''
	Best score: 5.557447
	Best model subset: (0, 1, 2, 3)
	Best model: reg_norm
	Best epsilon: 0.03
	Best C: 20
	'''	
	
	#######################################

	X = np.array(P.X)
	y = np.array(P.y)
	print X.shape
	print y.shape

	np.random.seed(123)

	N = len(clfs)
	b = []
	
	for k in range(2,N+1):
		for idx in list(itertools.combinations(range(N), k)):
			b.append(idx)

	# n_sample = 350
	# idx = np.random.permutation(y.size)
	# X = X[idx][:n_sample,:]
	# y = y[idx][:n_sample]

	# shuffle = True

	# if shuffle:
		# idx = np.random.permutation(y.size)
		# X = X[idx]
		# y = y[idx]
	

	reg_baseline = Pipeline([
	('regression', LinearSVR(epsilon=0))
	])

	reg_norm = Pipeline([
	('scale', preprocessing.StandardScaler()),
	('regression', LinearSVR(epsilon=0))
	])

	n_clfs = len(clfs)


	final_errors = np.zeros((n_iter,n_clfs))
	cv = cross_validation.ShuffleSplit(X.shape[0], n_iter=n_iter,test_size=test_size, random_state=524)

	models = [reg_baseline,reg_norm]
	model_names = ['reg','reg_norm']
	C_values = [.0001,.0003,.001,.003,.01,.03,.1,.3,1,3,10,20,30,50,100]
	epsilon_values = [0,.00001,.00003,.0001,.0003,.001,.003,.01,.03,.1,.3,1,2,3]

	hp_values = []

	for _indx in b:
		for model_name in model_names:
			for epsilon in epsilon_values:
				for C in C_values:
					hp_values.append(tuple((_indx,model_name,epsilon,C)))
	test_errors = np.zeros((n_iter,len(C_values)*len(epsilon_values)*len(models)*len(b)))

	for k, (train,test) in enumerate(cv):

		X_train, X_test, y_train, y_test = X[train,:], X[test,:], y[train], y[test]

		print "Creating train and test sets for blending."

		dataset_blend_train = np.zeros((X_train.shape[0], n_clfs))
		dataset_blend_test = np.zeros((X_test.shape[0], n_clfs))

		skf = list(cross_validation.KFold(len(y_train), n_folds, random_state=4002))

		for j, (clf,logfit) in enumerate(zip(clfs,logfits)):
			print j, logfit
			if j == 0:
				output = train_predict(clf,X_train,y_train,logfit,skf,X_test)
			else:
				output = train_predict_parallel(clf,X_train,y_train,logfit,skf,X_test)
			
			dataset_blend_test_k = np.zeros((X_test.shape[0], len(skf)))

			for _k, (test_1,y_pred,y_pred_test) in enumerate(output):
				dataset_blend_train[test_1, j] = np.array(y_pred)
				dataset_blend_test_k[:,_k] = y_pred_test
			dataset_blend_test[:, j] = np.mean(dataset_blend_test_k,axis=1)

			e = mean_absolute_error(dataset_blend_test[:, j],y_test)
			final_errors[k,j] = e
			
			print 'Error for model %i: %.6f'%(j,e)
			print 'Mean for model %i: %.6f'%(j,np.mean(final_errors[:k+1,j]))

		print
		print "Blending."
		hp_i = 0
		for idx in b:
			for model in models:
				for epsilon in epsilon_values:
					for C in C_values:
						model.named_steps['regression'].C = C
						model.named_steps['regression'].epsilon = epsilon
						model.fit(dataset_blend_train[:,idx],y_train)
						# print reg.named_steps['regression'].coef_,reg.named_steps['regression'].intercept_
						y_predictions = model.predict(dataset_blend_test[:,idx])
						e = mean_absolute_error(y_predictions,y_test)
						test_errors[k,hp_i] = e
						hp_i += 1

		print 'Mean errors for blend on iteration %i:'%(k)
		print 'Best score: %.6f'%np.min(np.mean(test_errors[:k+1,:],axis=0))
		best_idx,best_model,best_epsilon,best_C = hp_values[np.argmin(np.mean(test_errors[:k+1,:],axis=0))]

		# model.named_steps['regression'].C = best_C
		# model.named_steps['regression'].epsilon = best_epsilon
		# model.fit(dataset_blend_train,y_train)
		# print model.named_steps['regression'].coef_,model.named_steps['regression'].intercept_
		print 'Best model subset:',best_idx
		print 'Best model:',best_model
		print 'Best epsilon:',best_epsilon
		print 'Best C:',best_C

	print 'Best Single Model Errors:',np.min(np.mean(final_errors,axis=0))
	print 'Single Model Errors:',np.mean(final_errors,axis=0)
	# print 'Stacking Errors:',np.mean(test_errors,axis=0)
