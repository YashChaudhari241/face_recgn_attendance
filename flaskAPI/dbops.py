from firebase_admin import auth

def getUserId(unique, name, db):
    result = db.users.find_one({"unique": unique})
    if result:
        return result['_id']
    else:
        return db.users.insert_one({"name": name,
                                    "unique": unique,
                                    }).inserted_id


def insertEncoding(encoding, user_id, db):
    return db.encodings.insert_one({"user_id": user_id,
                                    "encoding": encoding.tolist()}).inserted_id


def getEncodingByIden(unique, db):
    result = db.users.find_one({"unique": unique})
    if result:
        return db.encodings.find_one({"user_id": result['_id']})['encoding']
    else:
        return None


def initializeUser(args, db):
    decoded_token = auth.verify_id_token(args['token'])
    uid = decoded_token['uid']
    result = db.userdata.update_one({'firebaseID': uid}, {'$set': {"priv": args['priv']}}, upsert=True)
    return result
