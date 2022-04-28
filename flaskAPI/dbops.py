from firebase_admin import auth
import datetime
from rec import getEncodings
import numpy as np
from nanoid import generate
class DbHelper:
    @staticmethod
    def getUserId(unique, name, db):
        result = db.users.find_one({"unique": unique})
        if result:
            return result['_id']
        else:
            return db.users.insert_one({"name": name,
                                        "unique": unique,
                                        }).inserted_id

    @staticmethod
    def insertEncoding(encoding, user_id, db):
        return db.encodings.insert_one({"user_id": user_id,
                                        "encoding": encoding.tolist()}).inserted_id

    @staticmethod
    def getEncodingByIden(unique, db):
        result = db.users.find_one({"unique": unique})
        if result:
            return db.encodings.find_one({"user_id": result['_id']})['encoding']
        else:
            return None

    @staticmethod
    def getUserIdFromToken(token):
        try:
            if token.startswith('Bearer '):
                tokenStr = token.split(" ")[1]
                decoded_token = auth.verify_id_token(tokenStr)
                uid = decoded_token['uid']
                return (True, uid)
            else:
                return (False, "unauthorized")
        except auth.InvalidIdTokenError:
            return (False, "expired/invalid")

    @staticmethod
    def initializeUser(args, db):
        try:
            if args['Authorization'].startswith('Bearer '):
                tokenStr = args['Authorization'].split(" ")[1]
                decoded_token = auth.verify_id_token(tokenStr)
                uid = decoded_token['uid']
            else:
                return "unauthorized"
        except auth.InvalidIdTokenError:
            return "expired/invalid"
        result = db.userdata.update_one({'firebaseID': uid}, {'$set': {"priv": args['priv'],"pubID":generate(size=8)}}, upsert=True)
        return "true" if (result.matched_count == 1 or result.upserted_id) else "false"

    @staticmethod
    def getOrgByStr(uniqueStr,db):
        return db.orgs.find_one({"uniqueString":uniqueStr})

    @staticmethod
    def markAttend(uid,orgDetails,args,db):
        newEncodings = np.array(getEncodings({args['pic']}))
        storedEncodings = db.userdata.find_one({"firebaseID":uid})
        if 'faceEncodings' not in storedEncodings:
            return (False,'Calibrate Face First')
        else:
            storedEncodings = storedEncodings['faceEncodings']
        for x in storedEncodings:
            if np.linalg.norm(np.array(x) - newEncodings) < 0.4:
                match = True
                break

        if match:
            attendanceObj = {
                    'org': orgDetails['_id'],
                    'entryExit': args['entryExit'],
                    'timeStamp': datetime.datetime.utcnow(),
                    'automated': False,
                }
            if orgDetails['markLoc']:
                attendanceObj['locx'] = args['locx']
                attendanceObj['locy'] = args['locy']
            db.userdata.update_one({"firebaseID":uid}, {'$push': {'attendance': attendanceObj}})
            return (True,True)
        else:
            return (False,'Face didnt match')

    @staticmethod
    def getEmployees(uid,db,uniqueStr):
        orgPipeline = [{
                "$match": {
                    "owner":uid,
                    "uniqueString":uniqueStr
                }
            },
            {
                "$lookup": {
                        "from": "userdata",
                        "localField": "_id",
                        "foreignField": "joinedOrgs",
                        "as": "users"}
                },
            {
                "$project":{
                    "users.faceEncodings":0,
                    "_id":0,
                    "users.joinedOrgs":0,
                    "users._id":0,
                    "users.attendance":0
                }
            }
            ]
        result = list(db.orgs.aggregate(orgPipeline))
        return {
                'result':True,
                'employees':result
            }

    @staticmethod
    def getOrgs(uid,db):
        result = list(db.orgs.find({'owner':uid},{"_id":0}))
        return {
                'result':True,
                'orgs':result
            }

    @staticmethod
    def hasAuthority(uid,db,pubID):
        orgPipeline = [{
                "$match": {
                    "owner":uid,
                }
            },
            {
                "$lookup": {
                        "from": "userdata",
                        "localField": "_id",
                        "foreignField": "joinedOrgs",
                        "as": "users"}
                },
            {
                "$project":{
                    "users.faceEncodings":0,
                    "_id":0,
                    "users.joinedOrgs":0,
                    "users._id":0,
                    "users.attendance":0
                }
            },{
                "$match":{
                    "users.pubID": pubID
                }
            }
            ]
        result = list(db.orgs.aggregate(orgPipeline))
        if result:
            return True
        else:
            return False

    @staticmethod
    def transfer(uid,db,org_str,pubID):
        orgPipeline = [{
                "$match": {
                    "owner":uid,
                    "uniqueString":org_str
                }
            },
            {
                "$lookup": {
                        "from": "userdata",
                        "localField": "_id",
                        "foreignField": "joinedOrgs",
                        "as": "users"}
                },
            {
                "$project":{
                    "users.faceEncodings":0,
                    "_id":0,
                    "users.joinedOrgs":0,
                    "users._id":0,
                    "users.attendance":0
                }
            },{
                "$match":{
                    "users.pubID": pubID
                }
            }
            ]
        result = db.orgs.aggregate(orgPipeline)
        if result and 'users' in result and result['users']:
            res = db.orgs.update_one({'uniqueStr':org_str},{'owner':result['users'][0]['firebaseID']}).modified_count
            if res>0:
                return {
                    'result':True,
                }
            else:
                return{
                    'result':False,
                    'error':'Not an Owner or New owner didnt join your org'
                }
        else:
            return {
                    'result':False,
                    'error':'Not an Owner or New owner didnt join your org'
                }


    @staticmethod
    def getUserDetails(uid,db):
        orgPipeline = [{
                "$match": {
                    "firebaseID": 0
                }
            },
            {
                "$lookup": {
                        "from": "orgs",
                        "localField": "joinedOrgs",
                        "foreignField": "_id",
                        "as": "orgDetails"}
                },
            {
                "$project":{
                    "attendance.org": 0,
                    "faceEncodings":0,
                    "_id":0,
                    "joinedOrgs":0,
                    "orgDetails._id":0
                }
            }
            ]
        orgPipeline[0]["$match"]["firebaseID"] = uid
        result = list(db.userdata.aggregate(orgPipeline))
        if result:
            dbres = result[0]
            if 'orgDetails' in dbres and dbres['orgDetails']:
                orgDetails = list(dbres['orgDetails'])[0]
            else:
                orgDetails = None
            return {
                'org': orgDetails,
                'user': dbres
            }
        else:
            return{
                'org': None,
                'user':None
            }

    @staticmethod
    def removeExtraQuotes(args):
        for x in args:
            if isinstance(args[x], str):
                args[x] = args[x].strip('"')
        return args

    @staticmethod
    def getLeavesWithOrgs(uid,db):
        orgPipeline = [{
                "$match": {
                    "orgOwner": uid
                }
            },
            {
                "$lookup": {
                        "from": "orgs",
                        "localField": "org",
                        "foreignField": "_id",
                        "as": "orgDetails"}
            },
            {
                "$project":{
                    "_id": 0,
                    "org": 0,
                    'orgDetails._id': 0,
                    'orgDetails.owner': 0,
                    'orgDetails.locationData': 0,
                    'orgDetails.joinPass': 0,
                    'orgOwner': 0
                }
            }
            ]
        dbres = list(db.leaves.aggregate(orgPipeline))
        identifiers = []
        for x in dbres:
            x['startDate'] = x['startDate'].isoformat()
            x['endDate'] = x['endDate'].isoformat()
            identifiers.append(auth.UidIdentifier(x['leaveBy']))
        result = auth.get_users(identifiers)
        memo =[]
        for z in dbres:
            if z['leaveBy'] not in memo:
                for x in result.users:
                    if x.uid == z['leaveBy']:
                        memo.append({x.uid:x.display_name})
                        z['leaveBy'] = x.display_name
            else:
                z['leaveBy'] = memo[z['leaveBy']]
        return dbres

    @staticmethod
    def getMyLeaves(uid,db):
        orgPipeline = [{
                "$match": {
                    "leaveBy": uid
                }
            },
            {
                "$lookup": {
                        "from": "orgs",
                        "localField": "org",
                        "foreignField": "_id",
                        "as": "orgDetails"}
            },
            {
                "$project":{
                    "_id": 0,
                    "org": 0,
                    "leaveBy": 0,
                    'orgDetails._id': 0,
                    'orgDetails.owner': 0,
                    'orgDetails.locationData': 0,
                    'orgDetails.joinPass': 0,
                }
            }
            ]
        dbres = list(db.leaves.aggregate(orgPipeline))
        identifiers = []
        for x in dbres:
            x['startDate'] = x['startDate'].isoformat()
            x['endDate'] = x['endDate'].isoformat()
            identifiers.append(auth.UidIdentifier(x['orgOwner']))
        result = auth.get_users(identifiers)
        memo =[]
        for z in dbres:
            if z['orgOwner'] not in memo:
                for x in result.users:
                    if x.uid == z['orgOwner']:
                        memo.append({x.uid:x.display_name})
                        z['orgOwner'] = x.display_name
            else:
                z['orgOwner'] = memo[z['orgOwner']]
        return dbres
