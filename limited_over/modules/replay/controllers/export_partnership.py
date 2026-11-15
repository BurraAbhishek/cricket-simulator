from bin.mongodb import mongoclient, mongoreplayclient


def export_partnership():
    partnership_collection = mongoreplayclient.get_replay_partnership()
    l = list(partnership_collection.find())
    for i in l:
        del i["_id"]
    return l
