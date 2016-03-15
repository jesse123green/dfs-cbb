## Match fanduel players with database

import pymysql
import sys

def sync_players(gameid):
	dbc = json.load(open('../credentials/db.json','rb'))
	live = dbc[dbc['live']]
	db = pymysql.connect(live['host'],live['user'],live['pw'],live['db'],charset="utf8",cursorclass=pymysql.cursors.DictCursor)


	c = db.cursor()
	c2 = db.cursor()
	c3 = db.cursor()

	c.execute("""SELECT fc.fid,fc.name,fc.position,fc.team FROM fanduel_contests fc WHERE fc.fppg>0 and fc.gameid=%s and fc.fid NOT IN (SELECT fid FROM players where fid is not null) GROUP BY fc.fid""",(gameid,))

	for result in c.fetchall():
		# print 'SOME RESULTS!'
		name = result[1]
		# print name_modified
		c2.execute("""SELECT distinct(pid) FROM players WHERE name = %s""",(name,))
		# else:
		# 	c2.execute("""SELECT distinct(pid) FROM batters WHERE name = %s""",(result[1],))

		players = c2.fetchall()

		if len(players) == 1:
			print 'INSERTING PLAYER:',result[0],result[1],name
			c3.execute("""UPDATE players SET fid = %s , fanduel=%s WHERE name=%s""",(result[0],result[1],result[1]))
			db.commit()
		elif len(players) == 0:
			print 'NO MATCHES'
			print result
		else:
			print 'MULTIPLE MATCHES'
			print result

if __name__ == "__main__":
	try:
		gameid = sys.argv[1]
	except:
		raise("NO GAMEID GIVEN")	

	sync_players(gameid)