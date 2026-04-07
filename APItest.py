import requests

# AMAZON
# URL = "http://api.axesso.de/amz/amazon-search-by-keyword-asin"
#
# headers = {
#     "axesso-api-key": "4ee06f3120b4424d858a295b5cb8fcf2",
#     "Cache-Control": "no-cache",
# }
#
# params = {
#     "domainCode": "ca",
#     "keyword": "toilet paper",
#     "page": 1,
# }
#
# response = requests.get(URL, params=params, headers=headers)
#
# print(response.text)

######################################################################

# URL = "http://api.axesso.de/wlm-ca/walmart-search-by-keyword"
#
# headers = {
#     "axesso-api-key": "976222a91a3d485faad5b4c2d8155b53",
#     "Cache-Control": "no-cache",
# }
#
# params = {
#     "domainCode": "ca",
#     "keyword": "toilet paper",
#     "page": 1,
# }
#
# response = requests.get(URL, params=params, headers=headers)


# WALMART API
# params = {
#   "api_key": "C2539FFD577943BE8C404CB3B1E59A42",
#   "type": "search",
#   "search_term": "toilet paper",
#   "walmart_domain":"walmart.ca"
# }
#
# api_result = requests.get('https://api.bluecartapi.com/request', params)
# print(api_result.json())

# COSTCO API
# url = "https://real-time-costco-data.p.rapidapi.com/search"
#
# querystring = {"query":"Toilet Paper","country":"CA","language":"en-CA","start":"0"}
#
# headers = {
# 	"x-rapidapi-key": "0f68519fcamsh2de7950fd615ce9p120591jsn97b9056c49c8",
# 	"x-rapidapi-host": "real-time-costco-data.p.rapidapi.com",
# 	"Content-Type": "application/json"
# }
#
# response = requests.get(url, headers=headers, params=querystring)
#
# print(response.json())