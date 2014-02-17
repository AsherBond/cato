from jobqueue import JobQueue

class Publisher(JobQueue):

    def __init__(self, db_name=None, queue_name=None, host=None,
                port=27017, user=None, password=None):
        """Constructs a publisher.

        Keyword arguments:
        db_name -- MongoDB database name (required)
        queue_name -- the name of a MongoDB collection in which the queue exists
        host -- hostname or ip address of the MongoDB service. Localhost if unspecified
        port -- MongoDB port (default 27017)
        user -- user with r/w permission on MongoDB collection
        password -- password for user

        """

        self.db_name = db_name
        self.queue_name = queue_name
        self.host = host
        self.port = port
        self.user = user
        self.password = password

        JobQueue.__init__(self, "publisher", self.db_name, self.queue_name, host=self.host,
                port=self.port, user=self.user, password=self.password)

    def submit_job(self, job_name, data=None):
        """Submits a job to a work queue"""

        job_data = {"job_name" : job_name, "data" : data} 
        self.queue.put(job_data)
    
