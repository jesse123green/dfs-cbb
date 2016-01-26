from pylab import plt
import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error
from sklearn import cross_validation
from sklearn.linear_model import Ridge,Lasso,LinearRegression,SGDRegressor
import numpy as np
from time import time
from operator import itemgetter
from sklearn.svm import LinearSVR,SVR
import gc
from sklearn.ensemble import GradientBoostingRegressor as GBR
from sklearn.ensemble import RandomForestRegressor,ExtraTreesRegressor
import multiprocessing as mp
from blend_models import load_blend_models

def train_fold(clf,X_train,y_train,train_1,test_1,i,logfit):
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
	else:
		y_pred = clf.predict(X_test_1)
	
	return tuple((test_1,y_pred))

def train_predict(clf,X_train,y_train,logfit,skf):
	## Train model clf, predict probabilities, and determine best threshold
	all_scores = []
	k = 0
	for i, (train_1, test_1) in enumerate(skf):
		score = train_fold(clf,X_train,y_train,train_1,test_1,i,logfit)
		all_scores.append(score)
		# print 'Iteration: %i, MSE: %.4f, Avg. MSE: %.6f'%(k,score,np.mean(all_scores))
		k += 1
		gc.collect()
	return list(all_scores)

def train_predict_parallel(clf,X_train,y_train,logfit,skf):
	pool = mp.Pool(processes=8)
	results = [pool.apply_async(train_fold, args=(clf,X_train,y_train,train_1,test_1,i,logfit)) for i, (train_1, test_1) in enumerate(skf)]
	output = [p.get() for p in results]

	pool.close()
	pool.terminate()
	pool.join()

	return list(output)

class CBB():

	def __init__(self):
		self.pre_processors = {}
		self.feature_headers = []
		self.X = []
		self.y = []

if __name__ == '__main__':

	###########################################
	############## FANDUEL ####################
	###########################################

	########### PLAYERS ############ 
	P = pickle.load(open('../../data/train/P_fd_001.p','rb'))
	clfs,logfits = load_blend_models()
	n_folds = 8
	epsilon_final = 0.03
	C_final = 20
	reg = Pipeline([
	('scale', preprocessing.StandardScaler()),
	('regression', LinearSVR(epsilon=epsilon_final,C=C_final))
	])	
	
	#######################################

	X = np.array(P.X)
	y = np.array(P.y)
	
	X_fp = P.X
	gc.collect()

	print 'Train data shape:',X.shape

	np.random.seed(0) # seed to shuffle the train set

	shuffle = True

	if shuffle:
		idx = np.random.permutation(y.size)
		X = X[idx]
		y = y[idx]
	

	n_clfs = len(clfs)
	final_model = {}


	print "Creating train and test sets for blending."

	dataset_blend_train = np.zeros((X.shape[0], n_clfs))

	skf = list(cross_validation.KFold(len(y), n_folds, random_state=4002))

	for j, (clf,logfit) in enumerate(zip(clfs,logfits)):
		print j, logfit
		if j == 0:
			output = train_predict(clf,X,y,logfit,skf)
		else:
			output = train_predict_parallel(clf,X,y,logfit,skf)

		for _k, (test_1,y_pred) in enumerate(output):
			dataset_blend_train[test_1, j] = np.array(y_pred)

		try:
			clf.named_steps['regression'].n_jobs = 7
		except:
			pass
		if logfit:
			y_min = np.min(y)
			y_log = np.log(y-y_min+1)
			clf.fit(X, y_log)
		else:
			clf.fit(X,y)
		

	print
	print "Blending."
	reg.fit(dataset_blend_train,y)
	final_model['stage1'] = clfs
	final_model['stage2'] = reg
	final_model['logfits'] = logfits
	final_model['ymin'] = np.min(y)

	pickle.dump(final_model,open('../../data/models/model_fd_stacked_002.p','wb'))
