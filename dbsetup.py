import pymongo
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://nghednh:123@cluster0.llhn1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['movie_db']
collection = db['movies']

def create_indexes():
    try:
        indexes = list(collection.list_indexes())
        for index in indexes:
            if index.get("name") == "name_text":
                collection.drop_index("name_text")
        for index in indexes:
            if index.get("name") == "overview_text":
                collection.drop_index("overview_text")
        collection.create_index([("name", pymongo.TEXT), ("overview", pymongo.TEXT)])

        collection.create_index([("movie_id", pymongo.ASCENDING)])

        print("Indexes created successfully!")
    except Exception as e:
        print(f"Error creating indexes: {e}")
create_indexes()
indexes = collection.list_indexes()
for index in indexes:
    print(index)
