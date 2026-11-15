from django import forms
from bin.mongodb import mongoclient


class PlayerField(forms.ChoiceField):

    def __init__(self, team_id: str) -> None:
            team = mongoclient.fetch_team(team_id).find()
            choices = []
            for i in team:
                choices.append((i["_id"], i["name"]))
            super().__init__(choices=choices)


class GamePlayerField(PlayerField):

    def __init__(self, position: int) -> None:
            live_details = mongoclient.live_db_get_collection(
                mongoclient.CURRENT_MATCH_DETAILS
            ).find_one(1)
            if position == 1:
                super().__init__(live_details["bat"])
            elif position == 2:
                super().__init__(live_details["bowl"])
            else:
                raise ValueError("Position must be either 1 or 2")
        

class OptionalGamePlayerField(forms.ChoiceField):

    def __init__(self, position: int) -> None:
            live_details = mongoclient.live_db_get_collection(
                mongoclient.CURRENT_MATCH_DETAILS
            ).find_one(1)
            if position == 1:
                team = mongoclient.fetch_team(live_details["bat"]).find()
                choices = [(None, "")]
                for i in team:
                    choices.append((i["_id"], i["name"]))
                super().__init__(choices=choices, required=False)
            elif position == 2:
                team = mongoclient.fetch_team(live_details["bowl"]).find()
                choices = [(None, "")]
                for i in team:
                    choices.append((i["_id"], i["name"]))
                super().__init__(choices=choices, required=False)
            else:
                raise ValueError("Position must be either 1 or 2")