import pymongo
from gridfs import GridFS

url = 'mongodb://localhost:27017'
client = pymongo.MongoClient(url)

db = client['aICounseling']

fs = GridFS(db,collection = 'files')

