from bin.mongodb import mongoclient
from bin.mongodb.mongoclient import DictCollection as Collection


def get_mid_commentary() -> Collection:
    live_details = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(1)
    if live_details["innings"] == 1:
        comment_table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS1_COMMENTARY
        )
    elif live_details["innings"] == 2:
        comment_table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS2_COMMENTARY
        )
    elif live_details["innings"] == 3:
        comment_table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS3_COMMENTARY
        )
    elif live_details["innings"] == 4:
        comment_table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS4_COMMENTARY
        )
    return comment_table


def get_batter_stat() -> Collection:
    live_details = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(1)
    if live_details["innings"] == 1:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS1_BATTERS
        )
    elif live_details["innings"] == 2:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS2_BATTERS
        )
    elif live_details["innings"] == 3:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS3_BATTERS
        )
    elif live_details["innings"] == 4:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS4_BATTERS
        )
    return table


def get_bowler_stat() -> Collection:
    live_details = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(1)
    if live_details["innings"] == 1:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS1_BOWLERS
        )
    elif live_details["innings"] == 2:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS2_BOWLERS
        )
    elif live_details["innings"] == 3:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS3_BOWLERS
        )
    elif live_details["innings"] == 4:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS4_BOWLERS
        )
    return table


def get_past_balls() -> Collection:
    live_details = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(1)
    if live_details["innings"] == 1:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS1_PROGRESSION
        )
    elif live_details["innings"] == 2:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS2_PROGRESSION
        )
    elif live_details["innings"] == 3:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS3_PROGRESSION
        )
    elif live_details["innings"] == 4:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS4_PROGRESSION
        )
    return table


def get_live_partnership() -> Collection:
    live_details = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(1)
    if live_details["innings"] == 1:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS1_PARTNERSHIP
        )
    elif live_details["innings"] == 2:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS2_PARTNERSHIP
        )
    elif live_details["innings"] == 3:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS3_PARTNERSHIP
        )
    elif live_details["innings"] == 4:
        table = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS4_PARTNERSHIP
        )
    return table
