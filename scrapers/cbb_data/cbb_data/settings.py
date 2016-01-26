# -*- coding: utf-8 -*-

# Scrapy settings for cbb_data project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'cbb_data'

SPIDER_MODULES = ['cbb_data.spiders']
NEWSPIDER_MODULE = 'cbb_data.spiders'


ITEM_PIPELINES = [
    'cbb_data.pipelines.CbbDataPipeline',
]

DOWNLOAD_HANDLERS = {'s3': None,}
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'cbb_data (+http://www.yourdomain.com)'
