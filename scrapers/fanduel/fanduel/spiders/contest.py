# -*- coding: utf-8 -*-
import scrapy,re,sys,json, urllib2
from fanduel.items import FanduelItem

class ContestSpider(scrapy.Spider):
	name = "contest"
	def __init__(self, gameid=None):
		self.allowed_domains = ["fanduel.com"]
		# self.start_urls = ["https://www.fanduel.com/e/Game/%s"%gameid]
		self.start_urls = ["https://www.fanduel.com/games/%s/contests/create?stakelist=1x1&isPublic=true"%gameid]

	def parse(self, response):

		item = FanduelItem()
		url = response.url

		for sel in response.xpath("//input[@name='game_id']"):
			item['gameid'] = sel.xpath("@value").extract()[0]

		for sel in response.xpath("//tr[@data-role='player']"):
			print '* '*50
			for d in sel.xpath('.//td[@class="player-name"]'):
				item['name'] = d.xpath('div/text()').extract()[0]
				indicator = d.xpath('div/span/text()').extract()
				if len(indicator) > 0:
					item['indicator'] = indicator[0]
				else:
					item['indicator'] = ''

			for d in sel.xpath('.//td[@class="player-add"]'):
				item['fid'] = d.xpath('a/@data-player-id').extract()[0]

			for d in sel.xpath('.//td[@class="player-fppg"]'):
				item['fppg'] = d.xpath('text()').extract()[0]
			for d in sel.xpath('.//td[@class="player-fixture"]'):
				opp = d.xpath('text()').extract()[0]
				if re.match('@',opp):
					item['home'] = 0
				else:
					item['home'] = 1
				item['opp'] = opp.replace('@','')
				item['team'] = d.xpath('b/text()').extract()[0].replace('@','')
			for d in sel.xpath('.//td[@class="player-salary"]'):
				item['salary'] = d.xpath('text()').extract()[0].replace('$','').replace(',','')
			for d in sel.xpath('.//td[@class="player-position"]'):
				item['position'] = d.xpath('text()').extract()[0]

			yield item
