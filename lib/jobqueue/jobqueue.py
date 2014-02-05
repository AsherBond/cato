from pymongo import MongoClient
from mongoqueue import MongoQueue
import uuid

class JobQueue():

    def __init__(self, type, db_name, queue_name, host=None, 
                port=27017, user=None, password=None):

        self.db_name = db_name
        self.host = host
        self.port = port
        self.user = user
        self.password = password

        conn_name = type + "-" + str(uuid.uuid4())

        db = self.connect()

        self.queue = MongoQueue(db[queue_name], timeout=300,
                            consumer_id=conn_name, max_attempts=3)

    def connect(self):
        """
        Connects to mongodb and optionally authenticates.

        If user is set to None, no authentication is performed.

        :return: instance of mongodb Database
        """
        try:

            c = MongoClient(host=self.host, port=self.port)
            db = c[self.db_name]

            if self.user:
                db.authenticate(self.user, self.password)
        except Exception as e:
            raise Exception("Couldn't create a Mongo connection to database [%s]" % self.db_name, e)
        return db
        
        

