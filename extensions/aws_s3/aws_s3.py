#########################################################################
# Copyright 2011 Cloud Sidekick
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#########################################################################

from catotaskengine import classes
try:
    import boto
    from boto.s3.key import Key
    from boto.s3.acl import CannedACLStrings
    import boto.exception
except ImportError as e:
    msg = "The AWS S3 require the Boto python library."
    raise Exception(msg)
except Exception as e:
    raise Exception(e)

def create_bucket(c, name):

    b = c.create_bucket(name)
    return b


def copy_file(c, from_file, from_bucket, to_file=None, to_bucket=None, storage="STANDARD", canned_acl=None):

    create = True
    if canned_acl and canned_acl not in CannedACLStrings:
        raise Exception("%s is not one of the canned S3 ACL strings" % (canned_acl))
    if storage not in ["STANDARD", "REDUCED_REDUNDANCY"]:
        raise Exception("%s is not a valid S3 storage class" % (storage))

    if not to_file:
        # use the same name as the from_file
        to_file = from_file
    if not to_bucket:
        # copy to the same bucket
        to_bucket = from_bucket

    try:
        b = c.get_bucket(to_bucket)
    except Exception as e:
        if e.error_code == "NoSuchBucket" and create is True:
            b = create_bucket(c, to_bucket)
        elif e.error_code == "AccessDenied":
            raise Exception("Access Denied attempting to connect to S3, check access key and secret key credentials")
        else:
            raise Exception(e)
    try:
        k = b.copy_key(to_file, from_bucket, from_file, storage_class=storage)
    except Exception as e:
        if e.error_code == "NoSuchBucket":
            raise Exception("From bucket %s does not exist" % (from_bucket))
        elif e.error_code == "NoSuchKey":
            raise Exception("From file named %s does not exist in bucket %s" % (from_file, from_bucket))
        else:
            raise Exception(e)
    if canned_acl:
        if canned_acl not in CannedACLStrings:
            raise Exception("%s is not one of the canned ACL strings" % (canned_acl))
        k.set_canned_acl(canned_acl)

def aws_s3_connect(TE):

    cloud_name = "us-east-1"
    try:
        cloud = TE.cloud_conns[cloud_name]
    except KeyError as ex:
        cloud = classes.Cloud(cloud_name)
        TE.cloud_conns[cloud_name] = cloud

    if not cloud.conn:
        cloud.conn = boto.connect_s3(TE.cloud_login_id, TE.cloud_login_password)

    return cloud


def s3_copy_file(te, step):

    from_file, from_bucket, to_file, to_bucket, storage, acl = te.get_command_params(step.command, "from_file", "from_bucket",
        "to_file", "to_bucket", "storage", "acl")[:]
    from_file = te.replace_variables(from_file)
    from_bucket = te.replace_variables(from_bucket)
    to_file = te.replace_variables(to_file)
    to_bucket = te.replace_variables(to_bucket)
    cloud = aws_s3_connect(te)

    if not len(from_file): 
        raise Exception("S3 Copy File error: From File cannot be blank")
    if not len(from_bucket): 
        raise Exception("S3 Copy File error: From Bucket cannot be blank")
    if not len(acl):
        acl = None
    if not len(to_file): 
        to_file = from_file
    if not len(to_bucket): 
        to_bucket = from_bucket
    if not len(storage): 
        storage = "STANDARD"

    copy_file(cloud.conn, from_file, from_bucket, to_file, to_bucket, storage, acl)


    msg = "AWS S3 file %s copied from bucket %s to bucket %s to filename %s" % (from_file, from_bucket, to_bucket, to_file)
    te.insert_audit(step.function_name, msg, "")
