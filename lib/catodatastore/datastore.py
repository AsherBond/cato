#########################################################################
#
# Copyright 2013 Cloud Sidekick
# __________________
#
#  All Rights Reserved.
#
# NOTICE:  All information contained herein is, and remains
# the property of Cloud Sidekick and its suppliers,
# if any.  The intellectual and technical concepts contained
# herein are proprietary to Cloud Sidekick
# and its suppliers and may be covered by U.S. and Foreign Patents,
# patents in process, and are protected by trade secret or copyright law.
# Dissemination of this information or reproduction of this material
# is strictly forbidden unless prior written permission is obtained
# from Cloud Sidekick.
#
#########################################################################

import catomongo
from time import sleep

from catolog import catolog
logger = catolog.get_logger(__name__)

import json
from catocommon import catocommon
from catomongo import Connection, extract_fragment_from_doc, modify_doc, \
    update_doc, query_doc, delete_doc, unset_doc
from catoerrors import DatastoreError, DocumentNotFoundError


def find_document(_id=None, query={}, collection="default"):
    if _id:
        query['_id'] = _id
    if "_id" in query:
        _id = query["_id"]
        from bson.objectid import ObjectId
        query["_id"] = ObjectId(query["_id"])
    if not collection:
        collection = "default"

    try:
        # connection should be later cleaned up:
        db = catocommon.new_mongo_conn()
        coll = db[collection]
        doc = coll.find_one(query)
        if doc:
            rdoc = Document()

            # convert from ObjectId
            rdoc.ID = str(doc['_id'])
            rdoc._collection_obj = coll
            rdoc.doc = doc
        else:
            raise DocumentNotFoundError('Document with id %s not found' % id)
    except Exception as ex:
        raise DatastoreError(ex)
    finally:
        # TODO: cleanup
        #db.close()
        pass

    return rdoc


def create_document(template, collection="default"):
    """
    Creates a new Document based on the given the parameters.


    :type template: dict
    :param template: any JSON document
    :type template: string
    :param collection: collection name to use for creating the document.

    :rtype: Document
    Note: there is no enforcement of cato_object_id being unique.  This is by design, as
    some documents may have the same cato_object_id and their uniqueness would be defined
    by additional arguments.

    raises DatastoreError
    """
    if not collection:
        collection = "default"

    jsondoc = {}
    if template:
        # verify the template is a valid document
        try:
            jsondoc = json.loads(template)
        except ValueError:
            return None, "Template is not a valid JSON document."
        except TypeError:
            # NOTE: we're expecting template to be a JSON STRING
            # but it's possible it could also be a python dict in which case
            # a TypeError will occur.
            jsondoc = template

    db = catocommon.new_mongo_conn()
    coll = db[collection]
    docid = coll.insert(jsondoc)
    catocommon.mongo_disconnect(db)
    # needed to add a incremental backoff retry loop because of mongo's eventual consistancy
    ii = 1
    while True:
        doc = Document({'_id': docid}, collection)
        if doc.ID:
            break
        elif ii == 5:
            break
        else:
            del(doc)
            sleep(ii * .1)

    if doc.ID:
        return doc, None
    else:
        return None, "Document was not created or could not be found by _id=%s." % docid


