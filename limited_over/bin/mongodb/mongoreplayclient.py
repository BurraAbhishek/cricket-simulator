from bin.mongodb import mongoclient
from bin.mongodb.mongoclient import DictCollection as Collection


def get_replay_innings(x):
    if x == 1 or x == 2:
        return x
    else:
        live_details = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_MATCH_DETAILS
        ).find_one(1)
        return live_details["innings"]


def get_mid_commentary(inning=0) -> Collection:
    i = get_replay_innings(inning)
    if i == 1:
        comment_table = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_INNINGS1_COMMENTARY
        )
    elif i == 2:
        comment_table = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_INNINGS2_COMMENTARY
        )
    return comment_table


def get_batter_stat(inning=0) -> Collection:
    i =  get_replay_innings(inning)
    if i == 1:
        table = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_INNINGS1_BATTERS
        )
    elif i == 2:
        table = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_INNINGS2_BATTERS
        )
    return table


def get_bowler_stat(inning=0) -> Collection:
    i = get_replay_innings(inning)
    if i == 1:
        table = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_INNINGS1_BOWLERS
        )
    elif i == 2:
        table = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_INNINGS2_BOWLERS
        )
    return table


def get_past_balls(inning=0) -> Collection:
    i = get_replay_innings(inning)
    if i == 1:
        table = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_INNINGS1_PROGRESSION
        )
    elif i == 2:
        table = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_INNINGS2_PROGRESSION
        )
    return table


def get_replay_partnership(inning=0) -> Collection:
    i = get_replay_innings(inning)
    if i == 1:
        table = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_INNINGS1_PARTNERSHIP
        )
    elif i == 2:
        table = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_INNINGS2_PARTNERSHIP
        )
    return table
