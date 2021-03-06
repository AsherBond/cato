
# Copyright 2012 Cloud Sidekick
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:# www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Datastore endpoint methods.
"""

import json


from catolog import catolog
logger = catolog.get_logger(__name__)

from catoapi import api
from catoapi.api import response as R
from catodatastore import datastore
from catocommon import catocommon


class dsMethods:
    """Cato Datastore"""

    def list_documents(self, args):
        """Lists all Datastore Documents.

Optional Arguments:

* `collection` - a document collection.  'Default' if omitted.
* `filter` - will filter a value match in the Document ID or data.  (Filter is a JSON object formatted as a Mongo query.)

Returns: A list of [Datastore Document Objects](restapi/api-response-objects.html#DatastoreDocument){:target="_blank"}.
"""
        collection = args["collection"] if "collection" in args else ""
        try:
            fltr = json.loads(args["filter"]) if "filter" in args else {}
        except ValueError as ex:
            raise Exception("Filter must be a valid datastore query in JSON format.\n%s" % (ex.__str__()))    
        obj = datastore.Documents(collection, fltr)
        if args.get("output_format") == "json" or args.get("output_format") == "text":
            return R(response=obj.AsJSON())
        else:
            return R(response=obj.AsXML())

    def list_document_collections(self, args):
        """Lists all Datastore Document Collections.

Optional Arguments:

* `filter` - will filter results on the Collection name.  (A string to match in the Collection name.)

Returns: A list of Document Collections.
"""
        fltr = args["filter"] if "filter" in args else ""

        obj = datastore.Collections(fltr)
        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())

    def create_document(self, args):
        """Creates a Datastore document.

Optional Arguments:

* `collection` - a document collection.  'Default' if omitted.
* `template` - A JSON document template.  A blank document will be created if omitted.

Returns: A [Datastore Document Object](restapi/api-response-objects.html#DatastoreDocument){:target="_blank"}.
"""
        collection = args["collection"] if "collection" in args else ""
        template = args["template"] if "template" in args else ""

        doc, msg = datastore.create_document(template, collection)
        if doc:
            if args.get("output_format") == "json":
                return R(response=doc.AsJSON())
            elif args.get("output_format") == "text":
                return R(response=doc.AsText())
            else:
                return R(response=doc.AsXML())
        else:
            return R(err_code=R.Codes.GetError, err_detail=msg)

    def get_document(self, args):
        """Gets a Datastore document.

Required Arguments:

* `query` - A query in JSON format to select the correct Document.

Optional Arguments:

* `collection` - a document collection.  'Default' if omitted.

Returns: A [Datastore Document Object](restapi/api-response-objects.html#DatastoreDocument){:target="_blank"}.
"""
        # define the required parameters for this call
        required_params = ["query"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        collection = args["collection"] if "collection" in args else ""
        query = json.loads(args["query"])
        doc = datastore.Document(query, collection)

        if doc.ID:
            if args.get("output_format") == "json":
                return R(response=doc.AsJSON())
            elif args.get("output_format") == "text":
                return R(response=doc.AsText())
            else:
                return R(response=doc.AsXML())
        else:
            return R(err_code=R.Codes.GetError, err_detail="Unable to find Data Document using query %s." % args["query"])

    def get_document_value(self, args):
        """Gets the value of a key in a Datastore document.

> Datastore queries always return a list of document matches, even if the result set happens to only return data from one document.

Required Arguments:

* `query` - A query in JSON format to select the correct Document.
* `lookupkey` - The section of the Document to retrieve.  Returns the entire document if omitted.

Optional Arguments:

* `collection` - a document collection.  'Default' if omitted.

Returns: A text value.
"""
        # define the required parameters for this call
        required_params = ["query", "lookupkey"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        collection = args["collection"] if "collection" in args else ""
        query = json.loads(args["query"])
        doc = datastore.Document(query, collection)
        if doc.ID:
            # we have a document!  let's dig in to it.
            result = doc.Lookup(args["lookupkey"])
            if result:
                return R(response=catocommon.ObjectOutput.IterableAsJSON(result))
#                    # now, the section we obtained might be a document itself...
#                    # so let's serialize it.
#                    if args.get("output_format") == "json":
#                        return R(response=doc.AsJSON())
#                    elif args.get("output_format") == "text":
#                        return R(response=doc.AsText())
#                    else:
#                        return R(response=doc.AsXML())
            else:
                return R(response="Lookup found no match.")

        else:
            return R(err_code=R.Codes.GetError, err_detail="Unable to find Document for Object ID [%s]." % args["doc_id"])

    def set_document_value(self, args):
        """Sets the value of a key in a Datastore document.

Required Arguments:

* `query` - A query in JSON format to select the correct Document.
* `lookupkey` - The section of the document to retrieve.

Optional Arguments:

* `collection` - a document collection.  'Default' if omitted.
* `value` - The value to set this item.  Item will be cleared if omitted.

Returns: A success message, or error messages on failure.
"""
        # define the required parameters for this call
        required_params = ["query", "lookupkey"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        collection = args["collection"] if "collection" in args else ""
        value = args["value"] if "value" in args else ""
        query = json.loads(args["query"])
        doc = datastore.Document(query, collection)
        if doc.ID:
            # we have a document!  let's dig in to it.
            result = doc.Set(args["lookupkey"], value)
            if result:
                return R(response="Value successfully set.")
            else:
                return R(err_code=R.Codes.CreateError, err_detail="Value was not set, see logfile for details.")

        else:
            return R(err_code=R.Codes.GetError, err_detail="Unable to find Document using query [%s]." % args["query"])

    def set_document_values(self, args):
        """Sets multiple values in a Datastore document.

Required Arguments:

* `query` - A query in JSON format to select the correct Document.
* `updatedoc` - A document representing path:value pairs to be updated.

Optional Arguments:

* `collection` - a document collection.  'Default' if omitted.

Multiple keys are updated in a looping manner.  Unsuccessful updates will return an error,
but will not stop subsequent updates from occuring.

Returns: A success message, or error messages on failure.
"""
        # define the required parameters for this call
        required_params = ["query", "updatedoc"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        collection = args["collection"] if "collection" in args else ""
        query = json.loads(args["query"])
        updatedoc = json.loads(args["updatedoc"])
        targetdoc = datastore.Document(query, collection)
        if targetdoc.ID:
            # loop each key in the updatedoc, and call doc.Set
            # collect all errors into a single response, key:error format
            
            failed = []
            for path, value in updatedoc.iteritems():
                result = targetdoc.Set(path, value)
                if not result:
                    failed.append(path)
            if not failed:
                return R(response="All values successfully set.")
            else:
                return R(err_code=R.Codes.UpdateError, err_detail="Failed to update the following keys: %s" % (catocommon.ObjectOutput.AsJSON(failed)))

        else:
            return R(err_code=R.Codes.GetError, err_detail="Unable to find Document using query [%s]." % query)
