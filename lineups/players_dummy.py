import urllib2, json, sys, re, time, pickle, pymysql
from datetime import datetime,date,timedelta
import numpy as np

class CBB():

	def __init__(self,pid,pos,team,opp,home,salary,name,season,fid=None):
		self.X = []
		self.is_valid = True
		self.pid = pid
		self.fid=fid
		self.pos = pos
		self.team = team
		self.opp = opp
		self.season = int(season)
		self.home = home
		self.salary = salary
		self.name = name
		self.fantasy_prediction = 0.
		self.gamesPlayed = 0

if __name__ == "__main__":

	pass
