from bin.models.team import AbstractPlayer


class Batter(AbstractPlayer):

    def __init__(self, player_id) -> None:
        self.runs = 0
        self.balls = 0
        self.scoring = [0] * 7
        self.dismissed = False
        self.dismissal = None
        super().__init__(player_id)

    def __getitem__(self, key):
        if key == "runs":
            return self.runs
        if key == "balls":
            return self.balls
        if key == "fours":
            return self.scoring[4]
        if key == "sixes":
            return self.scoring[6]
        if key == "dismissed":
            return self.dismissed
        if key == "dismissal":
            return self.dismissal
        return super().__getitem__(key)

    def as_dict(self):
        batter_dict = {
            "_id": self.id(),
            "runs": self.runs,
            "balls": self.balls,
            "scoring": self.scoring,
            "dismissed": self.dismissed
        }
        if self.dismissed is True:
            batter_dict["dismissal"] = self.dismissal
        return batter_dict
    
    def load_from(self, data: dict):
        self.runs = data.get("runs", 0)
        self.balls = data.get("balls", 0)
        self.scoring = data.get("scoring", [0] * 7)
        self.dismissed = data.get("dismissed", False)
        self.dismissal = data.get("dismissal", None)

    def strike_rate(self):
        if self.balls == 0:
            return 0
        return 100 * self.runs / self.balls


class Bowler(AbstractPlayer):

    def __init__(self, player_id) -> None:
        self.balls = 0
        self.dots = 0
        self.maidens = 0
        self.runs = 0
        self.wickets = 0
        super().__init__(player_id)

    def __getitem__(self, key):
        if key == "balls":
            return self.balls
        if key == "dots":
            return self.dots
        if key == "maidens":
            return self.maidens
        if key == "runs":
            return self.runs
        if key == "wickets":
            return self.wickets
        return super().__getitem__(key)

    def as_dict(self):
        bowler_dict = {
            "_id": self.id(),
            "balls": self.balls,
            "dots": self.dots,
            "maidens": self.maidens,
            "runs": self.runs,
            "wickets": self.wickets
        }
        return bowler_dict
    
    def load_from(self, data: dict):
        self.balls = data.get("balls", 0)
        self.dots = data.get("dots", 0)
        self.maidens = data.get("maidens", 0)
        self.runs = data.get("runs", 0)
        self.wickets = data.get("wickets", 0)
    
    def economy(self):
        if self.balls == 0:
            if self.runs > 0:
                return 36
            return 0
        return 6 * self.runs / self.balls


class AbstractFielder(AbstractPlayer):

    def __init__(self, player_id) -> None:
        super().__init__(player_id)