import random
from bin.mongoinserts.load_teams import TOURNAMENT_TEAMS
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS


participants = dict()
for team in TOURNAMENT_TEAMS.keys():
    for member in TOURNAMENT_TEAMS[team].get("members"):
        participants[member["_id"]] = team


class TeamCollection():

    def __init__(self) -> None:
        self.__teams = TOURNAMENT_TEAMS

    def find(self):
        """ Get all teams """
        return self.__teams.keys()
    
    def group_teams(self):
        """ Returns Group1, Group2 """
        l1 = []
        l2 = []
        for i in self.find():
            team = self.get(i)
            if team.ai():
                l2.append(i)
            else:
                l1.append(i)
        return l1, l2
    
    def count(self):
        return len(self.__teams.keys())
    
    def any_ai(self):
        for i in self.find():
            team = self.get(i)
            if team.ai():
                return True
        return False
    
    def group_split(self):
        """ To split bots into separate group or not """
        if not TOURNAMENT_SETTINGS.get("bot_group", True):
            return False
        return self.any_ai()
    
    def count_groups(self):
        """ Returns count Group1, Group2 """
        c1 = 0
        c2 = 0
        for i in self.find():
            team = self.get(i)
            if team.ai():
                c2 += 1
            else:
                c1 += 1
        return c1, c2

    def get(self, team_name: str):
        team = Team(team_name)
        if team.validate():
            return team
        return None

    def find_one(self, team_name: str):
        return self.__teams.get(team_name)
    
    def fetch_player_map(self, player_id: str):
        team_id = participants.get(player_id)
        team = Team(team_id)
        player_data = AbstractPlayer(player_id)
        return {
            "_id": player_id,
            "player_name": player_data.name(),
            "team_id": team_id,
            "team_name": team.name(),
            "player_data": player_data
        }


