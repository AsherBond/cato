from jobqueue import JobQueue

class Publisher(JobQueue):

    def __init__(self, db_name, queue_name, host=None,
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

        JobQueue.__init__(self, "publisher", db_name, queue_name, host=host,
                port=port, user=user, password=password)

    def submit_job(self, job_name, data=None):
        """Submits a job to a work queue"""

        job_data = {"job_name" : job_name, "data" : data} 
        self.queue.put(job_data)
    
