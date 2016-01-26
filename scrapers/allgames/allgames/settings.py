# -*- coding: utf-8 -*-

# Scrapy settings for allgames project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'allgames'

SPIDER_MODULES = ['allgames.spiders']
NEWSPIDER_MODULE = 'allgames.spiders'

ITEM_PIPELINES = [
    'allgames.pipelines.AllgamesPipeline',
]

DOWNLOAD_HANDLERS = {'s3': None,}
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'allgames (+http://www.yourdomain.com)'
