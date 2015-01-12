echo --- getting new games ---
cd cbb_games
scrapy crawl cbbgames
cd ..
echo --- getting game data ---
cd cbb_data
scrapy crawl cbbdata
cd ..
echo --- get rankings ---
cd rankings
scrapy crawl rankings
cd ..
# echo --- predicting fanduel ---
# cd fanduel
# scrapy crawl fanduel
# cd ..
