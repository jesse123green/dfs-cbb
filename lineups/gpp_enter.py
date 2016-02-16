from lineups_optimizer import lineupOptimizer
from import_export.fanduel_utils import enter_contest,fetch_contests,load_lineups_ids,entered_contest_ids,update_results,load_token
import time,gc,sys



def submit_multiple_entries(gameid,contestid,num_entries,token):

	opt = lineupOptimizer(excluded_players=[],excluded_teams=[],platform=platform)
	opt.get_players(gameid)

	opt.update_counts()
	if platform == 'fanduel':
		lineup = opt.choose_lineup()	
	for _ in range(num_entries):
		enter_contest(lineup,gameid,contestid,token)

	return

if __name__ == "__main__":

	print sys.argv[1]
	try:
		gameid = sys.argv[1]
	except:
		gameid = None

	try:
		contestid = sys.argv[2]
	except:
		contestid = 1

	try:
		num_entries = int(sys.argv[3])
	except:
		num_entries = 1

	try:
		platform = sys.argv[4]
	except:
		platform = 'fanduel'



	submit_multiple_entries(gameid,contestid,num_entries,token=load_token())


