from bin.models.team import Team
from bin.mongoinserts.load_games import fetch_game
from modules.stat.all_games import get_match_name


class Simul():

    def __init__(self, games, curr_position=0):
        """ games: {clas, id} """
        self.games = []
        self.max_position = 0
        self.clock = 0
        self.max_clock = 0
        self.complete = False
        for i in games:
            g = fetch_game(i["clas"], i["id"])
            component = SimulGame(g, curr_position)
            self.games.append(component)
            self.max_position = max(component.end_inning[-1], self.max_position)
            self.max_clock = max(component.max_clock, self.max_clock)
        self.curr_position = curr_position
        if self.curr_position > self.max_position:
            self.curr_position = self.max_position
        if self.clock > self.max_clock:
            self.clock = self.max_clock
        if self.clock >= self.max_clock:
            self.complete = True

    def render_data(self):
        data = []
        for i in self.games:
            data.append(i.fetch())
        return data


class SimulGame():

    def __init__(self, game, curr_position=0):
        self.team1 = game["team1"]
        self.team2 = game["team2"]
        self.team1_name = Team(game["team1"]).name()
        self.team2_name = Team(game["team2"]).name()
        self.winner = game["winner"]
        self.margin = game["margin"]
        self.name = get_match_name(game["_id"])
        self.end_inning = [0, 0]
        self.curr_inning = 0
        self.curr_position = 1
        self.ball_clock = 40
        self.inning_break = 600
        self.max_clock = 1080
        self.clock = 0
        self.data = [{"type": "start", "clock_start": 0, "clock_end": self.clock}]
        for i, e in enumerate(game["innings"]):
            score = 0
            balls = 0
            wickets = 0
            for j in e["data"]:
                for k in j:
                    score += k["score_int"]
                    balls += (1 if k["legal_delivery"] else 0)
                    wickets += (1 if k["dismissed_batter"] is not None and k["dismissed_batter"] != "" else 0)
                    ball = dict(k)
                    ball["inning"] = i
                    ball["batting_team"] = e["batting_team"]
                    ball["bowling_team"] = e["bowling_team"]
                    ball["total_score"] = score
                    ball["total_balls"] = balls
                    ball["total_wickets"] = wickets
                    ball["clock_start"] = self.clock
                    self.clock += self.ball_clock
                    ball["clock_end"] = self.clock
                    ball["type"] = "ball"
                    self.curr_position += 1
                    self.data.append(ball)
            self.end_inning[i] = self.curr_position - 1
            if i == 0:
                ibreak = {"type": "ibreak", "clock_start": self.clock, "clock_end": self.clock + self.inning_break}
                self.clock += self.inning_break
                self.data.append(ibreak)
                self.curr_position += 1
        self.max_clock = self.clock
        # self.load_curr_position()
        self.curr_position = curr_position
        if self.curr_position > self.end_inning[-1]:
            self.curr_position = self.end_inning[-1]

    def load_curr_position(self):
        for i, e in enumerate(self.data):
            if self.clock < e["clock_end"]:
                self.curr_position = i
                return
    
    def init_position(self):
        return {
            "position": 0,
            "name": self.name,
            "data": [
                {
                    "side": 0,
                    "bat": self.team1_name,
                    "bowl": self.team2_name,
                    "score": 0,
                    "wickets": 0,
                    "balls": 0
                },
                {
                    "side": 1,
                    "bat": self.team2_name,
                    "bowl": self.team1_name,
                    "score": 0,
                    "wickets": 0,
                    "balls": 0
                }
            ],
            "eval": {
                "white": 0.5,
                "draw": 0,
                "black": 0.5,
                "eval_verbose": "0.0"
            },
            "status": "Live"
        }
    
    def fetch(self):
        if self.curr_position < 1 or self.clock < self.ball_clock:
            return self.init_position()
        else:
            ball = self.data[self.curr_position]
            if ball["type"] != "ball":
                ball = self.data[self.curr_position - 1]
            score0 = 0
            balls0 = 0
            wickets0 = 0
            score1 = 0
            balls1 = 0
            wickets1 = 0
            if ball["inning"] == 0:
                score0 = ball["total_score"]
                balls0 = ball["total_balls"]
                wickets0 = ball["total_wickets"]
            elif ball["inning"] == 1:
                ball0 = self.data[self.end_inning[0]]
                score0 = ball0["total_score"]
                balls0 = ball0["total_balls"]
                wickets0 = ball0["total_wickets"]
                score1 = ball["total_score"]
                balls1 = ball["total_balls"]
                wickets1 = ball["total_wickets"]
            return {
                "position": self.curr_position,
                "name": self.name,
                "data": [
                    {
                        "side": 0,
                        "bat": self.team1_name,
                        "bowl": self.team2_name,
                        "score": score0,
                        "wickets": wickets0,
                        "balls": balls0
                    },
                    {
                        "side": 1,
                        "bat": self.team2_name,
                        "bowl": self.team1_name,
                        "score": score1,
                        "wickets": wickets1,
                        "balls": balls1
                    }
                ],
                "eval": ball["evaluation"],
                "status": self.status()
            }

    def status(self):
        if self.curr_position >= self.end_inning[1]:
            if self.winner is not None and self.winner != "":
                s = Team(self.winner).name()
                s += " are victorious"
            else:
                s = str(self.margin)
        elif self.data[self.curr_position]["type"] == "ibreak":
            if self.clock < self.data[self.curr_position]["clock_end"]:
                s = "Innings break"
        else:
            s = "Live"
        return s
        
    def next(self):
        max_position = self.end_inning[-1]
        if self.curr_position < max_position:
            self.curr_position += 1
    
    def previous(self):
        if self.curr_position > 0:
            self.curr_position -= 1