from flask import Flask
from flask_restx import Resource, Api
from rec import getEncodings
from flask_restx import reqparse
from flask_restx import inputs
from werkzeug.datastructures import FileStorage
import numpy as np
import os
# import sys
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dbops import DbHelper
import firebase_admin
from firebase_admin import auth
import random
import string
app = Flask(__name__)
api = Api(app)
portNo = int(os.environ.get("PORT", 5000))
try:
    dbCred = os.environ["DBCRED"]
except KeyError:
    print("Environment vairable not set")


default_app = firebase_admin.initialize_app()


sec = os.environ['GOOGLE_CRED']
with open(os.environ['GOOGLE_APPLICATION_CREDENTIALS'], 'w') as outfile:
    outfile.write(sec)
    outfile.close()

try:
    client = MongoClient("mongodb+srv://appAdmin:"+dbCred+"@cluster0.g49of.mongodb.net/myFirstDatabase?retryWrites=true&w=majority", server_api=ServerApi('1'))
    db = client.facerec
except KeyError:
    print("Unable to connect to database")


saveParser = reqparse.RequestParser()
saveParser.add_argument('picture',
                        type=FileStorage,
                        location='files')
saveParser.add_argument('name', required=True)
saveParser.add_argument('uniqueId', required=True)

userInitParser = reqparse.RequestParser()
userInitParser.add_argument('Authorization', location='headers', required=True)
userInitParser.add_argument('priv', type=int, location='json', required=True)

orgInitParser = reqparse.RequestParser()
orgInitParser.add_argument('Authorization', location='headers', required=True)
orgInitParser.add_argument('orgName', location='json', required=True)
orgInitParser.add_argument('locEnabled', type=inputs.boolean, location='json', required=True)
orgInitParser.add_argument('markExit', type=inputs.boolean, location='json', required=True)
orgInitParser.add_argument('joinPass', location='json')
orgInitParser.add_argument('locations', location='json',action='split')
orgInitParser.add_argument('locationsRadius', location='json', action='split')

passParser = reqparse.RequestParser()
passParser.add_argument('p', location='values')
passParser2 = passParser.copy()
passParser2.add_argument('Authorization', location='headers', required=True)

@api.route('/hello')
# @api.doc(params={'id': 'An ID'})
@api.doc()
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}


@api.route('/checkface')
@api.doc(params={'picture': 'An Image'})
class FaceEncoder(Resource):
    @api.expect(saveParser)
    def post(self):
        args = saveParser.parse_args()
        img = args['picture']
        unique = args['uniqueId']
        # storedEnc = np.load(args['name']+'.npy', allow_pickle=True)
        storedEnc = np.array(DbHelper.getEncodingByIden(unique, db))
        encodings = np.array(getEncodings({img}))
        return {'match': np.linalg.norm(storedEnc - encodings)}


@api.route('/saveface')
@api.doc(params={'picture': 'An Image'})
class FaceSaver(Resource):
    @api.expect(saveParser)
    def post(self):
        args = saveParser.parse_args()
        img = args['picture']
        name = args['name']
        unique = args['uniqueId']
        encodings = np.array(getEncodings({img}))
        # np.save(args['name']+'.npy', encodings)
        user_id = DbHelper.getUserId(unique, name, db)
        inserted_id = DbHelper.insertEncoding(encodings, user_id, db)
        return {'success': True if inserted_id else False}


@api.route('/inituser')
@api.doc(params={'payload': 'employee if 0, manager if 1',
                 'Authorization': 'firebase token'})
class CustomerInit(Resource):
    @api.expect(userInitParser)
    def post(self):
        args = userInitParser.parse_args()
        if args['priv'] == 0 or args['priv'] == 1:
            return {'result': DbHelper.initializeUser(args, db)}
        else:
            return{'result': 'false'}


@api.route('/initorg')
@api.doc(params={'payload': 'company name, locationEnabled? , locations and allowed range if required',
                 'Authorization': 'firebase token'})
class OrgInit(Resource):
    @api.expect(orgInitParser)
    def post(self):
        args = orgInitParser.parse_args()
        res, uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            orgToAdd = {
                'orgName': args['orgName'],
                'markExit': args['markExit'],
                'owner': uid,
                'markLoc': args['locEnabled'],
            }
            if args['locEnabled']:
                if 'locations' in args and args['locations']:
                    indx = 0
                    locationData = []
                    for i in args['locations']:
                        try:
                            x,y=i.split(":")
                        except:
                            return {"result": "invalid location data"}
                        if "locationsRadius" in args and indx < len(args['locationsRadius']):
                            rad = min(500, max(int(args['locationsRadius'][indx]), 20))
                        else:
                            rad = 30
                        locationData.append({
                            "xcord": x,
                            "ycord": y,
                            "radius": rad
                        })
                        indx = indx + 1
                else:
                    return {'result': 'Geofencing Enabled but missing Locations'}
                orgToAdd['locationData'] = locationData
            if args['joinPass']:
                if len(args['joinPass']) < 4:
                    return {'result': 'Password too short'}
                else:
                    orgToAdd['joinPass'] = args['joinPass']
            uniqueStr = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
            orgToAdd['uniqueString'] = uniqueStr
            db.orgs.insert_one(orgToAdd)
            return {'result': True,
                    'uniqueStr': uniqueStr}
        else:
            return {'result': 'Unauthorized'}


@api.route('/join/<string:org_str>')
class JoinOrg(Resource):
    @api.expect(passParser)
    def get(self, org_str):
        args = passParser.parse_args()
        org = DbHelper.getOrgByStr(org_str, db)
        if org:
            if ('joinPass' in org and 'p'in args and args['p'] == org['joinPass']) or ('joinPass' not in org):
                result = { 'orgName': org['orgName']}
                owner = auth.get_user(org.pop('owner'))
                result['ownerName'] = owner.display_name
                result['ownerPhoto'] = owner.photo_url
                if org['markLoc']:
                    numLoc = len(org['locationData'])
                    org.pop('locationData')
                    result['numLoc'] = numLoc
                result['verified'] = True
                return result
            else:
                return {
                    'orgName': org['orgName'],
                    'verified': False
                }
        else:
            return {
                'result': False
            }


    @api.expect(passParser2)
    def post(self,org_str):
        args = passParser2.parse_args()
        res,uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            org = DbHelper.getOrgByStr(org_str, db)
            if org:
                if ('joinPass' in org and 'p'in args and args['p'] == org['joinPass']) or ('joinPass' not in org):
                    #db.userdata.update_one({'firebaseID':uid}, {'$push': {'joinedOrgs': org['_id']}})
                    db.userdata.update_one({'firebaseID':uid},{'$set':{'joinedOrgs': org['_id']}})
                    return{ 'result':True}
                else:
                    return{ 'result': 'Incorrect password'}
            else:
                return{ 'result': 'Org not found'}
        else:
            return{
                'result':uid
            }

if __name__ == '__main__':
    if "IS_DEV" in os.environ:
        app.run(port=portNo, debug=False)
    else:
        app.run(host='0.0.0.0', port=portNo, debug=False)
    # app.run(debug=False)
