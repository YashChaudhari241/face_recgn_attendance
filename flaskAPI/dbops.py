from firebase_admin import auth
import datetime
from rec import getEncodings
import numpy as np
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
        result = db.userdata.update_one({'firebaseID': uid}, {'$set': {"priv": args['priv']}}, upsert=True)
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