class Team():

    def __init__(self, team_id: str):
        teams = TOURNAMENT_TEAMS
        self.__id = team_id
        self.__data = teams.get(team_id)

    def id(self):
        return self.__id

    def validate(self):
        return self.__data is not None
    
    def as_dict(self):
        return self.__data
    
    def ai(self):
        """used exclusively for BOT teams even though LLMs are also AI"""
        try:
            return self.__data.get("ai", bool("BOT" in self.__id))
        except AttributeError:
            return False

    def llm(self):
        try:
            return self.__data.get("llm", False)
        except AttributeError:
            return False
    
    def evaluator(self):
        return self.__data.get("evaluator", False)
        
    def classify(self):
        if self.llm():
            return "Large Language Model Team"
        if self.ai():
            return "Bot Team"
        return self.__data.get("classification", "National Side")
    
    def disqualified(self):
        return bool(
            self.__data.get("disqualified", False)
        )
    
    def headcount(self):
        try:
            return len(self.__data.get("members"))
        except TypeError:
            return 0
    
    def nominations(self):
        if self.headcount() <= 11:
            return {
                "captain": self.captain(),
                "default": self.lineup(),
                "substitutes": [],
                "replacements": {
                    "bat": None,
                    "pace": None,
                    "spin": None,
                    "all": None,
                    "keeper": None
                }
            }
        if self.__data.get("nomination") is None:
            lineup = self.lineup()
            # Most participating teams are balanced.
            return {
                "captain": self.captain(),
                "default": lineup[:11],
                "substitutes": lineup[11:],
                "replacements": {
                    "bat": lineup[11],
                    "pace": lineup[11],
                    "spin": lineup[11],
                    "all": lineup[11],
                    "keeper": lineup[11]
                }
            }
        submitted_data = self.__data.get("nomination")
        if submitted_data["scope"] == "replacement_only":
            lineup = self.lineup()
        else:
            lineup = submitted_data["mandatory"] + list(random.sample(submitted_data["optional"]))
        if submitted_data.get("replacement") is None:
            subs = lineup[11:15]
            replacement = {
                "bat": random.choice(subs),
                "pace": random.choice(subs),
                "spin": random.choice(subs),
                "all": random.choice(subs),
                "keeper": random.choice(subs)
            }
        else:
            replacement = submitted_data["replacement"]
        # Max 15 per ICC playing conditions
        subs = lineup[11:15]
        return {
            "captain": self.captain(),
            "default": lineup[:11],
            "substitutes": lineup[11:],
            "replacements": replacement
        }

    def name(self):
        return self.__data.get("name")
    
    def prefix(self):
        return self.__data.get("player_prefix", self.__id[-1])

    def lineup(self):
        if "player_lineup" in self.__data.keys():
            return self.__data["player_lineup"]
        return [i["_id"] for i in self.__data["members"]]
    
    def bowling_lineup(self, nominees=None):
        selection = "random"
        if "bowling_orders" in self.__data.keys():
            if len(self.__data["bowling_orders"]["bowlers"]) > 0:
                return self.__data["bowling_orders"]
            selection = self.__data["bowling_orders"].get("selection", "random")
        lineup = []
        for i in self.__data["members"]:
            if i.get("bowl", True):
                if nominees is None:
                    lineup.append(i["_id"])
                elif i["_id"] in nominees:
                    lineup.append(i["_id"])
        return {
            "selection": selection,
            "bowlers": lineup
        }
    
    def fielding_lineup(self, nominees=None):
        lineup = []
        for i in self.__data["members"]:
            if i.get("field", True):
                if nominees is None:
                    lineup.append(i["_id"])
                elif i["_id"] in nominees:
                    lineup.append(i["_id"])
        return lineup
    
    def abstract_name(self):
        return str("{{ " + self.__id + ".name }}")
    
    def find(self):
        return self.__data.get("members")

    def members(self):
        return self.__data.get("members")
    
    def captain(self):
        c = None
        for i in self.members():
            if i["captain"] is True:
                c = i["_id"]
        if c is not None:
            return c
        return self.find_one(0).id()
    
    def indexOf(self, member_id: str):
        prefix = self.get("player_prefix", self.id()[0])
        return int(member_id.split(prefix)[-1])
    
    def init_rating(self):
        return self.__data.get("rating")
    
    def aggression_rating(self):
        return self.__data.get("aggression_rating", self.init_rating())
    
    def get_rating(self):
        return self.__data.get("rating_glicko2").get("rating")
    
    def set_rating(self, rating_object):
        TOURNAMENT_TEAMS[self.__id]["rating_glicko2"] = rating_object
    
    def find_one(self, member_id: str | int):
        members = self.__data.get("members")
        if isinstance(member_id, str):
            for i in self.__data.get("members"):
                if i.get("_id") == member_id:            
                    return AbstractPlayer(i)
        if isinstance(member_id, int):
            return AbstractPlayer(members[member_id])

    def fetch_one(self, member_id: str | int, key: str):
        return self.find_one(member_id).get(key)
    
    def get(self, key):
        if self.__data is None:
            return None
        return self.__data.get(key)


