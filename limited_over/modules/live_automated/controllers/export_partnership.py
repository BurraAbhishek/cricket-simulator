from bin.mongodb import mongolivematchclient


def export_partnership():
    partnership_collection = mongolivematchclient.get_live_partnership()
    l = list(partnership_collection.find())
    for i in l:
        del i["_id"]
    return l
