from bin.mongoinserts.groupstage import update_gs


def get_qe():
    gs = update_gs(None)
    qualified = []
    eliminated = []
    for i in gs:
        if i["status"] == 1:
            qualified.append({
                "week": len(i["results"]),
                "team": i["_id"]
            })
        elif i["status"] == -1:
            eliminated.append({
                "week": len(i["results"]),
                "team": i["_id"]
            })
    return qualified, eliminated


QUALIFIED, ELIMINATED = get_qe()
