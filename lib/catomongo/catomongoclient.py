"""
Cato mongodb client - mongodb database access layer.


Sample document store in the database:

{
    "app": {
        "address": "107.22.57.90",
        "instance": "i-30340c4a"
    },
    "database": {},
    "proxy": {
        "address": "50.16.150.144",
        "instance": "i-ba2119c0"
    },
    "web": {
        "address": "54.242.12.216",
        "instance": "i-ba2911c0"
    }
}


Usage:

This is a thin layer around pymongo.

All collection functions are the same - see:
http://api.mongodb.org/python/current/api/pymongo/collection.html

This has been tested with mongodb server 2.2.


"""

from catolog import catolog
logger = catolog.get_logger(__name__)

import pymongo
from bson.objectid import ObjectId
from jsonpath import jsonpath
from catoerrors import BadParameterError

def jsonpath_replace(doc, fragment, jpath, append = False):
    """ 
    Performs a JSONPath update transaction.
    Implement the update part of JSONPath, using its facility to
    retrieve paths to JSONPath extraction results, rather than
    results themselves, and them building a Python statement from
    the paths that are executed to perform assignments of fragment
    to individual nodes in the dict tree.
    
    If there are more than than one nodes found in the dict tree, all of them
    will be assigned the fragment.
    If fragment is None, the node(s) will be removed.
    
    >>> tdoc = {'web': [{'instance': 'i-ba2911c0', 'address': '54.242.12.1'}, {'instance': 'this is not the one', 'address': '54.242.12.3'}, {'instance': 'this is the one', 'address': '54.242.12.3'}, {'instance': 'i-ba2911c0', 'address': '54.242.12.4'}], 'app': {'instance': 'i-30340c4a', 'address': '107.22.57.90'}, 'proxy': {'instance': 'i-ba2119c0', 'address': '50.16.150.144'}, 'database': {}}
    >>> jpath = 'web[2].address'
    >>> fragment = '111.111.111.111'
    >>> jsonpath_replace(tdoc, jpath, fragment)
    doc['web'][2]['address'] = fragment
    >>> tdoc
    {'web': [{'instance': 'i-ba2911c0', 'address': '54.242.12.1'}, 
      {'instance': 'this is not the one', 'address': '54.242.12.3'}, 
      {'instance': 'this is the one', 'address': '111.111.111.111'}, 
      {'instance': 'i-ba2911c0', 'address': '54.242.12.4'}], 
      'app': {'instance': 'i-30340c4a', 'address': '107.22.57.90'}, 
      'proxy': {'instance': 'i-ba2119c0', 'address': '50.16.150.144'}, 
      'database': {}}

    :type doc: dict
    :param doc: json doc
    :type fragment: str or dict
    :param fragment: fragment to replace JSONPath node with
    :type jpath: str
    :param jpath: JSONPath string
    
    :return: number of assignments performed
    
    """
    import jsonpath
    ipath = jsonpath.jsonpath(doc, jpath, result_type='IPATH')
    #print ipath
    # for example:
    # 1) web[2].address -> [[web', '2', 'address']]
    # or, given a certain doc:
    # 2) $..book[?(@.price<10)]', '$;..;book;?(@.price<10) 
    #  -> [['store', 'book', '0'], ['store', 'book', '2']]
    docname = 'doc'
    rhs = 'fragment'
    statements = []
    # build all assignment statements
    if ipath:
        for ip in ipath:
            expr = docname
            for w in ip:
                if w.isdigit():
                    expr += "[%s]" % w
                else:
                    expr += "['%s']" % w
            if append:
                # e.g.
                # >>> if isinstance(doc['web'], list): doc['web'].append('a')
                # ... else: doc['web'] = ['a']
                statement = 'if isinstance(%s, list): %s.append(fragment)\nelse: %s = [fragment]' % \
                  (expr, expr, expr)
                expr = statement
            elif fragment == None:
                expr = "del %s" % expr
            else:
                expr += " = %s" % rhs
            statements.append(expr)
            
    # example result statements:
    # for case 1):
    #   ["doc['web'][2]['address'] = fragment"]
    # for case 2):
    #  
    #print statements
    for s in statements:
        exec(s)
    return len(statements)
    
def _put(d, k, item):
    """ Puts item at key in dict d """
    if "." in k:
        key, rest = k.split(".", 1)
#                    print d
#                    print "key %s" % key
#                    print "rest %s" % rest
        if key not in d:
#                        print "%s doesn't exist, creating" % key
            # key doesn't exist, make it a dict node
            d[key] = {}
        else:
#                        print "%s exists..." % key
            # key does exist, and it's not already a dictionary
            if rest and not type(d[key]) == dict:
                # there are more keys coming... gotta make this into a dict
                d[key] = {} # destroys any existing text value... no other way

        _put(d[key], rest, item)
    else:
#                    print "%s is the last node, setting..." % k
        d[k] = item



