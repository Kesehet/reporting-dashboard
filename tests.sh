curl -X POST -H "Content-Type: application/json" \
  -d '{"count":3,"clear_db":true,"save_result":true,"prefix":"T-"}' \
  http://localhost:5000/quick_insert
  

curl -X POST -H "Content-Type: application/json" \
  -d '{"count":3,"clear_db":true,"save_result":true,"prefix":"T-"}' \
  https://vsdiswebdev01.myfnb.us/api/quick_insert
  

curl -X POST -H "Content-Type: application/json" \
  -d '{"count":3,"clear_db":true,"save_result":true,"prefix":"T-"}' \
  https://vsdiswebqa01.myfnb.us/api/quick_insert
  
  