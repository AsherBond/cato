# Cato jobqueue library

## Sample publisher to the queue

The following code 

```
from jobqueue.publisher import Publisher

p = Publisher("test", "job_queue", host="127.0.0.1")
p.connect()

data = {"task_instance" : "43782", "yyy" : "222"}
p.submit_job("job_1", data)
p.submit_job("job_2", data)
p.submit_job("run_task", data)
```


## Sample subscriber to the job queue

```
from jobqueue.subscriber import Subscriber
import time
import os

s = Subscriber("test", "job_queue", host="127.0.0.1")
s.connect()

@s.threaded_callback
def job_1(job):

    # this for loop simulates a process that runs for
    # 36 seconds, all the while updating a progress
    # indicator along the way
    print job.payload["job_name"]
    print("threaded process pid is %s" % (os.getpid()))
    for i in range(6):
        job.progress(i*10)
        time.sleep(6)
    job.complete()



@s.multiprocess_callback
def job_2(job):

    # this for loop simulates a process that runs for
    # 18 seconds, all the while updating a progress
    # indicator along the way
    print job.payload["job_name"]
    print("multi process pid is %s" % (os.getpid()))
    for i in range(3):
        job.progress(i*10)
        time.sleep(6)
    job.complete()

@s.forked_callback
def run_task(job):


    task_instance = job.payload["data"]["task_instance"]
    print("%s" % (task_instance))
    import sys
    sys.path.insert(0, "/Users/pdunnigan/cato_dev/cato/lib")
    from catotaskengine import catotaskengine

    ce = catotaskengine.TaskEngine("cato_task_engine", task_instance)
    print("forked process pid is %s" % (os.getpid()))
    ce.startup()
    ce.run()
    job.complete()

print("parent process pid is %s" % (os.getpid()))
s.monitor_queue()
```
