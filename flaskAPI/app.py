from flask import Flask
from flask_restx import Resource, Api
from rec import getEncodings
from flask_restx import reqparse
from flask_restx import inputs
from werkzeug.datastructures import FileStorage
import numpy as np
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dbops import DbHelper
import firebase_admin
from firebase_admin import auth
import geopy.distance
import datetime
import math
from nanoid import generate
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
    client = MongoClient(dbCred, server_api=ServerApi('1'))
    db = client.facerec
except KeyError:
    print("Unable to connect to database") // connect to databse


saveParser = reqparse.RequestParser()
saveParser.add_argument('picture',
                        type=FileStorage,
                        location='files')
saveParser.add_argument('name', required=True)
saveParser.add_argument('uniqueId', required=True)

userInitParser = reqparse.RequestParser()
userInitParser.add_argument('Authorization', location='headers', required=True)
userInitParser.add_argument('priv', type=int, location='form', required=True)

orgInitParser = reqparse.RequestParser()
orgInitParser.add_argument('Authorization', location='headers', required=True)
orgInitParser.add_argument('orgName', location='form', required=True)
orgInitParser.add_argument('locEnabled', type=inputs.boolean, location='form', required=True)
orgInitParser.add_argument('markExit', type=inputs.boolean, location='form', required=True)
orgInitParser.add_argument('allowMissedExit', type=inputs.boolean, location='form', required=True)
orgInitParser.add_argument('defMissedInterval',type=int, location='form')
orgInitParser.add_argument('joinPass', location='form')
orgInitParser.add_argument('locations', location='form',action='split')
orgInitParser.add_argument('locationsRadius', location='form', action='split')
orgInitParser.add_argument('defStart', location='form', required=True)
orgInitParser.add_argument('defEnd', location='form', required=True)


passParser = reqparse.RequestParser()
passParser.add_argument('p', location='values')
passParser2 = passParser.copy()
passParser2.add_argument('Authorization', location='headers', required=True)

userDetailsParser = reqparse.RequestParser()
userDetailsParser.add_argument('Authorization', location='headers', required=True)

calibrationParser = userDetailsParser.copy()
calibrationParser.add_argument('pic1',
                        type=FileStorage,
                        location='files',
                        required=True)
calibrationParser.add_argument('pic2',
                        required=True,
                        type=FileStorage,
                        location='files')
calibrationParser.add_argument('pic3',
                        type=FileStorage,
                        location='files',
                        required=True)

attendanceParser = reqparse.RequestParser()
attendanceParser.add_argument('Authorization', location='headers', required=True)
attendanceParser.add_argument('pic',
                        type=FileStorage,
                        location='files',
                        required=True)
attendanceParser.add_argument('locx',location='form')
attendanceParser.add_argument('locy',location='form')
attendanceParser.add_argument('entryExit', location='form', type=inputs.boolean, required=True)

newLeaveParser = userDetailsParser.copy()
newLeaveParser.add_argument('startDate', type=inputs.date, location='form',required=True)
newLeaveParser.add_argument('endDate', type=inputs.date, location='form',required=True)
newLeaveParser.add_argument('message', location='form',required=True)

approveLeaveParser = userDetailsParser.copy()
approveLeaveParser.add_argument('pubID', location='form', required=True)

cache={}

@api.route('/hello')
# @api.doc(params={'id': 'An ID'})
@api.doc()
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}


@api.deprecated
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


@api.deprecated
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
@api.doc(params={'priv': 'employee if 0, manager if 1',
                 'Authorization': 'firebase token'})
class CustomerInit(Resource):
    @api.expect(userInitParser)
    def post(self):
        args = userInitParser.parse_args()
        if args['priv'] == 0 or args['priv'] == 1:
            return {'result': DbHelper.initializeUser(args, db)}
        else:
            return{'result': False,
                   'error':'Invalid Parameters'}


@api.route('/initorg')
@api.doc(params={'orgName': 'Name of the org',
                 'markExit': 'Whether to mark Exit times',
                 'allowMissedExit': 'Whether to enable automatic exit marking',
                 'defMissedInterval': 'Time in minutes to refresh location and mark attendance when last spotted in radius ',
                 'joinPass': 'Password to join org',
                 'defStart': 'Default Start Time',
                 'defEnd': 'Default End Time',
                 'locEnabled': 'Whether to enable geofencing',
                 'locations': 'latituide longitude seperated by colon',
                 'locationsRadius': 'radius within which marking attendance is allowed, default is 25',
                 'Authorization': 'firebase token'})
