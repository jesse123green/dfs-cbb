import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error
from sklearn import cross_validation
from sklearn.linear_model import Ridge,Lasso,LinearRegression,SGDRegressor
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor as GBR
from sklearn.ensemble import RandomForestRegressor,ExtraTreesRegressor

class CBB():
	def __init__(self):
		self.pre_processors = {}
		self.feature_headers = []
		self.X = []
		self.y = []

def load_blend_models():

	n_estimators = 1020
	params = {'n_estimators': n_estimators, 'max_depth': 4, 'min_samples_split': 5,'subsample':.5,
	'learning_rate': 0.01, 'loss': 'lad', 'random_state':91}
	reg_gbr = GBR(**params)

	reg_rf = Pipeline([
	('scale', preprocessing.StandardScaler()),
	('regression', RandomForestRegressor(max_depth=20,max_features=.5,n_estimators=750,min_samples_split=5,n_jobs=1,random_state=2))
	])

	reg_et = Pipeline([
	('scale', preprocessing.StandardScaler()),
	('regression', ExtraTreesRegressor(max_depth=20,max_features=.5,n_estimators=750,min_samples_split=5,n_jobs=1,random_state=2))
	])

	# C = .3
	# gamma=.003
	# epsilon = .3
	# reg_svr = Pipeline([
	# ('scale', preprocessing.StandardScaler()),
	# ('regression', SVR(epsilon=epsilon, gamma=gamma,C=C))
	# ])
	
	epsilon=1.5
	alpha=.002
	eta0=.005
	loss='epsilon_insensitive'
	l1_ratio=.85
	penalty='elasticnet'

	reg_sgd = Pipeline([
	('scale', preprocessing.StandardScaler()),
	('regression', SGDRegressor(n_iter=50,random_state=14,epsilon=epsilon,alpha=alpha,eta0=eta0,loss='epsilon_insensitive',l1_ratio=.85,penalty='elasticnet'))
	])	


	regs = [reg_sgd,reg_rf,reg_et,reg_gbr]
	logfits = [False,True,True,False]


	return regs,logfits