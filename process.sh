#!/bin/bash

GAMEID="14984"

# echo --- getting new games ---
# cd scrapers/allgames
# scrapy crawl allgames
# cd ../..

# echo --- getting game data ---
# cd scrapers/cbb_data
# scrapy crawl cbbdata
# cd ../..

# echo --- get rankings ---
# cd scrapers/rankings
# scrapy crawl rankings
# cd ../..

# echo --- getting fanduel data ---
# cd lineups
# python fanduel_players.py "$GAMEID"
# cd ..

# echo --- housekeeping ---
# cd housekeeping
# python player_sync.py "$GAMEID"
# cd ..

# echo --- housekeeping ---
# cd housekeeping
# python team_sync.py "$GAMEID"
# cd ..

# echo --- predict ---
# cd lineups
# python predict_players.py "$GAMEID" "fanduel"
# cd ..

echo --- lineups ---
cd lineups
python lineups_optimizer.py "$GAMEID" "fanduel"
cd ..