class OrgInit(Resource):
    @api.expect(orgInitParser)
    def post(self):
        args = orgInitParser.parse_args()
        args = DbHelper.removeExtraQuotes(args)
        res, uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            orgToAdd = {
                'orgName': args['orgName'],
                'markExit': args['markExit'],
                'owner': uid,
                'markLoc': args['locEnabled'],
                'allowMissedExit': args['allowMissedExit'],
                'defStart': args['defStart'],
                'defEnd': args['defEnd']
            }
            if args['locEnabled']:
                if 'locations' in args and args['locations']:
                    indx = 0
                    locationData = []
                    for i in args['locations']:
                        try:
                            x,y=i.split(":")
                        except:
                            return {'result': False,
                                    'error': "invalid location data"}
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
                    return {'result': False,
                            'error': 'Geofencing Enabled but missing Locations'}
                orgToAdd['locationData'] = locationData
            if args['joinPass']:
                if len(args['joinPass']) < 4:
                    return {'result': False,
                            'error': 'Password too short'}
                else:
                    orgToAdd['joinPass'] = args['joinPass']
            uniqueStr = generate(size=6)
            orgToAdd['uniqueString'] = uniqueStr
            if args['allowMissedExit'] and args['markExit']:
                if 'defMissedInterval' in args:
                    orgToAdd['defMissedInterval'] = max(5,min(60,args['defMissedInterval']))
                else:
                    return {
                        'result': False,
                        'error': 'required interval if automark exit is enabled'
                    }
            db.orgs.insert_one(orgToAdd)
            return {'result': True,
                    'uniqueStr': uniqueStr}
        else:
            return {'result': False,
                    'error': 'Unauthorized'}


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
                result['result'] = True
                if org['markLoc']:
                    numLoc = len(org['locationData'])
                    org.pop('locationData')
                    result['numLoc'] = numLoc
                result['verified'] = True
                return result
            else:
                return {
                    'result': True,
                    'orgName': org['orgName'],
                    'verified': False
                }
        else:
            return {
                'result': False,
                'error': 'Org Doesnt Exist'
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
                    return{
                            'result': False,
                            'error': 'Incorrect password'
                          }
            else:
                return{
                        'result': False,
                        'error': 'Org not found'
                    }
        else:
            return{
                'result': False,
                'error':uid
            }

@api.route('/userdetails')
class UserDetails(Resource):
    @api.expect(userDetailsParser)
    def post(self):
        args = userDetailsParser.parse_args()
        res,uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            userres = DbHelper.getUserDetails(uid, db)
            if userres['user']:
                orgDetails = userres['org']
                attendanceObj = None
                if orgDetails:
                    owner = auth.get_user(orgDetails.pop('owner'))
                    orgDetails['ownerName'] = owner.display_name
                    orgDetails['ownerPic'] = owner.photo_url
                    attendanceObj = userres["user"]['attendance']
                    for x in attendanceObj:
                        x['timeStamp'] = x['timeStamp'].isoformat()

                result = {
                    'result': True,
                    'priv': userres['user']['priv'],
                    'attendance':attendanceObj,
                    'orgDetails': orgDetails
                }
            else:
                result = {
                    'result':False,
                    'error':"User Not Found"
                }
            return result
        else:
            return{
                'result': False,
                'error': uid
            }


@api.route('/calibrate')
class CalibrateFace(Resource):
    @api.expect(calibrationParser)
    def post(self):
        args = calibrationParser.parse_args()
        res,uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            args.pop('Authorization')
            enc = []
            for x in ['pic1','pic2','pic3']:
                enc.append(np.array(getEncodings({args[x]})).tolist())

            if len(enc) > 0:
                db.userdata.update_one({'firebaseID': uid}, {"$set": {"faceEncodings": enc}})
                return {
                    'result': True
                }
            else:
                return {
                    'result': False,
                    'error': 'no faces found'
                }
        else:
            return{
                'result': False,
                'error': uid
            }

@api.route('/markattendance')
@api.doc(params={'pic':'Current Picture of user to check if face matches',
                  'locx': 'Current Latitude',
                  'locy': 'Current Longitude',
                  'entryExit': 'Whether this attendance is entry or exit'})
class MarkAttendance(Resource):
    @api.expect(attendanceParser)
    def post(self):
        args = attendanceParser.parse_args()
        args = DbHelper.removeExtraQuotes(args)
        res,uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            userres = DbHelper.getUserDetails(uid, db)
            if not userres['user']:
                return {
                    'result':False,
                    'error': 'No user found'
                }
            if not userres['org']:
                return {
                    'result':False,
                    'error': 'Join org first'
                }
            dbres = userres['user']
            orgDetails = userres['org']
            if not orgDetails['markExit'] and args['entryExit']:
                return{
                    'result':False,
                    'error': 'Org doesnt allow to mark exit'
                }
            if 'attendance' in dbres and dbres['attendance']:
                lastAttendance = dbres['attendance'][-1]
                attendanceType = "Entry" if args['entryExit'] else "Exit"
                if args['entryExit'] == lastAttendance['entryExit'] and datetime.datetime.utcnow().date() == lastAttendance['timeStamp'].date():
                    return {
                        'result':False,
                        'error': attendanceType + 'Already Marked today at '+lastAttendance['timeStamp'].isoformat()
                    }
                elif not lastAttendance['entryExit'] and args['entryExit'] and datetime.datetime.utcnow().date() == lastAttendance['timeStamp'].date():
                    return {
                        'result':False,
                        'error': 'Entry after Exit'
                    }
                elif not args['entryExit'] and datetime.datetime.utcnow().date() != lastAttendance['timeStamp'].date():
                    return{
                        'result':False,
                        'error': 'Exit before Entry'
                    }
            elif not args['entryExit']:
                return {
                    'result':False,
                    'error': 'Cant exit without entry'
                }
            if orgDetails['markLoc'] == True and ('locx' not in args or 'locy' not in args):
                return{
                    'result':False,
                    'error': 'location required'
                }
            elif orgDetails['markLoc'] == True and 'locx' in args and 'locy' in args:
                mindist = None
                minr = None
                for x in orgDetails['locationData']:
                    dist = geopy.distance.geodesic((args['locx'],args['locy']), (x['xcord'],x['ycord'])).m
                    if (not mindist or dist<mindist):
                        mindist = dist
                        minr = x['radius']
                    if dist < x['radius']:
                        result = DbHelper.markAttend(uid, orgDetails, args, db)
                        return{
                                'result': result[1]
                            }
                return {
                    'result':False,
                    'error': 'Out of range (metres)',
                    'dist': str(math.ceil(mindist-minr))
                }
            elif not orgDetails['markLoc']:
                result = DbHelper.markAttend(uid, orgDetails, args, db)
                return {
                        'result': result
                    }
            return {
                'result': False,
                'error':'Some Error Occured'
            }
        else:
            return{
                'result':False,
                'error': uid
            }


@api.route('/newleave')
@api.doc(params={'Authorization': 'firebase token'})
class NewLeave(Resource):
    @api.expect(newLeaveParser)
    def post(self):
        args = newLeaveParser.parse_args()
        args = DbHelper.removeExtraQuotes(args)
        res,uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            userres = DbHelper.getUserDetails(uid, db)
            if userres['org']:
                db.leaves.insert_one({
                    'org': userres['org']['uniqueString'],
                    'orgOwner': userres['org']['owner'],
                    'leaveBy': userres['user']['firebaseID'],
                    'startDate': args['startDate'],
                    'endDate': args['endDate'],
                    'msg': args['message'],
                    'approved': 0,
                    'approvalTime': None,
                    'pubID': generate(size=8)
                })
                return {
                    'result': True
                }
            else:
                return {
                    'result': False,
                    'error': 'No org to create leave request'
                }
        else:
            return{
                'result':False,
                'error': uid
            }


@api.route('/getLeaves')
@api.doc(params={'Authorization': 'firebase token'})
class GetLeaves(Resource):
    @api.expect(userDetailsParser)
    def post(self):
        args = userDetailsParser.parse_args()
        res,uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            dbres = DbHelper.getLeavesWithOrgs(uid, db)
            if dbres:
                return {
                    'result':True,
                    'leaves':dbres
                }
            else:
                return {
                    'result':False,
                    'error': 'No Leaves Found'
                }
        else:
            return{
                'result':False,
                'error': uid
            }


@api.route('/myleaves')
@api.doc(params={'Authorization': 'firebase token'})
class MyLeaves(Resource):
    @api.expect(userDetailsParser)
    def post(self):
        args = userDetailsParser.parse_args()
        res,uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            dbres = DbHelper.getMyLeaves(uid, db)
            if dbres:
                return {
                    'result':True,
                    'leaves':dbres
                }
            else:
                return {
                    'result':False,
                    'error': 'No Leaves Found'
                }
        else:
            return{
                'result':False,
                'error': uid
            }
        

@api.route('/approveLeave')
@api.doc(params={'Authorization': 'firebase token'})
class ApproveLeaves(Resource):
    @api.expect(approveLeaveParser)
    def post(self):
        args = approveLeaveParser.parse_args()
        args = DbHelper.removeExtraQuotes(args)
        res, uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            dbres = db.leaves.update_one({'pubID':args['pubID']},{'$set':{'approved':1,'approvalTime':datetime.datetime.utcnow().date().isoformat()}})
            if dbres.modified_count > 0:
                return {
                    'result':True,
                }
            else:
                return {
                    'result':False,
                    'error': 'No Leaves Found'
                }
        else:
            return{
                'result':False,
                'error': uid
            }

@api.route('/getemployees/<string:org_str>')
@api.doc(params={'Authorization': 'firebase token'})
class GetEmployees(Resource):
    @api.expect(userDetailsParser)
    def post(self,org_str):
        args = userDetailsParser.parse_args()
        res, uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            return DbHelper.getEmployees(uid, db,org_str)
        else:
            return{
                'result':False,
                'error': uid
            }

@api.route('/getorgs')
@api.doc(params={'Authorization': 'firebase token'})
class GetOrgs(Resource):
    @api.expect(userDetailsParser)
    def post(self):
        args = userDetailsParser.parse_args()
        res, uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            return DbHelper.getOrgs(uid, db)
        else:
            return{
                'result':False,
                'error': uid
            }

@api.route('/leaveorg')
@api.doc(params={'Authorization': 'firebase token'})
class LeaveOrg(Resource):
    @api.expect(userDetailsParser)
    def post(self):
        args = userDetailsParser.parse_args()
        res, uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            db.userdata.update_one({'firebaseID':uid}, {"$set":{"joinedOrgs":None,"attendance":None,"faceEncodings":None}})
            return{
                'result':True
            }
        else:
            return{
                'result':False,
                'error': uid
            }

@api.route('/removeemp')
@api.doc(params={'Authorization': 'firebase token'})
class RemoveEmployee(Resource):
    @api.expect(approveLeaveParser)
    def post(self):
        args = approveLeaveParser.parse_args()
        res, uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            if DbHelper.hasAuthority(uid, db, args['pubID']):
                res = db.userdata.update_one({'pubID':args['pubID']}, {"$set":{"joinedOrgs":None,"attendance":None,"faceEncodings":None}}).modified_count
                if res>0:            
                    return{
                        'result':True
                    }
                else:
                    return{
                        'result':False,
                        'error': 'No user found'
                    }
            else:
                {
                        'result':False,
                        'error': 'Not Authorised to Remove'
                }

        else:
            return{
                'result':False,
                'error': uid
            }

@api.route('/delete/<string:org_str>')
@api.doc(params={'Authorization': 'firebase token'})
class DeleteOrg(Resource):
    @api.expect(userDetailsParser)
    def post(self,org_str):
        args = userDetailsParser.parse_args()
        res, uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            result = db.orgs.find_one({'owner':uid,'uniqueString':org_str})
            if result:
                db.userdata.update_many({'joinedOrgs':result['_id']}, {"$set":{"attendance":None,"faceEncodings":None,"joinedOrgs":None}})
                db.orgs.delete_one({"_id":result["_id"]})
                return{
                        'result':True
                    }
            else:
                return{
                'result':False,
                'error': "Not an Org owner or Incorrect Org Code"
            }    
        else:
            return{
                'result':False,
                'error': uid
            }
        
@api.route('/deleteaccount')
@api.doc(params={'Authorization': 'firebase token'})
class DeleteUser(Resource):
    @api.expect(userDetailsParser)
    def post(self):
        args = userDetailsParser.parse_args()
        res, uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            result = db.orgs.find_one({'owner':uid})
            if result:
                return {
                    'result': False,
                    'error': "Transfer Org ownership of "+result['orgName']+" or delete org before deleting account"
                }
            else:
                db.userdata.delete_one({'firebaseID':uid})
                return{
                    'result':True,
                }    
        else:
            return{
                'result':False,
                'error': uid
            }      

@api.route('/transfer/<string:org_str>')
@api.doc(params={'Authorization': 'firebase token'})
class DeleteUser(Resource):
    @api.expect(approveLeaveParser)
    def post(self,org_str):
        args = approveLeaveParser.parse_args()
        res, uid = DbHelper.getUserIdFromToken(args['Authorization'])
        if res:
            return DbHelper.transfer(uid, db, org_str, args['pubID'])
        else:
            return{
                'result':False,
                'error': uid
            }      


if __name__ == '__main__':
    if "IS_DEV" in os.environ:
        app.run(port=portNo, debug=False)
    else:
        app.run(host='0.0.0.0', port=portNo, debug=False)
    # app.run(debug=False)
