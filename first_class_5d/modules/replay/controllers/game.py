from bin.mongodb import mongoclient


def nextGameStage():
    # Fetch!
    live_details = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS1
    )
    game_stage = live_details.find_one(1)["replay_stage"]
    nbInnings = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS2
    ).find_one(2)["nbInnings"]
    # 1 - 1st inning start comment
    # 2 - 1st inning
    # 3 - 1st inning end comment
    # 4 - 2nd inning start comment
    # 5 - 2nd inning
    # 6 - 2nd inning end comment (+ result if limited overs)
    if game_stage < 3 * nbInnings:
        live_details.update_one(
            {
                "_id": 1,
            },
            {
                "$inc": {
                    "replay_stage": 1
                }
            }
        )
    elif game_stage == 3 * nbInnings:
        live_details.update_one(
                    {
                        "_id": 1,
                    },
                    {
                        "$set": {
                            "replay_stage": 0
                        }
                    }
                )
