import json
from django.contrib.staticfiles import finders
from collections import OrderedDict


# Database names
TEAM_DB_NAME = "fb14_teams"
TOURNAMENT_DB_NAME = "fb14_t20_e25"
CURRENT_MATCH_DB = "currently_playing"
REPLAY_DB = "match_replay"

# Tournament DB collection names
TOURNAMENT_TEAMS = "fb14_team_list"
TOURNAMENT_SUMMARY = "fb14_summary"
TOURNAMENT_GROUPSTAGE = "fb14_groupstage"
TOURNAMENT_KNOCKOUT = "fb14_knockout"
TOURNAMENT_PLAYERMAP = "fb14_member_mapping"

# current match DB collection names
CURRENT_TEAMS = "current_teams"
CURRENT_INNINGS1_PROGRESSION = "current_innings1_progression"
CURRENT_INNINGS1_BATTERS = "current_innings1_batters"
CURRENT_INNINGS1_BOWLERS = "current_innings1_bowlers"
CURRENT_INNINGS1_COMMENTARY = "current_innings1_commentary"
CURRENT_INNINGS1_PARTNERSHIP = "current_innings1_partnership"
CURRENT_INNINGS2_PROGRESSION = "current_innings2_progression"
CURRENT_INNINGS2_BATTERS = "current_innings2_batters"
CURRENT_INNINGS2_BOWLERS = "current_innings2_bowlers"
CURRENT_INNINGS2_COMMENTARY = "current_innings2_commentary"
CURRENT_INNINGS2_PARTNERSHIP = "current_innings2_partnership"
# Likewise for innings 3 and 4 in case of test match
CURRENT_MATCH_DETAILS = "match_details"
CURRENT_MATCH_DETAILS0 = "match_details0"
CURRENT_MATCH_DETAILS1 = "match_details1"
CURRENT_MATCH_DETAILS2 = "match_details2"


class DictCollection():

    def __init__(
            self,
            name: str,
            replay: bool=True,
            live: bool=False
            ) -> None:
        self.__name = name
        self.__replay = replay
        if replay:
            self.__live = False
        else:
            self.__live = live
        self.create()

    def create(self):
        if not self.__replay and not self.__live:
            return
        if self.__replay:
            match_path = finders.find('temp/replay/' + self.__name + '.json')
            if match_path is None:
                mp = str(finders.searched_locations[0])
                f = open(mp + "/temp/replay/" + self.__name + '.json', "w")
                f.write('{}')
                f.close()
                match_path = finders.find('temp/replay/' + self.__name + '.json')
            match_data_serialized = open(match_path)
            match_data = OrderedDict(json.load(match_data_serialized))
            self.__data = match_data
        elif self.__live:
            match_path = finders.find('temp/live/' + self.__name + '.json')
            if match_path is None:
                mp = str(finders.searched_locations[0])
                f = open(mp + "/temp/live/" + self.__name + '.json', "w")
                f.write('{}')
                f.close()
                match_path = finders.find('temp/live/' + self.__name + '.json')
            match_data_serialized = open(match_path)
            match_data = OrderedDict(json.load(match_data_serialized))
            self.__data = match_data

    def commit(self):
        if self.__replay:
            match_path = finders.find('temp/replay/' + self.__name + '.json')
        elif self.__live:
            match_path = finders.find('temp/live/' + self.__name + '.json')
        match_data_serialized = open(match_path, "w+")
        json.dump(self.__data, match_data_serialized)

    def find_one(self, key) -> dict:
        return self.__data.get(str(key))
    
    def find(self) -> list:
        result = []
        for i in self.__data.keys():
            result.append(self.find_one(i))
        return result
    
    def insert_one(self, data: dict):
        _id = data.get("_id")
        if _id is None:
            return
        _id = str(_id)
        if _id not in self.__data.keys():
            data["_id"] = str(data["_id"])
            self.__data[_id] = data
        self.commit()

    def update_one(self, condition: dict, update: dict):
        condition_id = condition.get("_id")
        if condition_id is None:
            return
        shortlist = self.__data.get(str(condition_id))
        if update.get("$set") is not None:
            update_data: dict = update.get("$set")
            for i in update_data.keys():
                shortlist[i] = update_data[i]
        if update.get("$inc") is not None:
            update_data: dict = update.get("$inc")
            for i in update_data.keys():
                new_update_value = shortlist[i] + update_data[i]
                shortlist[i] = new_update_value
        if update.get("$push") is not None:
            update_data: dict = update.get("$push")
            for i in update_data.keys():
                shortlist[i].append(update_data[i])
        self.commit()

    def test(self):
        pass


class ReplayDictCollection(DictCollection):

    def __init__(self, name: str) -> None:
        super().__init__(name, True, False)


class LiveDictCollection(DictCollection):

    def __init__(self, name: str) -> None:
        super().__init__(name, False, True)


def replay_db_get_collection(collection_name: str) -> DictCollection:
    return ReplayDictCollection(collection_name)

def replay_db_find_one(collection_name: str, data_id):
    collection = replay_db_get_collection(collection_name)
    return collection.find_one(data_id)

def replay_db_insert_one(collection_name: str, data) -> None:
    collection = replay_db_get_collection(collection_name)
    _id = data.get("_id")
    if _id is None:
        return
    if replay_db_find_one(collection_name, _id) is None:
        collection.insert_one(data)

def live_db_get_collection(collection_name: str) -> DictCollection:
    return LiveDictCollection(collection_name)

def live_db_find_one(collection_name: str, data_id):
    collection = live_db_get_collection(collection_name)
    return collection.find_one(data_id)

def live_db_insert_one(collection_name: str, data) -> None:
    collection = live_db_get_collection(collection_name)
    _id = data.get("_id")
    if _id is None:
        return
    if live_db_find_one(collection_name, _id) is None:
        collection.insert_one(data)
