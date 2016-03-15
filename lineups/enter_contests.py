from lineups_optimizer import lineupOptimizer
from import_export.fanduel_utils import enter_contest,fetch_contests,load_lineups_ids,entered_contest_ids,update_results,load_token
import time,gc,sys



def contest_loop(gameid,platform,max_fee=2,max_entries=50,token=''):
	max_entries = int(max_entries)

	opt = lineupOptimizer(excluded_players=[],excluded_teams=[],platform=platform)
	opt.get_players(gameid)

	opt.update_counts()
	if platform == 'fanduel':
		lineup = opt.choose_lineup()


	n_entries = load_lineups_ids(gameid,token)
	print 'Entered %i contests.'%n_entries
	update_results(token)
	while n_entries < max_entries:
		entered_ids = entered_contest_ids(gameid)
		contest_ids = fetch_contests(gameid,token,max_fee=max_fee,contest_type=[r'50/50',r'CBB Double Up'])
		entry_attempts = 0
		for _id in contest_ids:
			print _id
			if _id not in entered_ids:
				print 'ENTERING NEW CONTEST',_id
				enter_contest(lineup,gameid,_id,token)
				entry_attempts += 1
				if (n_entries + entry_attempts) >= max_entries:
					break
			else:
				# print 'OLD CONTEST',_id
				pass

		n_entries = load_lineups_ids(gameid,token)
		update_results(token)
		print 'Entered %i total contests.'%n_entries
		if n_entries < max_entries:
			time.sleep(600)



if __name__ == "__main__":

	print sys.argv[1]
	try:
		gameid = sys.argv[1]
	except:
		gameid = 13273

	try:
		platform = sys.argv[2]
	except:
		platform = 'fanduel'

	try:
		max_fee = sys.argv[3]
	except:
		max_fee = 2

	try:
		max_entries = sys.argv[4]
	except:
		max_entries = 30


	contest_loop(gameid,platform,max_fee=max_fee,max_entries=max_entries,token=load_token())