class Document(object):
    def __init__(self, query={}, collection="default", projection=None):

        self.ID = None
        self.collection = collection
        self._collection_obj = None

        # support empty query temporarily for find_document
        if not query:
            return

        # if the query includes _id, cast it to an ObjectId not a string.
        if "_id" in query:
            from bson.objectid import ObjectId
            query["_id"] = ObjectId(query["_id"])
        if not collection:
            collection = "default"

        self.doc = None

        try:
            # connection should be later cleaned up:
            db = catocommon.new_mongo_conn()
            coll = db[collection]
            self._collection_obj = coll
            doc = coll.find_one(query, projection)
            if doc is not None:
                # convert from ObjectId
                self.ID = str(doc['_id'])
                self.doc = doc
            else:
                logger.critical("Unable to find Datastore document using query %s." % query)
                self.doc = {}
        except Exception as ex:
            raise DatastoreError(ex)
        finally:
            # TODO: cleanup
            #db.close()
            pass

    def AsJSON(self):
        """ Returns a json python representation of Document, which
        is a dict

        :rtype: string
        :return : JSON dict
        """
        if self.doc:
            self.doc['_id'] = '%s' % self.ID
            return catocommon.ObjectOutput.AsJSON(self.doc)
        else:
            return "{}"

    def AsXML(self):
        """ Returns an XML representation of the document.

        :rtype: string
        :return : XML representation of the document
        """
        if self.doc:
            try:
                xml = catocommon.dict2xml(self.doc, "Document")
                return xml.tostring()
            except Exception as ex:
                raise ex

    def AsText(self):
        """ Returns a JSON text representation of Document.

        This is a representation which can be read back as valid JSON, e.g.
        using json.loads function.

        :rtype: string
        :return : JSON text representation
        """
        self.doc['_id'] = '%s' % self.doc['_id']
        return '%s' % json.dumps(self.doc, default=catocommon.jsonSerializeHandler)

    def Delete(self):
        """
        Deletes an object document.

        :return : bool
        """
        return delete_doc(self)

    def Lookup(self, key):
        """
        Looks up a subdocument or value from the object document.

        :return : fragment of document, as dict.
        """
        return extract_fragment_from_doc(self.doc, key)

    def Set(self, key, value):
        """
        Sets the value of an existing key.

        Creates the parent key(s) and document if necessary.

        Example usage:
        >>> document.Set("imagemap.us-east-1.image", "123456")
        >>> # will result in a document that may look like this:
        >>> logger.debug(document.AsJSON())
        {u'guid': u'abcd12345', u'_id': ObjectId('507465d8864faeeb60018b59'), u'imagemap': {u'us-east-1': {u'image': u'12345678'}}}

        :param key: key in JSONPath format
        :param value: dict containing JSON sub-document (document fragment)
        :return: number of nodes that were Set
        """
        return catomongo.update_doc(self._collection_obj, self.doc, value, key)

    def Unset(self, key):
        """
        Unsets fragment at the key.

        Example usage:
        >>> # document before unset
        >>> logger.debug(document.AsJSON())
        {u'_id': ObjectId('507465d8864faeeb60018b59'), u'imagemap': {u'us-east-1': {u'image': u'12345678'}}}
        >>> document.Unset("imagemap.us-east-1.image")
        >>> # will result in a document that may look like this:
        >>> logger.debug(document.AsJSON())
        {u'_id': ObjectId('507465d8864faeeb60018b59'), u'imagemap': {}}

        :param key: key in JSONPath format

        :return: Number of nodes that were unset, 0 if no action was taken since
         there was no node found under given jpath
        """
        #self.doc = catomongo.update_doc_delete(self._collection_obj, self.doc, key)
        return catomongo.unset_doc(self._collection_obj, self.doc, key)

    def Append(self, key, value):
        """
        Appends the value or fragment to the array at an existing key.

        No error is raised in case
        the node being appended to is not a list. This results
        in new list creation and replacment of that node.

        Example usage:
        >>> doc.Append("web", {"instance" : "mnbvcxz", "address" : "33.22.66.11"})

        :param key: key in JSONPath format
        :param value: dict or string containing JSON sub-document (document fragment)
        :return: index at which append was done. 0 if a new list node was created
         as a result of append.

        """
        return catomongo.append_doc(self._collection_obj, self.doc, value, key)

    def Save(self):
        """Saves the document."""
        logger.debug("Saving Document [%s - %s] using \n%s" % (self.collection, self.ID, self.doc))
        return catomongo.save_doc(self._collection_obj, self.doc)


