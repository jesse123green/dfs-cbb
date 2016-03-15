import numpy as np
import time,pickle
from datetime import datetime,date,timedelta
import csv, sys, json, os
from sklearn import preprocessing
from sklearn.metrics import mean_squared_error,mean_absolute_error
import pylab as plt
from sklearn.pipeline import Pipeline
import pymysql
from players import CBB
from cvxopt import matrix
from collections import defaultdict
from operator import itemgetter
import itertools, copy
from functools import wraps
import errno
import os
import signal
import multiprocessing
import warnings


def create_player(pid,position,team,opp,home,salary,name,season,fid):
	P = CBB(pid,position,team,opp,home,salary,name,season,fid)
	P.populate_data()
	P.predict()
	return P

def create_player_dk(pid,position,team,opp,home,salary,name,season,dkid):
	P = CBBDK(pid,position,team,opp,home,salary,name,season,dkid)
	P.populate_data()
	P.predict()
	return P

def get_players(gameid,platform,season):
	dbc = json.load(open('../credentials/db.json','rb'))
	live = dbc[dbc['live']]
	db = pymysql.connect(live['host'],live['user'],live['pw'],live['db'],charset="utf8",cursorclass=pymysql.cursors.DictCursor)

	c = db.cursor()

	if platform == 'fanduel':
		c.execute("""SELECT fc.fid fid,pid,fc.name name,t.team team,fc.position,salary,home,o.team opp from fanduel_contests fc,players,teams t, teams o WHERE fc.team=t.fanduel and fc.opp = o.fanduel and fc.fid = players.fid and gameid = %s"""%(gameid,))
		

		pool = multiprocessing.Pool(processes=8)
		results = [pool.apply_async(create_player, args=(result['pid'],result['position'],result['team'],result['opp'],result['home'],result['salary'],result['name'],season,result['fid'])) for result in c.fetchall()]

		output = [p.get() for p in results]
		pool.close()
		pool.terminate()
		pool.join()

		# for result in c.fetchall():
		# 	create_player(result['pid'],result['position'],result['team'],result['opp'],result['home'],result['salary'],result['name'],season,result['fid'])

		for F in output:
			c.execute("""UPDATE fanduel_contests SET pfp=%s WHERE gameid=%s and fid=%s """,(F.fantasy_prediction,gameid,F.fid))
		db.commit()

	elif platform == 'draftkings':
		c.execute("""SELECT dk.dkid dkid,pid,dk.name name,t.team team,dk.position,salary,home,o.team opp from draftkings_contests dk,players,teams t, teams o WHERE dk.team=t.dkid and dk.opp = o.dkid and dk.dkid = players.dkid and gameid = %s"""%(gameid,))
		
		# print 'dk',gameid
		pool = multiprocessing.Pool(processes=4)
		results = [pool.apply_async(create_player_dk, args=(result['pid'],result['position'],result['team'],result['opp'],result['home'],result['salary'],result['name'],season,result['dkid'])) for result in c.fetchall()]
		output = [p.get() for p in results]
		pool.close()
		pool.terminate()
		pool.join()

		# for result in c.fetchall():
		# 	create_player_dk(result['pid'],result['position'],result['team'],result['opp'],result['home'],result['salary'],result['name'],season,result['dkid'])

		for F in output:
			# print F.pid,F.fantasy_prediction
			c.execute("""UPDATE draftkings_contests SET pfp=%s WHERE gameid=%s and dkid=%s """,(F.fantasy_prediction,gameid,F.dkid))
		db.commit()

	return


if __name__ == "__main__":
	try:
		gameid = sys.argv[1]
	except:
		gameid = 13273

	try:
		platform = sys.argv[2]
	except:
		platform = 'fanduel'

	get_players(gameid,platform,season='2015')

