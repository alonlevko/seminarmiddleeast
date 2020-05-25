from cloudant.client import Cloudant
from requests import adapters
from cloudant.query import Query, QueryResult
from cloudant.error import CloudantException

serviceUsername = "7128478b-2062-4009-9051-186404f4ac8b-bluemix"
servicePassword = "786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd"
serviceURL = "https://7128478b-2062-4009-9051-186404f4ac8b-bluemix:786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd@7128478b-2062-4009-9051-186404f4ac8b-bluemix.cloudantnosqldb.appdomain.cloud"
httpAdapter = adapters.HTTPAdapter(pool_connections=15, pool_maxsize=100)
client = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=httpAdapter)

client.connect()
client.create_database("test_db")
db = client.get("test_db", remote=True)
db.create_document({
    "data": "My Name is Alon"
})
db.create_document({
    "data": "My Name is Shahar"
})
db.create_document({
    "data": "My Name is Fuji"
})
query_result = QueryResult(Query(db, selector={"$or": [{"$text": "Fuji"}, {"$text": "Shahar"}]}))
for doc in query_result:
    print(doc)