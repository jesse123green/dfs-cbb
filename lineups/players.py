import urllib2, json, sys, re, time, pickle, pymysql
from datetime import datetime,date,timedelta
import numpy as np

class CBB():

	model = pickle.load(open('../data/models/model_fd_stacked_001a.p','rb'))

	def __init__(self,pid,pos,team,opp,home,salary,name,season,fid=None):
		self.X = []
		self.is_valid = True
		self.pid = pid
		self.fid=fid
		self.pos_short = pos[-1]
		self.pos = pos
		self.team = team
		self.opp = opp
		self.season = int(season)
		self.home = home
		self.salary = salary
		self.name = name
		self.fantasy_prediction = 0.
		self.gamesPlayed = 0


	def daterange(self,start_date, end_date):
		for n in range(int ((end_date - start_date).days)):
			yield start_date + timedelta(n)

	def combine_features(self,X,xnew):
		xnew = np.array(xnew,dtype=float)
		if len(xnew.shape) == 1:
			xnew = xnew.reshape(xnew.shape[0], 1)
		return np.concatenate((X,xnew),axis=1)

	def historical_game_count(self,db):
		c = db.cursor()
		c.execute("SELECT count(*) cnt from gamelog,games WHERE games.gameid=gamelog.gameid AND games.season=%s and pid=%s",
		(self.season,self.pid))
		result = c.fetchone()
		# print result,self.season,self.pid
		try:
			self.gamesPlayed = int(result['cnt'])
		except:
			self.gamesPlayed = 0
		return


	def load_data(self,db):
		c = db.cursor()
		avg_stats = [25.87565,30.67279974484283,5.0116,10.9102,0.8971,2.4915,2.3553,3.0956,1.4124,4.1437,5.5561,2.9925,0.9959,0.6374,1.8225,2.3215,13.2756,0.3581]

		c.execute("""SELECT (avg(pts)+avg(reb)*1.2+avg(ast)*1.5+avg(blk)*2+avg(stl)*2-avg(tov)) fph, avg(min) min, avg(fgm) fgm,avg(fga) fga,avg(tpm) tpm,avg(tpa) tpa,avg(ftm) ftm,avg(fta) fta,avg(oreb) oreb,avg(dreb) dreb,avg(reb) reb,avg(ast) ast,avg(stl) stl,avg(blk) blk,avg(tov) tov,avg(pf) pf,avg(pts) pts from gamelog,games WHERE games.gameid=gamelog.gameid AND games.season=%s and pid=%s""",\
			(self.season,self.pid))
		result = c.fetchone()


		if result['fph'] == None:
			for v in avg_stats:
				self.X.append(v)
		else:
			for v in [float(result['fph']),float(result['min']),float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]:
				self.X.append(v)		
		return

	def home_away(self):
		self.X.append(self.home)
		return

	def previous_year(self,db):
		c = db.cursor()
		avg_stats = [25.87565,30.67279974484283,5.0116,10.9102,0.8971,2.4915,2.3553,3.0956,1.4124,4.1437,5.5561,2.9925,0.9959,0.6374,1.8225,2.3215,13.2756,0.3581]

		c.execute("""SELECT (avg(pts)+avg(reb)*1.2+avg(ast)*1.5+avg(blk)*2+avg(stl)*2-avg(tov)) fph, avg(min) min, avg(fgm) fgm,avg(fga) fga,avg(tpm) tpm,avg(tpa) tpa,avg(ftm) ftm,avg(fta) fta,avg(oreb) oreb,avg(dreb) dreb,avg(reb) reb,avg(ast) ast,avg(stl) stl,avg(blk) blk,avg(tov) tov,avg(pf) pf,avg(pts) pts from gamelog,games WHERE games.gameid=gamelog.gameid AND games.season=%s and pid=%s""",\
			(self.season-1,self.pid))
		result = c.fetchone()


		if result['fph'] == None:
			for v in avg_stats:
				self.X.append(v)
		else:
			for v in [float(result['fph']),float(result['min']),float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]:
				self.X.append(v)		
		return

	def position(self):

		if self.pos_short == 'C':
			positions = [1.,0.]
			# print self.pos
		elif self.pos_short == 'F':
			positions = [1.,0.]
			# print self.pos
		elif self.pos_short == 'G':
			positions = [0.,1.]
			# print self.pos
		for v in positions:
			self.X.append(v)
		
		return

	def past_n_games(self,n,db):
		c = db.cursor()
		c.execute("""SELECT (pts+reb*1.2+ast*1.5+blk*2+stl*2-tov) fph,min,fgm,fga,tpm,tpa,ftm,fta,oreb,dreb,reb,ast,stl,blk,tov,pf,pts from gamelog where pid=%s order by gametime desc limit %s """,\
			(self.pid,n))
		result = c.fetchall()
		# print self.pid
		for game in result:
			for v in [float(game['fph']),float(game['min']),float(game['fgm']),float(game['fga']),float(game['tpm']),float(game['tpa']),float(game['ftm']),float(game['fta']),float(game['oreb']),float(game['dreb']),float(game['reb']),float(game['ast']),float(game['stl']),float(game['blk']),float(game['tov']),float(game['pf']),float(game['pts'])]:
				self.X.append(v)
		return


	def add_team_averages(self,db):

		c = db.cursor()
		c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts \
				FROM gamelog,games where gamelog.team=%s and games.season=%s and games.gameid=gamelog.gameid""",\
			(self.team,self.season))
		result = c.fetchone()
		for v in [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]:
			self.X.append(v)
		return

	def add_opponent_averages(self,db):

		c = db.cursor()
		c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts \
				FROM gamelog,games where gamelog.team=%s and games.season=%s and games.gameid=gamelog.gameid""",\
			(self.opp,self.season))
		result = c.fetchone()
		for v in [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]:
			self.X.append(v)
		return

	def add_opponent_averages_limit(self,n,db):

		c = db.cursor()
		c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts FROM gamelog WHERE team=%s and gametime > (SELECT gametime from games where (home = %s or away = %s) order by gametime desc LIMIT 1 OFFSET %s)""",\
			(self.opp,self.opp,self.opp,n))
		result = c.fetchone()
		for v in [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]:
			self.X.append(v)
	
		return

	def add_team_averages_limit(self,n,db):

		c = db.cursor()
		c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts FROM gamelog WHERE team=%s and gametime > (SELECT gametime from games where (home = %s or away = %s) order by gametime desc LIMIT 1 OFFSET %s)""",\
			(self.team,self.team,self.team,n))
		result = c.fetchone()

		for v in [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]:
			self.X.append(v)
	
		return

	def add_opponent_position_defense(self,db):
		c = db.cursor()

		c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts \
				FROM gamelog,games where gamelog.pos=%s and gamelog.team != %s  and (games.home = %s or games.away = %s) and games.season=%s and games.gameid=gamelog.gameid""",\
			(self.pos_short,self.opp,self.opp,self.opp,self.season))
		result = c.fetchone()
		for v in [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]:
			self.X.append(v)
		return

	def add_opponent_defense_all(self,db):

		c = db.cursor()

		c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts \
				FROM gamelog,games where gamelog.team != %s  and (games.home = %s or games.away = %s) and games.season=%s and games.gameid=gamelog.gameid""",\
			(self.opp,self.opp,self.opp,self.season))
		result = c.fetchone()
		for v in [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]:
			self.X.append(v)
		return

	def add_opponent_defense_limit(self,n,db):

		c = db.cursor()

		c.execute("""SELECT SUM(fgm)/SUM(min) fgm,SUM(fga)/SUM(min) fga,SUM(tpm)/SUM(min) tpm,SUM(tpa)/SUM(min) tpa,SUM(ftm)/SUM(min) ftm,SUM(fta)/SUM(min) fta,SUM(oreb)/SUM(min) oreb,SUM(dreb)/SUM(min) dreb,SUM(reb)/SUM(min) reb,SUM(ast)/SUM(min) ast,SUM(stl)/SUM(min) stl,SUM(blk)/SUM(min) blk,SUM(tov)/SUM(min) tov,SUM(pf)/SUM(min) pf,SUM(pts)/SUM(min) pts FROM gamelog WHERE gamelog.team != %s  and (home = %s or away = %s) and gametime > (SELECT gametime from games where (home = %s or away = %s) order by gametime desc LIMIT 1 OFFSET %s)""",\
			(self.opp,self.opp,self.opp,self.opp,self.opp,n))
		result = c.fetchone()
		for v in [float(result['fgm']),float(result['fga']),float(result['tpm']),float(result['tpa']),float(result['ftm']),float(result['fta']),float(result['oreb']),float(result['dreb']),float(result['reb']),float(result['ast']),float(result['stl']),float(result['blk']),float(result['tov']),float(result['pf']),float(result['pts'])]:
				self.X.append(v)

		return

	def add_missed_games(self,n,db):
		c = db.cursor()

		c.execute("""SELECT count(*) game_cnt from gamelog where pid = %s and gametime > \
		(SELECT gametime from games where (home = %s or away = %s) order by gametime desc LIMIT 1 OFFSET %s)""",\
			(self.pid,self.team,self.team,n))
		result = c.fetchone()
		game_cnt = result['game_cnt']
		self.X.append(min(5,game_cnt))

		return

	def days_since_last_game(self,db):
		c = db.cursor()
		c.execute("""SELECT (DATEDIFF(CURDATE(),gameday)) as days_off from gamelog where pid = %s ORDER BY gameday DESC LIMIT 1""",\
			(self.pid))
		result = c.fetchone()
		days_off = result['days_off']

		self.X.append(days_off)

		return

	def add_games_played(self):

		if self.gamesPlayed < 15:
			for v in [1.,0.,0.]:
				self.X.append(v)
		elif self.gamesPlayed < 20:
			for v in [0.,1.,0.]:
				self.X.append(v)
		else:
			for v in [0.,0.,1.]:
				self.X.append(v)		
		return

	def add_team_rankings(self,db):
		c = db.cursor()
		
		c.execute("SELECT rank FROM rankings WHERE team=%s order by rankdate desc",(self.team,))
		teamresults = c.fetchone()
		
		c.execute("SELECT rank FROM rankings WHERE team=%s order by rankdate desc",(self.opp,))
		oppresults = c.fetchone()

		for v in [teamresults['rank'],oppresults['rank'],float(teamresults['rank'])-float(oppresults['rank'])]:
			self.X.append(v)

		return
		
	def previous_season_games_played(self,db):
		c = db.cursor()
		c.execute("SELECT count(*) cnt from gamelog,games WHERE games.gameid=gamelog.gameid AND games.season=%s and pid=%s",
		(self.season-1,self.pid))
		result = c.fetchone()
		try:
			previous_season_gamesPlayed = int(result['cnt'])
		except:
			previous_season_gamesPlayed = 0

		if previous_season_gamesPlayed < 10:
			for v in [1.,0.,0.,0.]:
				self.X.append(v)
		elif previous_season_gamesPlayed < 20:
			for v in [0.,1.,0.,0.]:
				self.X.append(v)
		elif previous_season_gamesPlayed < 30:
			for v in [0.,0.,1.,0.]:
				self.X.append(v)
		else:
			for v in [0.,0.,0.,1.]:
				self.X.append(v)

		return

	def populate_data(self):
		db = pymysql.connect("localhost","cbb","","cbb",charset="utf8",cursorclass=pymysql.cursors.DictCursor)
		self.historical_game_count(db)
		self.load_data(db)
		if self.gamesPlayed < 4:
			return
		self.add_games_played()
		self.position()
		self.home_away()
		self.past_n_games(5,db)
		self.add_team_averages(db)
		self.add_opponent_averages(db)
		self.add_opponent_position_defense(db)
		self.add_opponent_defense_all(db)
		self.add_missed_games(5,db)
		self.add_team_averages_limit(3,db)
		self.add_opponent_averages_limit(3,db)
		self.add_opponent_defense_limit(3,db)
		self.add_team_rankings(db)
		return

	def predict(self):
		# print 'predicting'
		# print self.gamesPlayed

		# self.fantasy_prediction = np.random.rand()
		# return
		if self.gamesPlayed > 9 and self.is_valid:
			data = np.array(self.X,dtype=float)

			#### SINGLE ########
			# model = pickle.load(open('../data/models/model_players_fd_GBR_200.p','rb'))
			# p = self.model['reg'].predict(data)[0]
			#######################
			

			#### STACKED ########
			y_preds = []
			for reg,logfit in zip(self.model['stage1'],self.model['logfits']):
				if logfit:
					y_preds.append(np.exp(reg.predict(data)[0])+self.model['ymin']-1)
				else:
					y_preds.append(reg.predict(data)[0])
			p = self.model['stage2'].predict(y_preds)[0]
			#######################
			# print p,type(p),self.pid,self.name
			self.fantasy_prediction = float(p)

			if self.fantasy_prediction < 0 or self.fantasy_prediction > 5 or True:
				print self.pid,self.name,self.salary,self.fantasy_prediction,self.gamesPlayed,self.team

		else:

			# print 'not enough games for player:',self.gamesPlayed,self.name
			self.fantasy_prediction = 0.

		return self.fantasy_prediction		


if __name__ == "__main__":

	pass
