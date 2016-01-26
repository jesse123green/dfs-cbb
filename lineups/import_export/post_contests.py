import urllib2
import requests
import ssl
import json,pymysql,re
import numpy as np

def update_fanduel_lineups(gameid,lineups,token):
	headers = {'Host': 'api.fanduel.com','Connection': 'keep-alive','Accept': 'application/json, text/plain, */*',\
	'X-Auth-Token': token,\
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',\
	'Authorization': 'Basic N2U3ODNmMTE4OTIzYzE2NzVjNWZhYWFmZTYwYTc5ZmM6','Origin': 'https://www.fanduel.com',\
	'Referer': 'https://www.fanduel.com/games','Accept-Encoding': 'gzip, deflate, sdch','Accept-Language': 'en-US,en;q=0.8'}


	db = pymysql.connect("localhost","cbb","","cbb",charset="utf8",cursorclass=pymysql.cursors.DictCursor)
	c = db.cursor()
	c.execute("""SELECT entryid FROM fanduel_entries WHERE gameid=%s order by size desc""",(gameid,))

	entries = c.fetchall()
	# np.random.shuffle(entries) ## shuffle these guys up
	print 'hello dood'
	print len(entries)
		# return
	### define entry
	lineup_i = 0

	for entryid in entries:
		if lineup_i < len(lineups):
			lineup = lineups[lineup_i]
		else:
			lineup_i = 0
			lineup = lineups[lineup_i]
		k += 1

		entry = {"entries":[{"entry_fee":{"currency":"usd"},"roster":{"lineup":[]}}]}
		fanduel_lineup = [{},{},{},{},{},{},{},{},{}]
		indx = {'F':0,'G':5}

		for player in lineup[1]:
			m = re.search('[0-9][^A-Z]*', player)
			fid = m.group(0)
			pos = player.split(fid)[1]

			##### define entry
			fanduel_lineup[indx[pos]] = {"position":pos,"player":{"id":fid}}
			indx[pos] += 1
			# print pid,pos
		entry['entries'][0]['roster']['lineup'] = fanduel_lineup
		#### Put it
		
		req = requests.put('https://api.fanduel.com/entries/%i'%entryid['entryid'],json=entry,headers=headers,verify=False)
		print lineup[0],req.status_code,req.text,entryid['entryid']

	return



if __name__ == '__main__':
	update_fanduel_lineups(gameid,lineups,token)