class Documents(object):
    """List all documents in a collection satisfying a given filter.

        :param cfilter: collection filter to apply to collections to retrieve from the
         database

        Two attributes are created:
        _names: a list of just the document names (for REST API output)
        _collections: a list of Mongo collection objects.
    """
    rows = {}

    def __init__(self, collection=None, query={}):
        """Instantiates a set of documents in a collection satisfying a
        given filter.

        Note:
        The current implementation may results in memory problems for
        huge collections, if filter is such that it returns many documents.


        Example usage:

        >>> query = {'guid': '3678df6e-120d-11e2-a0f5-58b035f767f3'}
        >>> docs = Documents(query)

        :type collection: string
        :param collection: collection name to use for creating the document.
        :type query: dict
        :param query: document filter to apply when retrieving documents
        from collection. The filter is in the native mongodb format.
        """
        if not collection:
            collection = "default"
        self.collection = collection
        self._collection_obj = None

        if not query:
            query = {}

        try:
            # _id must be manipulated from a string into an ObjectId
            _id = query.get("_id")
            if _id:
                from bson.objectid import ObjectId
                query["_id"] = ObjectId(_id)

            db = catocommon.new_mongo_conn()
            coll = db[self.collection]
            cursor = coll.find(query)
            self.documents = []
            for d in cursor:
                #d['_id'] = str(d['_id'])
                self.documents.append(d)
        except Exception as ex:
            raise DatastoreError(ex.__str__())

    def count(self):
        """ Returns count of collections """
        return len(self.documents)

    def AsJSON(self):
        """ Returns a json python representation of Documents, which
        is a list of JSON documents


        :rtype: JSON list
        :return : list of JSON documents
        """
        return catocommon.ObjectOutput.IterableAsJSON(self.documents)

    def AsXML(self):
        """ Returns an XML representation of the documents.

        Example:

        <Documents><Document>
            <web><instance>i-ba2911c0</instance><address>54.242.12.216</address>...
        </Document></Documents>

        :rtype: string
        :return : XML representation of the documents
        """
        return catocommon.ObjectOutput.IterableAsXML(self.documents, "Documents", "Document")

    def AsText(self, delimiter=None, headers=None):
        """ Returns a ???
        This is TBD - we don't want to return entire documents, but the _id isn't useful.
        Perhaps we can return a snippet?

        TODO: finish implementation.
        """
        return catocommon.ObjectOutput.IterableAsText(self.documents, ['Documents'], delimiter, headers)


class Collections(object):
    """ Wraps collections in database """
    rows = {}

    def __init__(self, cfilter=""):
        """ Instantiates a collections object containing all collections
         satisfying a given filter.

        Example usage:

        >>> # return all collections having the string 'test' in the name
        >>> colls = Collections("test")


        :param cfilter: collection filter to apply to collections to retrieve from the
         database

        Two attributes are created:
        _names: a list of just the collection names (for REST API output)
        _collections: a list of Mongo collection objects.
        """
        try:

            db = catocommon.new_mongo_conn()
            names = db.collection_names()
            # filter by sfilter
            self._names = filter(lambda x: x.find(cfilter) >= 0, names)

            # strip out the Mongo "system." collections
            self._names = [x for x in self._names if "system." not in x]

            #print self._names
            self._collections = []
            # create collections
            for n in self._names:
                self._collections.append(db[n])
        except Exception as ex:
            raise DatastoreError(ex)

    def count(self):
        """ Returns count of collections """
        return len(self._collections)

    def AsJSON(self):
        return catocommon.ObjectOutput.IterableAsJSON(self._names)

    def AsXML(self):
        return catocommon.ObjectOutput.IterableAsXML(self._names, "Collections", "Collection")

    def AsText(self, delimiter=None, headers=None):
        return catocommon.ObjectOutput.IterableAsText(self._names, ['Collection'], delimiter, headers)
