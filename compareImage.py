import requests
from PIL import Image
import imagehash
from io import BytesIO

response1 = requests.get('https://images.cdn.saveonfoods.com/detail/00030772132296.jpg')
response2 = requests.get('https://media-www.canadiantire.ca/product/living/home-essentials/household-consumables/4992139/charmin-bathroom-tissue-12-48-rolls-strong-54b05660-1d30-4555-a04c-330be239f6be-jpgrendition.jpg?imdensity=1&imwidth=1244&impolicy=gZoom')

hash0 = imagehash.average_hash(Image.open(BytesIO(response1.content)))
hash1 = imagehash.average_hash(Image.open(BytesIO(response2.content)))
cutoff = 5  # maximum bits that could be different between the hashes.

if hash0 - hash1 < cutoff:
  print('images are similar')
else:
  print('images are not similar')