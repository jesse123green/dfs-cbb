import json,sys

D = json.load(open('contests.json','rb'))
for contest in  D['contests']:
	if contest["entry_fee"] < 5 and ("FIFTY_FIFTY" in contest["type"]["_members"]):
		print json.dumps(contest,indent=4)
	# sys.exit()