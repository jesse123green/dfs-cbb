import json, sys, pickle
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error
from sklearn import cross_validation
from sklearn.linear_model import Ridge,Lasso,LinearRegression,SGDRegressor
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor as GBR
from sklearn.ensemble import RandomForestRegressor,ExtraTreesRegressor
import xgboost as xgb
from sklearn.decomposition import PCA

class CBB():
	def __init__(self):
		self.pre_processors = {}
		self.feature_headers = []
		self.X = []
		self.y = []

def load_blend_models():

	n_estimators = 1095
	params = {'n_estimators': n_estimators, 'max_depth': 4, 'min_samples_leaf': 20,'subsample':.3,
	'learning_rate': 0.01, 'loss': 'lad', 'random_state':91}
	reg_gbr = GBR(**params)
	
	reg_rf = Pipeline([
	('scale', preprocessing.StandardScaler()),
	('regression', RandomForestRegressor(max_depth=20,max_features=.5,n_estimators=750,min_samples_leaf=20,n_jobs=1,random_state=2))
	])

	reg_et = Pipeline([
	('scale', preprocessing.StandardScaler()),
	('regression', ExtraTreesRegressor(max_depth=20,max_features=.5,n_estimators=750,min_samples_leaf=20,n_jobs=1,random_state=2))
	])


	params_xgb = {'n_estimators': 780, 'max_depth': 4, 'subsample':.45,'learning_rate': 0.01,'seed':88}
	reg_xgb = xgb.XGBRegressor(**params_xgb)
	
	epsilon=1.5
	alpha=.003
	eta0=.003
	loss='epsilon_insensitive'
	l1_ratio=.85
	penalty='l1'

	reg_sgd = Pipeline([
	('pca',PCA(n_components = 45)),
	('scale', preprocessing.StandardScaler()),
	('regression', SGDRegressor(n_iter=50,random_state=14,epsilon=epsilon,alpha=alpha,eta0=eta0,loss=loss,l1_ratio=l1_ratio,penalty=penalty))
	])	


	regs = [reg_sgd,reg_rf,reg_xgb,reg_gbr]
	logfits = [False,True,True,False]

	# regs = [reg_sgd,reg_xgb]
	# logfits = [False,True]

	return regs,logfits

