#!/bin/bash
# shutdown mongodb server
# run on the server that hosts mongodb

# adjust path to mongo on Mac/Windows or other dev system
MONGO=mongo

# perform shutdown
$MONGO --quiet admin --eval 'db.shutdownServer()'

