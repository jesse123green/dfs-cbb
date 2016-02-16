import urllib2
import requests,re
import ssl,json,sys,pymysql
import numpy as np


def load_token():
	f = open('/Users/jessegreen/Documents/fantasy/token.txt','rb')
	return str(f.readline().strip())

def update_results(token):

	headers = {'Host': 'api.fanduel.com','Connection': 'keep-alive','Accept': 'application/json, text/plain, */*',\
	'X-Auth-Token': token,\
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',\
	'Authorization': 'Basic N2U3ODNmMTE4OTIzYzE2NzVjNWZhYWFmZTYwYTc5ZmM6','Origin': 'https://www.fanduel.com',\
	'Referer': 'https://www.fanduel.com/games','Accept-Encoding': 'gzip, deflate, sdch','Accept-Language': 'en-US,en;q=0.8'}


	db = pymysql.connect("localhost","cbb","","cbb",charset="utf8",cursorclass=pymysql.cursors.DictCursor)
	c = db.cursor()
	c2 = db.cursor()

	c.execute("""SELECT DISTINCT(contestid) cid FROM fanduel_entries WHERE score IS NULL""")

	for v in c.fetchall():
		print 'Getting contest:',v['cid']
		### results
		req = requests.get('https://api.fanduel.com/contests/%s/entries?page=1&page_size=250&user=2558430'%(v['cid']),headers=headers,verify=False)
		contest = json.loads(req.text)
		# print json.dumps(contest,indent=4)

		try:
			if contest['contests'][0]['started'] == False:
				size = contest['contests'][0]['size']['max']
				c2.execute("""UPDATE fanduel_entries SET size=%s WHERE contestid=%s""",\
				 (size,v['cid']))			
			elif contest['contests'][0]['final'] == True:
				lowest_score = contest['contests'][0]['scoring']['lowest_score']
				last_winning_score = contest['contests'][0]['scoring']['last_winning_score']
				highest_score = contest['contests'][0]['scoring']['highest_score']
				last_winning_rank = contest['contests'][0]['scoring']['last_winning_rank']
				size = contest['contests'][0]['entries']['count']
				name = contest['contests'][0]['name']
				entry_fee = contest['contests'][0]['entry_fee']

				c2.execute("""UPDATE fanduel_entries SET last_winning_score=%s,lowest_score=%s,\
				 highest_score=%s,last_winning_rank=%s,size=%s,name=%s,entry_fee=%s WHERE contestid=%s""",\
				 (last_winning_score,lowest_score,highest_score,last_winning_rank,size,name,entry_fee,v['cid']))

				roster_scores = []
				for roster in contest['rosters']:
					roster_scores.append(roster['score'])
				roster_scores = sorted(roster_scores)

				entry_ranks = []
				entry_prizes = []
				entry_ids = []
				for entry in contest['entries']:
					entry_ranks.append(entry['rank'])
					entry_prizes.append(entry['prizes']['total'])
					entry_ids.append(entry['id'])
				entryI = np.argsort(entry_ranks)[::-1]
				for i,ei in enumerate(entryI):
					c2.execute("""UPDATE fanduel_entries SET rank=%s,prize=%s,score=%s WHERE entryid=%s""",\
					 (entry_ranks[ei],entry_prizes[ei],roster_scores[i],entry_ids[ei]))
		except:
			print 'Error for contestid:',v['cid']

		db.commit()
	c2.execute("""DELETE FROM fanduel_entries WHERE entry_fee is null and date(entry_created)< date(NOW())""")
	db.commit()
	
	return


def entered_contest_ids(gameid):
	db = pymysql.connect("localhost","cbb","","cbb",charset="utf8",cursorclass=pymysql.cursors.DictCursor)
	c = db.cursor()
	c.execute("""SELECT DISTINCT(contestid) FROM fanduel_entries WHERE gameid=%s""",(gameid,))
	return [x['contestid'] for x in c.fetchall()]


def load_lineups_ids(gameid,token):
	print 'load lineups'
	headers = {'Host': 'api.fanduel.com','Connection': 'keep-alive','Accept': 'application/json, text/plain, */*',\
	'X-Auth-Token': token,\
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',\
	'Authorization': 'Basic N2U3ODNmMTE4OTIzYzE2NzVjNWZhYWFmZTYwYTc5ZmM6','Origin': 'https://www.fanduel.com',\
	'Referer': 'https://www.fanduel.com/games','Accept-Encoding': 'gzip, deflate, sdch','Accept-Language': 'en-US,en;q=0.8'}


	db = pymysql.connect("localhost","cbb","","cbb",charset="utf8",cursorclass=pymysql.cursors.DictCursor)
	c = db.cursor()

	### current rosters
	req = requests.get('https://api.fanduel.com/users/2558430/rosters?page=1&page_size=250&status=upcoming',headers=headers,verify=False)
	rosters = json.loads(req.text)
	# rosters = json.load(open('rosters.json','rb'))

	grouped_entries = []
	# print json.dumps(rosters,indent=4)
	if not(rosters.has_key('rosters')):
		return 0
	for ge in rosters['rosters']:
		if (gameid in ge["fixture_list"]["_members"]):
			grouped_entries.append(ge['grouped_entries']['_url'])

	# print grouped_entries

	
	### current entry ids

	entry_count = 0
	for group_entry_url in grouped_entries:
		req = requests.get(group_entry_url,headers=headers,verify=False)
		ge_response = json.loads(req.text)
		# ge_response = json.load(open('grouped_entries.json','rb'))
		# print json.dumps(ge_response,indent=4)
		for ge in ge_response['grouped_entries']:
			contest_id = ge['contest']['_members'][0]
			for _id in ge['entries']['ids']:
				c.execute("""INSERT IGNORE INTO fanduel_entries (entryid,gameid,contestid) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE contestid=%s""",(_id,gameid,contest_id,contest_id))
				# print _id
				entry_count += 1
		db.commit()
	return entry_count


