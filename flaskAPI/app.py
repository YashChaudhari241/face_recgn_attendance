from flask import Flask
from flask_restx import Resource, Api
from rec import getEncodings
from flask_restx import reqparse
from werkzeug.datastructures import FileStorage
import numpy as np
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dbops import getUserId, insertEncoding, getEncodingByIden

app = Flask(__name__)
api = Api(app)
portNo = int(os.environ.get("PORT", 5000))
try:
    dbCred = os.environ["DBCRED"]
except KeyError:
    print("Environment vairable not set")

try:
    client = MongoClient("mongodb+srv://appAdmin:"+dbCred+"@cluster0.g49of.mongodb.net/myFirstDatabase?retryWrites=true&w=majority", server_api=ServerApi('1'))
    db = client.facerec
except KeyError:
    print("Unable to connect to database")


saveparser = reqparse.RequestParser()
saveparser.add_argument('picture',
                        type=FileStorage,
                        location='files')
saveparser.add_argument('name', required=True)
saveparser.add_argument('uniqueId', required=True)

@api.route('/hello')
# @api.doc(params={'id': 'An ID'})
@api.doc()
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}


@api.route('/checkface')
@api.doc(params={'picture': 'An Image'})
class FaceEncoder(Resource):
    @api.expect(saveparser)
    def post(self):
        args = saveparser.parse_args()
        img = args['picture']
        unique = args['uniqueId']
        # storedEnc = np.load(args['name']+'.npy', allow_pickle=True)
        storedEnc = np.array(getEncodingByIden(unique, db))
        encodings = np.array(getEncodings({img}))
        return {'match': np.linalg.norm(storedEnc - encodings)}


@api.route('/saveface')
@api.doc(params={'picture': 'An Image'})
class FaceSaver(Resource):
    @api.expect(saveparser)
    def post(self):
        args = saveparser.parse_args()
        img = args['picture']
        name = args['name']
        unique = args['uniqueId']
        encodings = np.array(getEncodings({img}))
        # np.save(args['name']+'.npy', encodings)
        user_id = getUserId(unique, name, db)
        inserted_id = insertEncoding(encodings, user_id, db)
        return {'success': True if inserted_id else False}


if __name__ == '__main__':
    if "IS_DEV" in os.environ:
        app.run(port=portNo, debug=False)
    else:
        app.run(host='0.0.0.0', port=portNo, debug=False)
    # app.run(debug=False)