def modify_doc(doc, doc_fragment, jpath, append = False):
    """ Modifies doc by replacing doc fragment at given JSONPath
      by the given doc fragment.
      
    Creates the parent key(s) and document if necessary.

    :type doc: dict
    :param doc: JSON document to update
    
    :type doc_fragment: dict or string
    :param doc_fragment: document fragment with which to update
    
    :type jpath: string
    :param jpath: JSONPath at which to update the fragment
    :return: number of nodes modified
    """
    logger.debug('modify_doc: doc_fragment, jpath: %s, %s' % (doc_fragment, jpath))
    # eval doesn't work with ObjectId.
    # we therefore replace ObjectId with string
    # {'_id': ObjectId('506da6b025dc9a250b000000'),
    id = doc.get('_id')
    if id and not isinstance(id, str):
        doc['_id'] = str(id)
    # identify map subnode to modify/update
    subdocs = jsonpath(doc, jpath)
    if append and subdocs and len(subdocs) > 1:
        raise BadParameterError('append can be performed only on JSONPath that matches a single node')
    
    if append and (not subdocs or (subdocs and not isinstance(subdocs[0], list))):
        # create a new list
        _put(doc, jpath, [])
        subdocs = jsonpath(doc, jpath)
        assert(subdocs)
    if not subdocs:
        logger.debug('modify_doc: %s applied to %s yielded no results' % \
                       (jpath, doc))
        # create the given doc_fragment at jpath
        _put(doc, jpath, doc_fragment)
        ret = 1
    else:
        
        ret = jsonpath_replace(doc, doc_fragment, jpath, append)
        # restore original id
        #if id:
        #    doc['_id'] = id
    return ret

def update_doc(coll, doc, doc_fragment, jpath):
    """ Updates the document fragment at the given JSONPath key.

    Creates the parent key(s) and document if necessary.

    :param coll: collection for which document is being updated
    
    :type doc: dict
    :param doc: JSON document to update
    
    :type doc_fragment: map
    :param doc_fragment: document fragment to update
    
    :type jpath: string
    :param jpath: JSONPath at which to update the fragment
      
    """
    # modify the doc
    count = modify_doc(doc, doc_fragment, jpath)
    _do_save(coll, doc)
    return count

def _do_save(coll, doc):
    # update modifed doc in db
    if doc.has_key('_id'):
        if isinstance(doc['_id'], unicode) or isinstance(doc['_id'], str):
            doc['_id'] = ObjectId(doc['_id'])
    #filt = {'_id': ObjectId(doc['_id'])}
    #logger.debug('_do_save: %s, filter: %s' % (doc, filt))
    #print('_do_save: %s' % doc)
    coll.save(doc)
    
def append_doc(coll, doc, doc_fragment, jpath):
    """ Appends to the document fragment at the given JSONPath key.
    
    Creates the parent key(s) and document if necessary.

    :param coll: collection for which document is being updated
    
    :type doc: dict
    :param doc: JSON document to append to
    
    :type doc_fragment: map
    :param doc_fragment: document fragment to append
    
    :type jpath: string
    :param jpath: JSONPath at which to append the fragment

    :return: index at which append was done. 0 if a new list node was created
     as a result of append.
           
    """
    # modify the doc
    modify_doc(doc, doc_fragment, jpath, append=True)
    _do_save(coll, doc)
    #logger.debug('update_doc: %s, filter: %s' % (doc, filt))
    subdocs = jsonpath(doc, jpath)
    #print('append_doc: %s' % subdocs)
    if subdocs:
        # append happened at index {len - 1)
        ret = len(subdocs[0]) - 1
    else:
        ret = 0
    return ret

def unset_doc(coll, doc, jpath):
    """ Removes node at given JSONPath 
    
    :return: True if node was unset, False if no action was taken since
     there was no code found under given jpath
    
    """
    id = doc.get('_id')
    if id and not isinstance(id, str):
        doc['_id'] = str(id)
    # identify map subnode to modify/update
    subdocs = jsonpath(doc, jpath)
    if subdocs:
        count = jsonpath_replace(doc, None, jpath)
        _do_save(coll, doc)
    else:
        #logger.debug('unset_doc: %s applied to %s yielded no results, therefore nothing removed from doc' % \
        #               (jpath, doc))
        count = 0
    return count
    
    

def extract_fragment_from_doc(doc, jpath):
    """ Extract a fragment from document at the given JSONPath.
    
    Usage:
    Extract address fragment from document
    >>> subdoc = extract_fragment_from_doc(doc, '$.app.address')

    # return all addresses in the document:
    >>> extract_fragment_from_doc(doc, '$..address')

    :param doc: doc from which fragment is being extracted

    :type jpath: string
    :param jpath: JSONPath at which to update the fragment

    :rtype: map
    :return: a JSON document
    
    """
    return jsonpath(doc, jpath)


def query_doc(coll, jpath):
    """ Performs a query in collection using the JSONPath.
    
    For example, return all documents satisfying the given JSONPath expression.
    i.e. all documents that contain a non-empty value at the given JSONPath
    >>> query_doc(coll, '$.app.address')


    # return all documents with a non-empty address:
    >>> query_doc(coll, '$..address')

    :param coll: collection being queried

    :type jpath: string
    :param jpath: JSONPath at which to update the fragment

    :rtype: list 
    :return: a list of map (a list of JSON documents)
    
    """
    # initially, using brute force approach: 
    # 1. first get all docs,
    docs = coll.find()
    # 2. then filter those that have a match of jpath
    results = filter(lambda x: jsonpath(x, jpath), docs)
    return results

def save_doc(coll, doc):
    _do_save(coll, doc)
    
def delete_doc(doc):
    """ Deletes a document from a collection.
    
    :type doc: map
    :param doc: JSON document to update
    
    """
    doc._collection_obj.remove(ObjectId(doc.ID))

class Connection(pymongo.Connection):
    """ Cato mongodb client"""

    def __init__(self, host, port, username=None, password=None):
        #logger.debug('host: %s, port: %s, username: %s' % (host, port, username))
        self.username = username
        self.password = password
        pymongo.Connection.__init__(self, host, port)
        
    

