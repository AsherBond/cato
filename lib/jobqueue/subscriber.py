import threading
import multiprocessing
import time
import os
from jobqueue import JobQueue

class Subscriber(JobQueue):

    def __init__(self, db_name, queue_name, host=None,
                port=27017, user=None, password=None, queue_delay=.1,
                poll_delay=.2):
        """Constructs a subscriber.

        Keyword arguments:
        db_name -- MongoDB database name (required)
        queue_name -- the name of a MongoDB collection in which the queue exists
        host -- hostname or ip address of the MongoDB service. Localhost if unspecified
        port -- MongoDB port (default 27017)
        user -- user with r/w permission on MongoDB collection
        password -- password for user
        queue_delay -- a sleep throttle so that multiple subscribers can pull 
                        from queued jobs (default .1 seconds)
        poll_delay -- if nothing is in the queue, number of seconds to sleep
                        before checking again (default .2 seconds)

        """

        JobQueue.__init__(self, "subscriber", db_name, queue_name, host=host,
                port=port, user=user, password=password)
        self.queue_delay = queue_delay
        self.poll_delay = poll_delay
        self.fk_func_map = {}
        self.th_func_map = {}
        self.mul_func_map = {}

    def forked_callback(self, func):
        """Used to register forked callback functions for processing. Can be used
        as a decorator or called by passing the function.

        """
    
        self.fk_func_map[func.__name__] = func

    def threaded_callback(self, func):
        """Used to register threaded callback functions for processing. Can be used
        as a decorator or called by passing the function.

        """
    
        self.th_func_map[func.__name__] = func

    def multiprocess_callback(self, func):
        """Used to register multiprocessing callback functions for processing. Can be used
        as a decorator or called by passing the function.

        """
    
        self.mul_func_map[func.__name__] = func

    def monitor_queue(self):
        """Polls the queue in a perpetual loop."""

        while True:
            job = self.queue.next()
            if job:
                #print("found %s" % (job.job_id))

                job_name = job.payload["job_name"]

                if job_name in self.mul_func_map:

                    t = self.mul_func_map[job_name]
                    p = multiprocessing.Process(target=t,args=(job,))
                    p.daemon = True
                    p.start()

                elif job_name in self.th_func_map:

                    t = self.th_func_map[job_name]
                    # create a thread to process the job
                    p = threading.Thread(target=t,args=(job,))
                    p.daemon = True
                    # start the thread, going into the worker function
                    p.start()

                elif job_name in self.fk_func_map:
                    t = self.fk_func_map[job_name]
                    if not os.fork():
                        os.setsid()
                        t(job)
                        exit()
                else:
                    # jobs in this queue that are unknown are presently being skipped
                    # however they could probably get moved to a 'dead letter' queue
                    # for closer examination
                    print("unknown job name %s, skipping" % (job_name))


                # throttle so that other worker subscribers get a chance 
                time.sleep(self.queue_delay)
            else:
                time.sleep(self.poll_delay)

                # prints the number of threads
                # print len(threading.enumerate())

