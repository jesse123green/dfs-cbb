select ctype,entry_fee,sum(entry_fee),sum(prize),sum(prize)-sum(entry_fee),sum(prize)/sum(entry_fee) from 
((select size,entry_fee,prize,'double up' ctype from fanduel_entries where name like "%double up%")
UNION ALL
(select size,entry_fee,prize,'fiftyfifty' ctype from fanduel_entries where name like "%50/50%")
UNION ALL
(select size,entry_fee,prize,'h2h' ctype from fanduel_entries where size=2)
UNION ALL
(select size,entry_fee,prize,'gpp' ctype from fanduel_entries where size!=2 and name not like "%50/50%" and name not like "%double up%")) x
group by entry_fee,ctype order by sum(prize)/sum(entry_fee) desc