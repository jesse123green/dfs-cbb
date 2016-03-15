import urllib2, json, sys, re
import pymysql
import datetime
import pylab as plt
import numpy as np

dbc = json.load(open('../credentials/db.json','rb'))
live = dbc[dbc['live']]
db = pymysql.connect(live['host'],live['user'],live['pw'],live['db'],charset="utf8",cursorclass=pymysql.cursors.DictCursor)

c = db.cursor()

# c.execute("""SELECT fppg,pfp from fanduel_contests where pfp > 0 limit 5000""")

c.execute("""SELECT ROUND(pfp) pfp,median(fp) fp,count(*) cnt FROM
	(SELECT fppg,pfp,(pts+reb*1.2+ast*1.5+blk*2+stl*2-tov) fp,gamelog.pid,entry_created from 
fanduel_contests fc inner join (select gameid,entry_created from fanduel_entries group by gameid) fe on fe.gameid=fc.gameid 
inner join players on players.fid=fc.fid 
inner join gamelog on date(entry_created) = date(gametime) and gamelog.pid=players.pid 
where pfp > 0 and (pts+reb*1.2+ast*1.5+blk*2+stl*2-tov) > 0) x group by ROUND(pfp)""")

# c.execute("""SELECT fppg,pfp,(pts+reb*1.2+ast*1.5+blk*2+stl*2-tov) fp,gamelog.pid,entry_created,gameday from 
# fanduel_contests fc inner join (select gameid,entry_created from fanduel_entries group by gameid) fe on fe.gameid=fc.gameid 
# inner join players on players.fid=fc.fid 
# inner join gamelog on date(entry_created) = gameday and gamelog.pid=players.pid 
# where pfp > 0 and (pts+reb*1.2+ast*1.5+blk*2+stl*2-tov) > 0 and gameday > '2016-02-04'""")

r = c.fetchall()
n = len(r)

plt.plot(np.arange(61),np.arange(61),linewidth=3)

fp = []
for v in r:
	# print r
	# print r['fppg']
	print v['pfp'],v['fp'],v['cnt']
	# plt.plot(v['pfp'],v['fp'],'o',markersize=1*np.sqrt(v['cnt']))
	plt.plot(v['pfp'],v['fp'],'o')

plt.ylabel('Fantasy Points')
plt.xlabel('Projected Fantasy Points')
plt.xlim((0,60))
plt.show()
