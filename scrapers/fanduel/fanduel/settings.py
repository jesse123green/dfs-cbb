# -*- coding: utf-8 -*-

# Scrapy settings for fanduel project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'fanduel'

SPIDER_MODULES = ['fanduel.spiders']
NEWSPIDER_MODULE = 'fanduel.spiders'

ITEM_PIPELINES = [
    'fanduel.pipelines.FanduelPipeline',
]

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'fanduel (+http://www.yourdomain.com)'
