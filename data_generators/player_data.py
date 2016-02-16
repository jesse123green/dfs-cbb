import urllib2, json, sys, re, time, pickle, pymysql
from datetime import datetime,date,timedelta
import numpy as np

db = pymysql.connect("localhost","cbb","","cbb",charset="utf8",cursorclass=pymysql.cursors.DictCursor)

class CBB():

	def __init__(self):
		self.pre_processors = {}
		self.feature_headers = []
		self.X = []
		self.y = []


	def daterange(self,start_date, end_date):
		for n in range(int ((end_date - start_date).days)):
			yield start_date + timedelta(n)

	def combine_features(self,X,xnew):
		xnew = np.array(xnew,dtype=float)
		if len(xnew.shape) == 1:
			xnew = xnew.reshape(xnew.shape[0], 1)
		return np.concatenate((X,xnew),axis=1)

	def load_data(self,min_games=10,min_avg_fp=7):
		c = db.cursor()
		self.X = []
		self.y = []
		c.execute("""SELECT DATE(MIN(gametime)) start,DATE(MAX(gametime)) stop from games""")
		days = c.fetchone()

		c.execute("""SELECT distinct(team) t from rankings""")
		ranked_teams = {}
		for team in c.fetchall():
			ranked_teams[team['t']] = 0

		# avg_stats = [25.87565,30.67279974484283,5.0116,10.9102,0.8971,2.4915,2.3553,3.0956,1.4124,4.1437,5.5561,2.9925,0.9959,0.6374,1.8225,2.3215,13.2756,0.3581]
		# n_fea = len(avg_stats)

		# for aday in self.daterange(days['stop']-timedelta(5),days['stop']+timedelta(1)):
		# for aday in self.daterange(days['start'],days['stop']+timedelta(1)):
		for aday in self.daterange(date(2015,1,8),days['stop']+timedelta(1)):
			print aday

			c.execute("SELECT today.opponent opponent,today.season season,today.team team,today.pid pid,today.gameid today_gameid,today.pos today_pos,(today.pts+today.reb*1.2+today.ast*1.5+today.blk*2+today.stl*2-today.tov) today_fp,\
			(hist.avg_pts+hist.avg_reb*1.2+hist.avg_ast*1.5+hist.avg_blk*2+hist.avg_stl*2-hist.avg_tov) fph,hist.avg_min as hist_min,hist.avg_fgm as hist_fgm,hist.avg_fga as hist_fga,hist.avg_tpm as hist_tpm,hist.avg_tpa as hist_tpa,hist.avg_ftm as hist_ftm,hist.avg_fta as hist_fta,hist.avg_oreb as hist_oreb,hist.avg_dreb as hist_dreb,hist.avg_reb as hist_reb,hist.avg_ast as hist_ast,hist.avg_stl as hist_stl,hist.avg_blk as hist_blk,hist.avg_tov as hist_tov,hist.avg_pf as hist_pf,hist.avg_pts as hist_pts,hist.cpid as hist_game_count,cpid \
			FROM \
			(SELECT pid,count(pid) cpid,avg(min) avg_min, avg(fgm) avg_fgm,avg(fga) avg_fga,avg(tpm) avg_tpm,avg(tpa) avg_tpa,avg(ftm) avg_ftm,avg(fta) avg_fta,avg(oreb) avg_oreb,avg(dreb) avg_dreb,avg(reb) avg_reb,avg(ast) avg_ast,avg(stl) avg_stl,avg(blk) avg_blk,avg(tov) avg_tov,avg(pf) avg_pf,avg(pts) avg_pts from gamelog,games WHERE games.gameid=gamelog.gameid AND date(games.gametime) < %s AND games.season=(SELECT season FROM games WHERE date(gametime)=%s LIMIT 1) group by pid having count(pid) > %s and (avg(pts)+avg(reb)*1.2+avg(ast)*1.5+avg(blk)*2+avg(stl)*2-avg(tov))>%s) AS hist,\
			(SELECT IF(team=games.home,games.away,games.home) opponent,season,team,games.gameid,pid,pts,reb,ast,blk,stl,tov,pos FROM gamelog,games WHERE games.gameid=gamelog.gameid AND date(games.gametime) = %s AND pos!='NA' AND min IS NOT NULL) AS today \
			WHERE hist.pid = today.pid order by today.gameid,today.pid;",
			(aday,aday,min_games,min_avg_fp,aday))

			for d in c.fetchall():
				if ranked_teams.has_key(d['team']) and ranked_teams.has_key(d['opponent']):
					fh = {}
					fh['pid'] = d['pid']
					fh['gameid'] = d['today_gameid']
					fh['pos'] = d['today_pos']
					if fh['pos'] == 'C':
						fh['pos'] = 'F'
					fh['team'] = d['team']
					fh['season'] = d['season']
					fh['gametime'] = aday
					fh['opponent'] = d['opponent']
					fh['game_count'] = d['cpid']
					fh['fph'] = float(d['fph'])
					# print d['team'],aday
					
					self.feature_headers.append(fh)

					self.y.append(float(d['today_fp']))
					historical_stats = [float(d['fph']),float(d['hist_min']),float(d['hist_fgm']),float(d['hist_fga']),float(d['hist_tpm']),float(d['hist_tpa']),float(d['hist_ftm']),float(d['hist_fta']),float(d['hist_oreb']),float(d['hist_dreb']),float(d['hist_reb']),float(d['hist_ast']),float(d['hist_stl']),float(d['hist_blk']),float(d['hist_tov']),float(d['hist_pf']),float(d['hist_pts'])]

					self.X.append(historical_stats)

		self.X = np.array(self.X,dtype=float)
		return

	def position(self):
		positions = []
		k = 0
		for row in self.feature_headers:

			if row['pos'] == 'C':
				positions.append([1.,0.])
			elif row['pos'] == 'F':
				positions.append([1.,0.])
			elif row['pos'] == 'G':
				positions.append([0.,1.])

		self.X = self.combine_features(self.X,positions)
		return

	def games_played(self):
		gp = []
		k = 0
		for row in self.feature_headers:

			if row['game_count'] < 15:
				gp.append([1.,0.,0.])
			elif row['game_count'] < 20:
				gp.append([0.,1.,0.])
			else:
				gp.append([0.,0.,1.])

		self.X = self.combine_features(self.X,gp)
		return

	def games_played_last_year(self):
		gp = []
		k = 0
		for row in self.feature_headers:

			if row['n_games_last_year'] < 10:
				gp.append([1.,0.,0.,0.])
			elif row['n_games_last_year'] < 20:
				gp.append([0.,1.,0.,0.])
			elif row['n_games_last_year'] < 30:
				gp.append([0.,0.,1.,0.])
			else:
				gp.append([0.,0.,0.,1.])

		self.X = self.combine_features(self.X,gp)
		return

	def home_away(self):
		c = db.cursor()
		homeaway = []

		for row in self.feature_headers:
			c.execute("SELECT IF(gamelog.team = gamelog.home,1,0) ha,gamelog.team,home,away FROM gamelog WHERE gamelog.gameid = %s and gamelog.pid = %s",(row['gameid'],row['pid']))
			result = c.fetchone()
			homeaway.append(float(result['ha']))
			# print result['ha'],result['team'],result['home'],result['away']
		self.X = self.combine_features(self.X,homeaway)
		return

	def previous_year(self):
		c = db.cursor()
		last_year = []
		avg_stats = [16.75161286,23.95441817,3.05738002,6.89188935,0.83262512,2.36660795,1.7999249,2.56890417,1.10152368,2.7724201,3.87394385,1.62841595,0.7814614,0.42406357,1.49812266,2.12166462,8.74732903]
		n_fea = len(avg_stats)

		for row in self.feature_headers:
			c.execute("""SELECT count(*) as game_count,(avg(pts)+avg(reb)*1.2+avg(ast)*1.5+avg(blk)*2+avg(stl)*2-avg(tov)) fph, avg(min) min, avg(fgm) fgm,avg(fga) fga,avg(tpm) tpm,avg(tpa) tpa,avg(ftm) ftm,avg(fta) fta,avg(oreb) oreb,avg(dreb) dreb,avg(reb) reb,avg(ast) ast,avg(stl) stl,avg(blk) blk,avg(tov) tov,avg(pf) pf,avg(pts) pts from gamelog,games WHERE games.gameid=gamelog.gameid AND games.season=(SELECT season-1 FROM games WHERE gametime=%s LIMIT 1) and pid=%s""",\
				(row['gametime'],row['pid']))
			result = c.fetchone()

			if result['fph'] == None:
				last_year.append(avg_stats)
				row['n_games_last_year'] = 0
			else:
				last_year.append([float(result['fph']),float(result['min']),float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])])
				row['n_games_last_year'] = result['game_count']

		self.X = self.combine_features(self.X,last_year)
		return

	def past_n_games(self,n):
		c = db.cursor()
		n_fea = 17
		past_games = []
		k=0
		for row in self.feature_headers:
			c.execute("""SELECT (pts+reb*1.2+ast*1.5+blk*2+stl*2-tov) fph,min,fgm,fga,tpm,tpa,ftm,fta,oreb,dreb,reb,ast,stl,blk,tov,pf,pts from gamelog WHERE gamelog.pid=%s and gametime < %s order by gametime desc limit %s """,\
				(row['pid'],row['gametime'],n))
			result = c.fetchall()



			d = []
			for game in result:
				try:
					d.append([float(game['fph']),float(game['min']),float(game['fgm']),float(game['fga']),float(game['tpm']),float(game['tpa']),float(game['ftm']),float(game['fta']),float(game['oreb']),float(game['dreb']),float(game['reb']),float(game['ast']),float(game['stl']),float(game['blk']),float(game['tov']),float(game['pf']),float(game['pts'])])
				except:
					print 'BAD MINUTES'
					mins = []
					for game in result:
						try:
							mins.append(float(game['min']))
						except:
							pass
					try:
						min_avg = np.mean(mins)
					except:
						min_avg = 0
					print k,mins,min_avg
					k += 1


					d.append([float(game['fph']),float(min_avg),float(game['fgm']),float(game['fga']),float(game['tpm']),float(game['tpa']),float(game['ftm']),float(game['fta']),float(game['oreb']),float(game['dreb']),float(game['reb']),float(game['ast']),float(game['stl']),float(game['blk']),float(game['tov']),float(game['pf']),float(game['pts'])])


			past_games.append(np.reshape(d,(n_fea*n,)))
		self.X = self.combine_features(self.X,past_games)
		return

	def add_team_averages(self):

		c = db.cursor()
		team_stats = []

		for row in self.feature_headers:
			c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts \
				FROM gamelog,games where gamelog.team=%s and games.gametime < %s and games.season=%s and games.gameid=gamelog.gameid and gamelog.min is not null""",\
				(row['team'],row['gametime'],row['season']))
			result = c.fetchone()
			team_stats.append([float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])])
			# print [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]
		self.X = self.combine_features(self.X,team_stats)
		return

	def add_opponent_averages(self):

		c = db.cursor()
		team_stats = []

		for row in self.feature_headers:
			# print row
			c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts \
				FROM gamelog,games where gamelog.team=%s and games.gametime < %s and games.season=%s and games.gameid=gamelog.gameid and gamelog.min is not null""",\
				(row['opponent'],row['gametime'],row['season']))
			result = c.fetchone()
			team_stats.append([float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])])
			# print [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]
		self.X = self.combine_features(self.X,team_stats)
		return

	def add_team_averages_limit(self,n):

		c = db.cursor()
		team_stats = []

		for row in self.feature_headers:
			c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts FROM gamelog WHERE min is not null and team=%s and gametime < %s and gametime > (SELECT gametime from games where gametime < %s and (home = %s or away = %s) order by gametime desc LIMIT 1 OFFSET %s)""",\
				(row['team'],row['gametime'],row['gametime'],row['team'],row['team'],n))
			result = c.fetchone()
			team_stats.append([float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])])
			# print [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]
		self.X = self.combine_features(self.X,team_stats)
		return

	def add_opponent_averages_limit(self,n):

		c = db.cursor()
		team_stats = []

		for row in self.feature_headers:
			c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts FROM gamelog WHERE min is not null and team=%s and gametime < %s and gametime > (SELECT gametime from games where gametime < %s and (home = %s or away = %s) order by gametime desc LIMIT 1 OFFSET %s)""",\
				(row['opponent'],row['gametime'],row['gametime'],row['opponent'],row['opponent'],n))
			result = c.fetchone()
			team_stats.append([float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])])
			# print [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]
		self.X = self.combine_features(self.X,team_stats)
		return


	def add_opponent_position_defense(self):
		## Center,Forward,Guard
		n_fea = 15
		c = db.cursor()
		team_stats = []

		for row in self.feature_headers:
			# print row
			c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts \
				FROM gamelog,games where gamelog.pos=%s and gamelog.team != %s  and (games.home = %s or games.away = %s) and games.gametime < %s and games.season=%s and games.gameid=gamelog.gameid and gamelog.min is not null""",\
				(row['pos'],row['opponent'],row['opponent'],row['opponent'],row['gametime'],row['season']))
			result = c.fetchone()
			team_stats.append([float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])])

		self.X = self.combine_features(self.X,team_stats)
		return

	def add_opponent_defense_all(self):

		c = db.cursor()
		team_stats = []

		for row in self.feature_headers:
			c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts \
				FROM gamelog,games where gamelog.team != %s  and (games.home = %s or games.away = %s) and games.gametime < %s and games.season=%s and games.gameid=gamelog.gameid and gamelog.min is not null""",\
				(row['opponent'],row['opponent'],row['opponent'],row['gametime'],row['season']))
			result = c.fetchone()
			team_stats.append([float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])])

		self.X = self.combine_features(self.X,team_stats)
		return

	def add_opponent_defense_limit(self,n):

		c = db.cursor()
		team_stats = []

		for row in self.feature_headers:

			c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts FROM gamelog where gamelog.team != %s  and (home = %s or away = %s) and gametime < %s and gamelog.min is not null and gametime > (SELECT gametime from games where gametime < %s and (home = %s or away = %s) order by gametime desc LIMIT 1 OFFSET %s)""",\
				(row['opponent'],row['opponent'],row['opponent'],row['gametime'],row['gametime'],row['opponent'],row['opponent'],n))
			result = c.fetchone()
			# print row
			# print result
			# print '-'*20
			team_stats.append([float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])])

		self.X = self.combine_features(self.X,team_stats)
		return

	def add_opponent_defense_position_limit(self,n):

		c = db.cursor()
		team_stats = []

		for row in self.feature_headers:
			c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts FROM gamelog where pos=%s and gamelog.team != %s  and (home = %s or away = %s) and gametime < %s and gamelog.min is not null and gametime > (SELECT gametime from games where gametime < %s and (home = %s or away = %s) order by gametime desc LIMIT 1 OFFSET %s)""",\
				(row['pos'],row['opponent'],row['opponent'],row['opponent'],row['gametime'],row['gametime'],row['opponent'],row['opponent'],n))
			result = c.fetchone()
			team_stats.append([float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])])

		self.X = self.combine_features(self.X,team_stats)
		return

	def add_opponent_stength_of_schedule(self): ## opponent_opponent_offense_historical

		c = db.cursor()
		c2 = db.cursor()
		team_stats = []
		sos_data = {}

		for row in self.feature_headers:
			team_sos = []
			c.execute("""SELECT gamelog.gameid,IF(gamelog.team=gamelog.home,gamelog.away,gamelog.home) opponent,gamelog.gametime gametime from gamelog,games where games.gameid=gamelog.gameid and team = %s and gamelog.gametime < %s and games.season=%s group by gameid""",(row['opponent'],row['gametime'],row['season']))
			for game in c.fetchall():
				if sos_data.has_key((game['opponent'],game['gametime'])):
					team_sos.append(sos_data[(game['opponent'],game['gametime'])])
				else:
					c2.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts FROM gamelog,games where games.season=%s and games.gameid=gamelog.gameid and gamelog.team = %s and gamelog.gametime < %s""",\
					(row['season'],row['opponent'],row['gametime']))
					result = c2.fetchone()
					team_sos.append([float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])])
					sos_data[(game['opponent'],game['gametime'])] = [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]
			# print row
			# print team_sos
			# print np.mean(team_sos,axis=0)
			# print '-'*10
			team_stats.append(np.mean(team_sos,axis=0))
		self.X = self.combine_features(self.X,team_stats)
		return

	def add_missed_games(self,n):
		c = db.cursor()
		missed_games = []

		for row in self.feature_headers:
			c.execute("""SELECT count(*) game_cnt from gamelog where gametime < %s AND pid = %s and gametime > \
			(SELECT gametime from games where gametime < %s and (home = %s or away = %s) order by gametime desc LIMIT 1 OFFSET %s)""",\
				(row['gametime'],row['pid'],row['gametime'],row['team'],row['team'],n))
			result = c.fetchone()
			game_cnt = result['game_cnt']
			# print row['gametime'],row['pid'],row['gametime'],row['team'],row['team'],n
			# game_cnt_cat = np.zeros((n+1,))
			# game_cnt_cat[min(5,game_cnt)] = 1.
			missed_games.append(min(5,game_cnt))
			# print row['gametime'],game_cnt_cat,game_cnt
		self.X = self.combine_features(self.X,missed_games)
		return

	def days_since_last_game(self):
		c = db.cursor()
		days_off_all = []

		for row in self.feature_headers:
			c.execute("""SELECT (DATEDIFF(%s,gametime)) as days_off from gamelog where gametime < %s AND pid = %s ORDER BY gametime DESC LIMIT 1""",\
				(row['gametime'],row['gametime'],row['pid']))
			result = c.fetchone()
			days_off = result['days_off']

			days_off_all.append(days_off)
			# print row['pid'],row['gametime'],days_off,np.max(days_off_all)
		self.X = self.combine_features(self.X,days_off_all)
		return

	def add_team_rankings(self):
		c = db.cursor()
		c2 = db.cursor()
		rankings = []
		for row in self.feature_headers:
			c.execute("SELECT rank FROM rankings WHERE team=%s and rankdate <= %s order by rankdate desc",(row['team'],row['gametime']))
			c2.execute("SELECT rank FROM rankings WHERE team=%s and rankdate <= %s order by rankdate desc",(row['opponent'],row['gametime']))
			teamresults = c.fetchone()
			oppresults = c2.fetchone()
			rankings.append([teamresults['rank'],oppresults['rank'],float(teamresults['rank'])-float(oppresults['rank'])])
			# print [teamresults['rank'],oppresults['rank'],float(teamresults['rank'])-float(oppresults['rank'])]
		self.X = self.combine_features(self.X,rankings)
		return

	def add_missed_games_ts(self,n):
		c = db.cursor()
		missed_games = []

		for row in self.feature_headers:
			c.execute("""SELECT games.gameid,gamelog.gameid from games left outer join gamelog on gamelog.gameid = games.gameid and pid=%s where (games.home = %s or games.away = %s) and games.gametime < %s and games.gametime > \
			(SELECT gametime from games where gametime < %s and (home = %s or away = %s) order by gametime desc LIMIT 1 OFFSET %s)""",\
				(row['pid'],row['team'],row['team'],row['gametime'],row['gametime'],row['team'],row['team'],n))
			result = c.fetchall()

			d = []
			# print '--'*10
			for game in result:
				if game['gamelog.gameid'] == None:
					d.append(0)
				else:
					d.append(1)

			missed_games.append(d)
		self.X = self.combine_features(self.X,missed_games)
		return		

	def fph_threshold(self,n):
		below_thresh = []
		for row in self.feature_headers:
			if row['fph'] < 10:
				below_thresh.append(1)
			else:
				below_thresh.append(0)
		self.X = self.combine_features(self.X,below_thresh)
		return

if __name__ == "__main__":

	t = time.time()
	ti= time.time()
	P = CBB()

	print 'Loading historical player stats...'
	P.load_data()
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	print 'Adding games played...'
	P.games_played()
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()
	
	print 'Adding position categories...'
	P.position()
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	print 'Adding home/away...'
	P.home_away()
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	print 'Adding past n games...'
	P.past_n_games(5)
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	print 'Adding team stats...'
	P.add_team_averages()
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	print 'Adding opponent stats...'
	P.add_opponent_averages()
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	print 'Adding opponent stats against position...'
	P.add_opponent_position_defense()
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	print 'All games for opponent defense...'
	P.add_opponent_defense_all()
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	print 'Team rankings...' # 
	P.add_team_rankings()
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	print 'Opponent averages limit...'
	P.add_opponent_averages_limit(3)
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	print 'Games missed...'
	P.add_missed_games_ts(3)
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	print 'Opponent defense limit...' # optimized 2016-02-15
	P.add_opponent_defense_limit(4)
	print P.X.shape
	print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	ti= time.time()

	##################### TESTING #############################	

	# P = pickle.load(open('../data/train/P_fd_004.p','rb'))

	# print 'Team averages limit...'
	# P.add_team_averages_limit(1)
	# print P.X.shape
	# print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	# ti= time.time()

	####################### DUMP ###########################

	pickle.dump(P,open('../data/train/P_fd_004.p','wb'))
	
	####################### REMOVED ###########################

	# print 'Opponent strength of schedule...' # optimized 2016-02-15
	# P.add_opponent_stength_of_schedule()
	# print P.X.shape
	# print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	# ti= time.time()

	# print 'Games missed...'
	# P.add_missed_games(5)
	# print P.X.shape
	# print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	# ti= time.time()

	# print 'Loading player stats for previous year...' # removed 2016-02-15
	# P.previous_year()
	# print P.X.shape
	# print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	# ti= time.time()

	# print 'Adding games played last year...'# removed 2016-02-15
	# P.games_played_last_year()
	# print P.X.shape
	# print 'Finished after %.2f mins\n'%((time.time()-ti)/60.)
	# ti= time.time()	

	

