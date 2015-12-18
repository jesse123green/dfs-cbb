#!/bin/bash

GAMEID="14041"

echo --- getting new games ---
cd scrapers/cbb_games
scrapy crawl cbbgames
cd ../..

# echo --- getting game data ---
# cd scrapers/cbb_data
# scrapy crawl cbbdata
# cd ../..

# echo --- get rankings ---
# cd scrapers/rankings
# scrapy crawl rankings
# cd ../..

# echo --- getting fanduel data ---
# cd scrapers/fanduel
# scrapy crawl contest -a gameid="$GAMEID"
# cd ../..

# echo --- housekeeping ---
# cd housekeeping
# python player_sync.py
# cd ..

# echo --- predict ---
# cd lineups
# python predict_players.py "$GAMEID" "fanduel"
# cd ..

# echo --- lineups ---
# cd lineups
# python lineups_optimizer.py "$GAMEID" "fanduel"
# cd ..
