from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from bin.mongoinserts.cachebase import get_item
from bin.mongoinserts.team.bots import load_bot_team
from bin.mongoinserts.team.team9C import fetch_carl


def load_teams_from_scratch():
    teams = {
        "CARLBOT": fetch_carl(),
        "BOT2800": load_bot_team(2800),
    }
    return teams


def load_teams():
    x = get_item("teams")
    if x is not None:
        return x
    return load_teams_from_scratch()


TOURNAMENT_TEAMS = load_teams()


class Team():

    def __init__(self, team_name: str):
        teams = TOURNAMENT_TEAMS
        self.__data = teams.get(team_name)

    def validate(self):
        return self.__data is not None
    
    def find(self):
        return self.__data.get("members")
    
    def find_one(self, member_id: str | int):
        members = self.__data.get("members")
        if isinstance(member_id, int):
            return members[member_id]
        else:
            for i in members:
                if i["_id"] == member_id:
                    return i
                
    def get(self, key: str):
        if key == "nickname" and self.__data.get("nickname") is None:
            return self.__data.get("name")
        if key == "avatar" or key == "avatar0" or key == "face":
            avatar_switch = TOURNAMENT_SETTINGS.get("avatar", 0)
            if avatar_switch == 1:
                return self.__data.get("avatar0")
            elif avatar_switch == 2:
                return self.__data.get("face")
            else:
                return self.__data.get("avatar")
        return self.__data.get(key)

    def fetch_one(self, member_id: str | int, key: str):
        members = self.__data.get("members")
        member: dict | None = None
        if isinstance(member_id, int):
            member = members[member_id]
        else:
            for i in members:
                if i["_id"] == member_id:
                    member = i
                    break
        if member is None:
            return None
        if key == "nickname" and member.get("nickname") is None:
            return member.get("name")
        if key == "avatar" or key == "avatar0" or key == "face":
            avatar_switch = TOURNAMENT_SETTINGS.get("avatar", 0)
            if avatar_switch == 1:
                return member.get("avatar0", member.get("avatar"))
            elif avatar_switch == 2:
                return member.get("face", member.get("avatar"))
            else:
                return member.get("avatar")
        return member.get(key)


class TeamCollection():

    def __init__(self) -> None:
        self.__teams = TOURNAMENT_TEAMS

    def get(self, team_name: str):
        team = Team(team_name)
        if team.validate():
            return team
        return None

    def find_one(self, team_name: str):
        return self.__teams.get(team_name)
    
    def fetch_player_map(self, player_id: str):
        for i in self.__teams.keys():
            name = self.__teams.get(i).get("name")
            members = self.__teams.get(i).get("members")
            for j in members:
                if j["_id"] == player_id:
                    return {
                        "_id": player_id,
                        "player_name": j["name"],
                        "team_id": i,
                        "team_name": name,
                        "player_data": j
                    }
