from bin.mongoinserts.load_games import fetch_game


class Game():

    def __init__(self, game_data=None, clas=None, id=None) -> None:
        if game_data is None:
            self.data = fetch_game(clas, id)
        else:
            self.data = game_data

    def played(self):
        return not self.data.get("played", False)
    
    def terminated(self):
        return self.data.get("terminated", False)
    
    def winner(self):
        return self.data.get("winner")
    
    def loser(self):
        loser = ""
        if self.data.get("winner") == self.data.get("team1"):
            loser = self.data.get("team2")
        if self.data.get("winner") == self.data.get("team2"):
            loser = self.data.get("team1")
        return loser
    
    def innings_win(self):
        return bool(
            "innings" in self.data.get("margin")
            or str(self.data.get("margin", "")).lower() == "forfeit"
            or str(self.data.get("margin", "")).lower() == "walkover"
        )
    
    def double_forfeit(self):
        return bool(
            str(self.data.get("margin", "")).lower() == "double forfeit"
            or str(self.data.get("margin", "")).lower() == "double DQ"
        )
