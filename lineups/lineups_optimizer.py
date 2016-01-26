import numpy as np
import time,pickle
from datetime import datetime,date,timedelta
import csv, sys, json, os
from sklearn import preprocessing
from sklearn.metrics import mean_squared_error,mean_absolute_error
import pylab as plt
from sklearn.pipeline import Pipeline
import pymysql
from players_dummy import CBB
from cvxopt import matrix
from cvxopt.glpk import ilp
from cvxopt import glpk
from collections import defaultdict
from operator import itemgetter
import itertools, copy
from functools import wraps
import errno
import os,gc
import signal
import multiprocessing
import warnings
from import_export.fanduel_utils import update_fanduel_lineups,load_token
# from import_export.get_contests import login

warnings.filterwarnings("ignore")

glpk.options['msg_lev'] = 'GLP_MSG_OFF'
# glpk.options['tm_lim'] = 1000
# glpk.options['meth'] = 'GLP_DUALP'


class lineupOptimizer():

	def __init__(self,excluded_players=[],excluded_teams=[],platform='fanduel',season='22015'):
		self.db = pymysql.connect("localhost","cbb","","cbb",charset="utf8",cursorclass=pymysql.cursors.DictCursor)
		self.all_players = []
		self.season = season
		self.excluded_players = excluded_players
		self.excluded_teams = excluded_teams
		self.platform = platform

		### Model parameters
		self.team_count = 0
		self.player_count = 0
		self.dup_player_count = 0
		self.all_players_dups = []
		self.dup_playersI = {}
		self.teamsI = {}
		self.matchup = {}

		### Model results
		self.lineups = []

	def n_lineups(self,gameid):
		c = self.db.cursor()
		c.execute("""SELECT count(*) as cnt FROM fanduel_entries WHERE gameid=%s""",(gameid))
		return int(c.fetchone()['cnt'])

	def get_players(self,gameid):

		c = self.db.cursor()

		if self.platform == 'fanduel':
			c.execute("""SELECT players.fid fid,pid,fc.name name,t.team team,fc.position,salary,home,o.team opp,pfp from fanduel_contests fc,players,teams t, teams o WHERE fc.team=t.fanduel and fc.opp = o.fanduel and fc.fid = players.fid and gameid = %s and pid not in (%s) and fc.team NOT IN (%s) and indicator NOT IN ('IR','O')"""%(gameid,"'" + "','".join(self.excluded_players)+ "'","'" + "','".join(self.excluded_teams)+ "'"))
			

			for result in c.fetchall():
				P = CBB(result['pid'],result['position'],result['team'],result['opp'],result['home'],result['salary'],result['name'],self.season,result['fid'])
				P.fantasy_prediction = result['pfp']
				if P.fantasy_prediction > 5:
					self.all_players.append(P)


		elif self.platform == 'draftkings':
			c.execute("""SELECT players.dkid dkid,pid,dk.name name,t.nba team,dk.position,salary,home,o.nba opp,pfp from draftkings_contests dk,players,teams t, teams o WHERE dk.team=t.dkid and dk.opp = o.dkid and dk.dkid = players.dkid and gameid = %s and pid not in (%s) and team NOT IN (%s) and indicator NOT IN ('O','Out')"""%(gameid,"'" + "','".join(self.excluded_players)+ "'","'" + "','".join(self.excluded_teams)+ "'"))
			

			for result in c.fetchall():
				P = NBADK(result['pid'],result['position'],result['team'],result['opp'],result['home'],result['salary'],result['name'],self.season,result['dkid'])
				P.fantasy_prediction = result['pfp']
				if P.fantasy_prediction > 5:
					self.all_players.append(P)			
		print 'Number of Players:',len(self.all_players)
		return

	def update_counts(self):
		dup_player_count = 0
		player_count = 0
		all_players = []
		dup_playersI = {}

		k = 0
		for _p in self.all_players:
			if type(_p.pos) is list:

				dup_playersI[_p.pid] = k
				dup_player_count += 1
				player_count += len(_p.pos)
				k += 1

				for _pos in _p.pos:
					all_players.append(copy.copy(_p))
					all_players[-1].pos = _pos
					# print all_players[-1].pos,all_players[-1].name
			else:
				player_count += 1
				all_players.append(_p)

		teams = {}
		teamsI = {}
		matchup = {}
		k = 0

		## Get unique teams
		for player in self.all_players:
			# print player.pid,player.name,player.team
			if teams.has_key(player.team):
				teams[player.team] += 1
			else:
				teams[player.team] = 1
				teams[player.opp] = 0
				teamsI[player.team] = k

				### matchup to guarantee players from n games
				matchup[player.team] = k
				matchup[player.opp] = k
				k += 1
				teamsI[player.opp] = k
				k += 1

		team_count = len(teams)
		print teamsI
		print 'Number of teams:',team_count
		self.all_players_dups = all_players
		self.team_count = team_count
		self.teamsI = teamsI
		self.dup_player_count = dup_player_count
		self.dup_playersI = dup_playersI
		self.player_count = player_count
		self.matchup = matchup

		return


	def choose_lineup(self,player_noise=0,verbose=False):
		c = []
		G = []
		A = []


		f = []
		teamG = np.zeros((self.team_count+1,self.player_count)) # number of players on team <=4 (+1 for salary)

		# print 'Number of teams:',team_count


		A = np.zeros((2,self.player_count)) # 5 positions

		positionI = {'F':0,'G':1}


		pI = 0

		for player in self.all_players:

			if player_noise > 0:
				noise = np.random.normal(0,player_noise)
			else:
				noise = 0

			## update teams
			teamG[self.teamsI[player.team]+1,pI] = 1 ## no more than 4 players from 1 team

			teamG[0,pI] = player.salary

			# print player.pid,noise,player.fantasy_prediction,noise+player.fantasy_prediction
			f.append(player.fantasy_prediction+noise)

			A[positionI[player.pos],pI] = 1


			pI += 1

		# print f
		c = matrix(f)
		G = matrix(teamG,tc='d')

		h = 4*np.ones((self.team_count+1,1)) ## only 4 players per team max
		h[0] = 60000 ## set salary constraints

		h = matrix(h,tc='d')

		A = matrix(A,tc='d')
		b = matrix([5,4],tc='d')

		# print G.size
		# print h.size

		# print A.size
		# print b.size
		# print b

		(status, sol) = ilp(-c,G,h,A,b,B=set(range(self.player_count)))

		# print(status, sol)

		total_sal = 0
		total_fp = 0
		unique_teams = defaultdict(int)

		sortedplayerlist = sorted(self.all_players, key=lambda k: k.fantasy_prediction/k.salary)

		if verbose:
			for row in range(player_count):
				print sortedplayerlist[row].pid,sortedplayerlist[row].pos,sortedplayerlist[row].name,sortedplayerlist[row].team,sortedplayerlist[row].salary,'%.2f'%sortedplayerlist[row].fantasy_prediction,'%.2f'%(sortedplayerlist[row].fantasy_prediction/sortedplayerlist[row].salary*1000.)
      
				print '\n'
				print '*'*40
				print '\n'

		lineup_pids = set()
		for row in range(self.player_count):
			if sol[row] == 1:
				if verbose:
					print self.all_players[row].pid,self.all_players[row].pos,self.all_players[row].name,self.all_players[row].team,self.all_players[row].salary,'%.2f'%self.all_players[row].fantasy_prediction,'%.2f'%(self.all_players[row].fantasy_prediction/self.all_players[row].salary*1000.)
				total_sal += self.all_players[row].salary
				total_fp += self.all_players[row].fantasy_prediction
				unique_teams[self.all_players[row].team] += 1
				lineup_pids.add(str(self.all_players[row].fid)+self.all_players[row].pos)
			elif self.all_players[row].pos == 'P':
				# print self.all_players[row].pid,self.all_players[row].pos,self.all_players[row].name,self.all_players[row].team,self.all_players[row].salary,self.all_players[row].fantasy_prediction
				pass
		if verbose:
			print '%i Unique Teams'%(len(unique_teams))
			print 'Total Salary: $%s'%total_sal
			print 'Projected Fantasy Points: %.2f'%total_fp

		return lineup_pids

	def choose_lineup_dk(self,player_noise=0,verbose=False):
		c = []
		G = []
		A = []


		f = []
		teamG = np.zeros((10+1,self.player_count)) # choose variable positions and salary

		# print 'Number of teams:',team_count


		A = np.zeros((1,self.player_count)) # choose 8 players

		positionI = {'PG':0,'SG':1,'SF':2,'PF':3,'C':4} ### at least one of these
		flexI = {'PG':5,'SG':5,'SF':6,'PF':6} ## at least 3 g,f
		flexII = {'PG':7,'SG':7,'SF':8,'PF':8,'C':9} ## at most 4 g,f; at most 2 C


		pI = 0

		for player in self.all_players:

			if player_noise > 0:
				noise = np.random.normal(0,player_noise)
			else:
				noise = 0

			## update teams

			teamG[positionI[player.pos]+1,pI] = -1
			if player.pos != 'C':
				teamG[flexI[player.pos]+1,pI] = -1
			teamG[flexII[player.pos]+1,pI] = 1

			teamG[0,pI] = player.salary

			# print player.pid,noise,player.fantasy_prediction,noise+player.fantasy_prediction
			f.append(player.fantasy_prediction+noise)

			A[0,pI] = 1


			pI += 1

		c = matrix(f)
		G = matrix(teamG,tc='d')

		h = np.ones((teamG.shape[0],1)) 
		h[0] = 50000 ## set salary constraints
		h[1:6] = -1 ## at least one pg,sg,sf,pf,c
		h[6:8] = -3 ## at least three g,f
		h[8:10] = 4 ## at most four g,f
		h[10] = 2 ## at most 2 centers

		h = matrix(h,tc='d')

		A = matrix(A,tc='d')
		b = matrix([8],tc='d') ## one center

		# print G.size
		# print h.size

		# print A.size
		# print b.size
		# print b

		(status, sol) = ilp(-c,G,h,A,b,B=set(range(self.player_count)))

		# print(status, sol)

		total_sal = 0
		total_fp = 0
		unique_teams = defaultdict(int)

		sortedplayerlist = sorted(self.all_players, key=lambda k: k.fantasy_prediction/k.salary)

		if verbose:
			for row in range(player_count):
				print sortedplayerlist[row].pid,sortedplayerlist[row].pos,sortedplayerlist[row].name,sortedplayerlist[row].team,sortedplayerlist[row].salary,'%.2f'%sortedplayerlist[row].fantasy_prediction,'%.2f'%(sortedplayerlist[row].fantasy_prediction/sortedplayerlist[row].salary*1000.)
      
				print '\n'
				print '*'*40
				print '\n'

		lineup_pids = set()
		for row in range(self.player_count):
			if sol[row] == 1:
				if verbose:
					print self.all_players[row].pid,self.all_players[row].pos,self.all_players[row].name,self.all_players[row].team,self.all_players[row].salary,'%.2f'%self.all_players[row].fantasy_prediction,'%.2f'%(self.all_players[row].fantasy_prediction/self.all_players[row].salary*1000.)
				total_sal += self.all_players[row].salary
				total_fp += self.all_players[row].fantasy_prediction
				unique_teams[self.all_players[row].team] += 1
				lineup_pids.add(str(self.all_players[row].dkid)+self.all_players[row].pos)
			elif self.all_players[row].pos == 'P':
				# print self.all_players[row].pid,self.all_players[row].pos,self.all_players[row].name,self.all_players[row].team,self.all_players[row].salary,self.all_players[row].fantasy_prediction
				pass
		if verbose:
			print '%i Unique Teams'%(len(unique_teams))
			print 'Total Salary: $%s'%total_sal
			print 'Projected Fantasy Points: %.2f'%total_fp

		return lineup_pids

	def mc_top_lineups(self,iterations,n_l,k_l,player_noise=0,useFirst=False):
		lineup_counts = defaultdict(int)
		lineups = {}

		bar_length = 30
		print '\n'*5

		## Run lineup optimizer with projection + noise
		
		# parent_conn,child_conn = multiprocessing.Pipe()
		for k in range(iterations):
			# queue1 = multiprocessing.Queue()
			# parent_conn,child_conn = multiprocessing.Pipe()
			if self.platform == 'draftkings':
				lineup = self.choose_lineup_dk(player_noise=player_noise)
				lineup_str = ''.join(np.array(sorted(list(lineup)),dtype=str))
				lineup_counts[lineup_str] += 1
				lineups[lineup_str] = lineup
			elif self.platform == 'fanduel':
				lineup = self.choose_lineup(player_noise=player_noise)
				lineup_str = ''.join(np.array(sorted(list(lineup)),dtype=str))
				lineup_counts[lineup_str] += 1
				lineups[lineup_str] = lineup

			## Progress bar

			percent = float(k) / iterations
			hashes = '#' * int(round(percent * bar_length))
			spaces = ' ' * (bar_length - len(hashes))
			sys.stdout.write("\rProgress: [%s] %.2f%%"%(hashes + spaces, percent * 100.))
			sys.stdout.flush()      
		
		print '\n'*5
		print 'Unique lineups =',len(lineups.keys())
		print_max = n_l
		k = 0
		top_lineups = []
		for key, value in sorted(lineup_counts.iteritems(), key=lambda (k,v): (v,k),reverse=True):
			k += 1
			print value, lineups[key]
			top_lineups.append(lineups[key])
			if k == print_max:
				break

		max_overlap = 1e9
		for i in list(itertools.combinations(enumerate(top_lineups), k_l)):
			if (i[0][0] != 0) and useFirst:
				continue
			overlap = 0

			## Compute overlap for valid lineups
			for sub_i in list(itertools.combinations(i, 2)):
				overlap += len(set.intersection(sub_i[0][1],sub_i[1][1]))

			## Choose lineups if is current best
			if overlap < max_overlap:
				output = i
				max_overlap = int(overlap)
			# print overlap
			# print '*'*40
		try:
			print output
		except:
			print 'No matches found! Try increasing n_l.'
			return


		all_players_unique = {}
		all_players_count = defaultdict(int)
		for l in output:
			print '*'*40
			total_sal = 0
			total_fp = 0
			for p in self.all_players_dups:
				try:
					fanid = str(p.fid)
				except:
					fanid = str(p.dkid)
				if fanid+p.pos in l[1]:
					# print str(p.fid),p.pos,p.name,p.team,str(p.salary),'%.2f'%p.fantasy_prediction,'%.2f'%(p.fantasy_prediction/p.salary*1000.)
					# print '|'.join([str(p.fid),p.pos,p.name,p.team,str(p.salary),'%.2f'%p.fantasy_prediction,'%.2f'%(p.fantasy_prediction/p.salary*1000.)])
					all_players_count[fanid] += 1
					all_players_unique[fanid] = '\t|\t'.join([str(fanid),str(p.pid),p.pos,p.name.ljust(25),str(p.team),str(p.salary),'%.2f'%p.fantasy_prediction,'%.2f'%(p.fantasy_prediction/p.salary*1000.)])
					print fanid,p.pos,p.name,p.team,p.salary,'%.2f'%p.fantasy_prediction,'%.2f'%(p.fantasy_prediction/p.salary*1000.)
					total_sal += p.salary
					total_fp += p.fantasy_prediction
			print 'Total Salary: $%s'%total_sal
			print 'Projected Fantasy Points: %.2f'%total_fp
			print '\n\n'

		headers = '\t|\t'.join(['dkid','pid','pos','name'.ljust(25),'team','salary','proj.','value','lineups'])
		print headers
		print '-'*len(headers)
		for p in all_players_unique:
			all_players_unique[p] += '\t|\t'+str(all_players_count[p])
			print all_players_unique[p]
		print 'Total unique player:',len(all_players_unique)

		return output

if __name__ == "__main__":

	try:
		gameid = sys.argv[1]
	except:
		gameid = 13273

	try:
		platform = sys.argv[2]
	except:
		platform = 'fanduel'

	t = time.time()
	ti= time.time()

	opt = lineupOptimizer(excluded_players=['',''],excluded_teams=[],platform=platform)


	print 'Load Players for Contest...'
	opt.get_players(gameid)
	opt.update_counts()

	# n_lineups = opt.n_lineups(gameid)
	n_lineups = 15
	print 'Solving for %i lineups...'%(n_lineups)
	gc.collect()
	t = time.time()
	if platform == 'fanduel':
		output = opt.mc_top_lineups(100000,n_l=n_lineups,k_l=n_lineups,player_noise=1.1,useFirst=True)
	elif platform == 'draftkings':
		# n_lineups = 35
		output = opt.mc_top_lineups(50000,n_l=n_lineups,k_l=n_lineups,player_noise=2,useFirst=True)
	
	var = raw_input("Would you like to export to fanduel? (Y/N)")
	if var == 'Y':
		update_fanduel_lineups(gameid,output,token=load_token())