def enter_contest(lineup,gameid,contest,token):

	headers = {'Host': 'api.fanduel.com','Connection': 'keep-alive','Accept': 'application/json, text/plain, */*',\
	'X-Auth-Token': token,\
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',\
	'Authorization': 'Basic N2U3ODNmMTE4OTIzYzE2NzVjNWZhYWFmZTYwYTc5ZmM6','Origin': 'https://www.fanduel.com',\
	'Referer': 'https://www.fanduel.com/games','Accept-Encoding': 'gzip, deflate, sdch','Accept-Language': 'en-US,en;q=0.8'}

	entry = {"entries":[{"entry_fee":{"currency":"usd"},"roster":{"lineup":[]}}]}
	fanduel_lineup = [{},{},{},{},{},{},{},{},{}]
	indx = {'F':0,'G':5}

	for player in lineup:
		m = re.search('[0-9][^A-Z]*', player)
		fid = m.group(0)
		pos = player.split(fid)[1]

		##### define entry
		fanduel_lineup[indx[pos]] = {"position":pos,"player":{"id":str(gameid)+'-'+str(fid)}}
		indx[pos] += 1
		# print pid,pos
	entry['entries'][0]['roster']['lineup'] = fanduel_lineup
	
	#### Add new entry
	req = requests.post('https://api.fanduel.com/contests/%s/entries'%(contest),json=entry,headers=headers,verify=False)

	print req.status_code,req.text
	return

def fetch_contests(gameid,token,max_fee=1,contest_type=[r'[50/50]']):
	headers = {'Host': 'api.fanduel.com','Connection': 'keep-alive','Accept': 'application/json, text/plain, */*',\
	'X-Auth-Token': token,\
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',\
	'Authorization': 'Basic N2U3ODNmMTE4OTIzYzE2NzVjNWZhYWFmZTYwYTc5ZmM6','Origin': 'https://www.fanduel.com',\
	'Referer': 'https://www.fanduel.com/games','Accept-Encoding': 'gzip, deflate, sdch','Accept-Language': 'en-US,en;q=0.8'}
	
	req = requests.get('https://api.fanduel.com/contests?fixture_list=%s&include_restricted=true'%str(gameid),headers=headers,verify=False)
	contest_ids = []
	# print 'token',token
	# print req.text
	D = json.loads(req.text)
	for contest in  D['contests']:
		# print json.dumps(contest,indent=4)
		if contest["entry_fee"] <= int(max_fee):
			for ctype in contest_type:
				if re.search(ctype,contest["name"]):
					contest_ids.append(contest["id"])	
					# print ctype,contest["name"],'yes'
				else:
					# print ctype,contest["name"],'no'
					pass

	return contest_ids

def update_fanduel_lineups(gameid,lineups,token):
	headers = {'Host': 'api.fanduel.com','Connection': 'keep-alive','Accept': 'application/json, text/plain, */*',\
	'X-Auth-Token': token,\
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',\
	'Authorization': 'Basic N2U3ODNmMTE4OTIzYzE2NzVjNWZhYWFmZTYwYTc5ZmM6','Origin': 'https://www.fanduel.com',\
	'Referer': 'https://www.fanduel.com/games','Accept-Encoding': 'gzip, deflate, sdch','Accept-Language': 'en-US,en;q=0.8'}


	db = pymysql.connect("localhost","cbb","","cbb",charset="utf8",cursorclass=pymysql.cursors.DictCursor)
	c = db.cursor()
	c.execute("""SELECT entryid,size FROM fanduel_entries fe inner join (SELECT count(*) ecount,contestid from fanduel_entries group by contestid) c on c.contestid=fe.contestid WHERE gameid=%s order by ecount desc,size desc""",(gameid,))

	entries = c.fetchall()
	n_entries = len(entries)
	entries = np.array(entries)

	n_lineups = len(lineups)

	### Shuffle entries within lineup interval

	for k in range(int(1.*n_entries/n_lineups)):
		idx = np.arange(k*n_lineups,(k+1)*n_lineups)
		shuffled_idx = np.arange(k*n_lineups,(k+1)*n_lineups)
		np.random.shuffle(shuffled_idx)
		entries[idx] = entries[shuffled_idx]

	

		
	### define entry
	lineup_i = 0

	for entryid in entries:
		if lineup_i < n_lineups:
			lineup = lineups[lineup_i]
		else:
			lineup_i = 0
			lineup = lineups[lineup_i]
		lineup_i += 1

		entry = {"entries":[{"entry_fee":{"currency":"usd"},"roster":{"lineup":[]}}]}
		fanduel_lineup = [{},{},{},{},{},{},{},{},{}]
		indx = {'F':0,'G':5}

		for player in lineup[1]:
			m = re.search('[0-9][^A-Z]*', player)
			fid = m.group(0)
			pos = player.split(fid)[1]

			##### define entry
			fanduel_lineup[indx[pos]] = {"position":pos,"player":{"id":str(gameid)+'-'+str(fid)}}
			indx[pos] += 1
			# print pid,pos
		entry['entries'][0]['roster']['lineup'] = fanduel_lineup
		#### Put it
		
		req = requests.put('https://api.fanduel.com/entries/%i'%entryid['entryid'],json=entry,headers=headers,verify=False)
		print lineup[0],req.status_code,req.text,entryid['size']
		# print lineup[0],entryid['size']

	return

if __name__ == '__main__':
	update_results(load_token())




