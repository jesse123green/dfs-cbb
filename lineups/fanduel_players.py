import requests
import simplejson as json
from import_export.fanduel_utils import load_token
import pymysql,sys

def load_fanduel_players(gameid,token):

	headers = {'Host': 'api.fanduel.com','Connection': 'keep-alive','Accept': 'application/json, text/plain, */*',\
	'X-Auth-Token': token,\
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',\
	'Authorization': 'Basic N2U3ODNmMTE4OTIzYzE2NzVjNWZhYWFmZTYwYTc5ZmM6','Origin': 'https://www.fanduel.com',\
	'Referer': 'https://www.fanduel.com/games','Accept-Encoding': 'gzip, deflate, sdch','Accept-Language': 'en-US,en;q=0.8'}


	db = pymysql.connect("localhost","cbb","","cbb",charset="utf8",cursorclass=pymysql.cursors.DictCursor)
	c = db.cursor()
	url = "https://api.fanduel.com/fixture-lists/%s/players"%(str(gameid),)


	req = requests.get(url,headers=headers,verify=False)
	D = json.loads(req.text)

	# print json.dumps(D,indent=4)
	teams = {}
	for team in D['teams']:
		teams[team['id']] = team['code']

	home_away = {}
	opponents = {}
	for m in D['fixtures']:
		home_away[m['home_team']['team']['_members'][0]] = 1
		home_away[m['away_team']['team']['_members'][0]] = 0
		opponents[m['home_team']['team']['_members'][0]] = m['away_team']['team']['_members'][0]
		opponents[m['away_team']['team']['_members'][0]] = m['home_team']['team']['_members'][0]

	for player in D['players']:

		fid = player['id'].split('-')[1]
		team_id = player["team"]['_members'][0]
		team = teams[team_id]
		opp = teams[opponents[team_id]]
		home = home_away[team_id]

		try:
			injury = player['injury_status'].upper()
		except:
			injury = ''

		c.execute("""INSERT IGNORE INTO fanduel_contests (gameid,fid,fppg,team,opp,home,indicator,name,position,salary) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",\
		(gameid,fid,player['fppg'],team,opp,home,injury,player['first_name']+ ' ' + player['last_name'],player['position'],player['salary']))

		
		db.commit()

if __name__ == '__main__':
	try:
		gameid = sys.argv[1]
	except:
		raise('no game id!')



	load_fanduel_players(gameid,load_token())