class AbstractPlayer():

    def __init__(self, player: str | dict) -> None:
        if isinstance(player, dict):
            self.__data = player
            self.__id = player.get("_id")
        else:
            team = Team(participants.get(player))
            data: dict = team.find_one(player)
            self.__id = player
            self.__data = data

    def id(self) -> str:
        return self.__id
    
    def team(self):
        return Team(self.get("team"))

    def parent_team(self):
        return Team(self.parent_team_name())

    def parent_team_name(self):
        parent_team = self.__data.get("parent_team")
        if parent_team is None:
            return self.get("team")
        return parent_team

    def name(self) -> str:
        return self.__data.get("name")

    def ai(self) -> bool:
        """used exclusively for BOT teams even though LLMs are also AI"""
        return self.__data.get("ai", False)

    def llm(self) -> bool:
        return self.__data.get("llm", False)
    
    def disqualified(self):
        return bool(
            self.__data.get("disqualified", False)
        )

    def rating(self):
        ratings = [
            self.__data.get("rating_bat"),
            self.__data.get("rating_bowl"),
            self.__data.get("rating_field")
        ]
        am_rating = int(sum(ratings) / 3)
        if ratings[0] >= 2200 or ratings[1] >= 2200 or ratings[2] >= 2200:
            return max([] + ratings + [am_rating])
        return min([] + ratings + [am_rating])

    def aggression_rating(self):
        agg_rating = self.__data.get("rating_aggression")
        if agg_rating is None:
            return self.__data.get("rating_bat")
        return agg_rating

    def w_threshold(self, bowl_rating=1800):
        # 1 at 1000, 0 at 2900. If rating >= 2900 it is 0.5 at 2900
        if bowl_rating <= 1000:
            return 20
        bat_rating = self.__data.get("rating_bat")
        if bat_rating >= 2900:
            if bowl_rating < 2900:
                return 20
            return 0.5
        if bat_rating >= 2650:
            if bat_rating > bowl_rating:
                return 2.5
            if bat_rating == bowl_rating:
                return 0.5
            if bat_rating < bowl_rating:
                return 0.1
    
    def color(self, theme=None):
        if theme == "dark":
            return self.team().get("dark_color")
        if theme == "light":
            return self.team().get("light_color")
        return self.team().get("color")
    
    def flag(self):
        return self.team().get("flag")
    
    def abstract_name(self):
        return str("{{ " + self.__id + ".name }}")
    
    def bowler(self):
        return self.__data.get("bowler", True)
    
    def fielder(self):
        return self.__data.get("fielder", True)

    def flight(self):
        return self.__data.get("flight", False)

    def female(self):
        return self.__data.get("female", False)

    def rating_title(self):
        """ Similar to rating Titles """
        if not TOURNAMENT_SETTINGS.get("player_title", False):
            return {"id": "", "name": ""}
        # These player titles remain unchanged in this tournament.
        # rating Master -> Federation Master
        # rating Master is rating-Exclusive. Hence not used here to avoid copyright issues.
        if self.team().ai() and TOURNAMENT_SETTINGS.get("bot_title", False):
            return {"id": "BOT", "name": "Bot Player"}
        # GM "Norms". These are harder than the corresponding rating GM norms
        if self.get("rating_bat") >= 2500 and self.get("rating_bowl") >= 2500 and self.get("rating_field") >= 2500:
            return {"id": "GM", "name": "Grandmaster"}
        # IM "Norms". These are harder than the corresponding rating GM norms. Yes GM, not IM.
        if self.get("rating_bat") >= 2400 and self.get("rating_bowl") >= 2400 and self.get("rating_field") >= 2400:
            return {"id": "IM", "name": "International Master"}
        # FM: If any one rating 2300
        if self.get("rating_bat") >= 2300 or self.get("rating_bowl") >= 2300 or self.get("rating_field") >= 2300:
            return {"id": "FM", "name": "Federation Master"}
        # CM: If any one rating 2200
        if self.get("rating_bat") >= 2200 or self.get("rating_bowl") >= 2200 or self.get("rating_field") >= 2200:
            return {"id": "CM", "name": "Candidate Master"}
        # No title. In rating, as of 2026, <1400 Elo is unrated.
        return {"id": "", "name": "None"}
    
    def default_avatar(self):
        if self.llm():
            return "/images/default/abstract/llm.svg"
        elif self.ai():
            return "/images/default/abstract/bot.svg"
        return "/images/default/abstract/person.svg"

    def avatar(self):
        """Defaults to face"""
        avatar_switch = TOURNAMENT_SETTINGS.get("avatar", 0)
        if avatar_switch == 1:
            return self.__data.get("avatar0", self.default_avatar())
        elif avatar_switch == 2:
            return self.__data.get("face", self.default_avatar())
        else:
            return self.__data.get("avatar", self.default_avatar())
        
    def as_dict(self):
        return self.__data
    
    def get(self, key, default=None):
        if key == "nickname":
            return self.__data.get("nickname", self.name())
        if key == "avatar" or key == "avatar0" or key == "face":
            return self.avatar()
        return self.__data.get(key, default)
    
    def __getitem__(self, key):
        return self.get(key)

