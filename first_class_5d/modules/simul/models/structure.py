from bin.models.team import Team
from bin.mongoinserts.load_games import fetch_game
from modules.index.common import render_score
from modules.stat.all_games import get_match_name
from modules.simul.common.timer import time_to_verbose, break_to_verbose


class Simul():

    def __init__(self, games, curr_clock=0):
        """ games: {clas, id} """
        self.games: list[SimulGame] = []
        self.clock = 0
        self.max_clock = 0
        self.complete = False
        for i in games:
            g = fetch_game(i["clas"], i["id"])
            component = SimulGame(g, curr_clock)
            self.games.append(component)
            self.max_clock = max(component.max_clock, self.max_clock)
        self.clock = curr_clock
        if self.clock > self.max_clock:
            self.clock = self.max_clock
        if self.clock >= self.max_clock:
            self.complete = True
        self.clock_verbose = time_to_verbose(self.clock)

    def render_data(self, playing=False):
        data = []
        for i in self.games:
            if not playing or not i.gameover:
                data.append(i.fetch())
        return data


class SimulGame():

    def __init__(self, game, curr_clock=0):
        self.team1 = game["team1"]
        self.team2 = game["team2"]
        self.team1_name = Team(game["team1"]).name()
        self.team2_name = Team(game["team2"]).name()
        self.winner = game["winner"]
        self.margin = game["margin"]
        self.follow_on = game["follow_on"]
        self.inning_count = len(game["innings"])
        self.name = get_match_name(game["_id"])
        self.data = []
        self.end_inning = [-1, -1, -1, -1]
        self.declarations = [False, False, False, False]
        self.curr_inning = 0
        self.curr_position = 0
        self.day = 1
        self.max_clock = 0
        self.clock = 0
        self.ball_clock = 40
        self.inning_break = 600
        self.lunch_break = 2400
        self.tea_break = 1200
        self.day_clock_limit = 28800
        self.session_breaks = [[], [], [], []]
        self.gameover = False
        self.inningbreak_duration = [self.inning_break] * 4
        try:
            self.engine_name = game["prediction"]["name"]
        except KeyError:
            self.engine_name = "DefaultEngine"
        if self.margin in ["Match Cancelled", "Walkover", "Disciplinary Forfeit"]:
            self.gameover = True
            return
        for i0, s0 in enumerate(game["sessions"]):
            if not s0["capture_end"]:
                ei = s0["end_inning"]
                eb = s0["end_ball"]
                if i0 % 3 == 0:
                    session_type = "sbreak_lunch"
                    session_duration = self.lunch_break
                if i0 % 3 == 1:
                    session_type = "sbreak_tea"
                    session_duration = self.tea_break
                if i0 % 3 == 2:
                    session_type = "sbreak_stumps"
                    session_duration = -1
                if i0 % 3 < 3:
                    self.session_breaks[ei].append({
                        "type": session_type,
                        "day": 1 + (i0 // 3),
                        "ball": eb,
                        "duration": session_duration
                    })
            else:
                if s0["end_inning"] < self.inning_count - 1:
                    if i0 % 3 == 0:
                        self.inningbreak_duration[s0["end_inning"]] = self.lunch_break
                    if i0 % 3 == 1:
                        self.inningbreak_duration[s0["end_inning"]] = self.tea_break
                    if i0 % 3 == 2:
                        self.inningbreak_duration[s0["end_inning"]] = -1
        for i, e in enumerate(game["innings"]):
            score = 0
            balls = 0
            wickets = 0
            self.declarations[i] = e["declared"]
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
                    ball["outcome"] = k["score"]
                    self.clock += self.ball_clock
                    ball["clock_end"] = self.clock
                    ball["type"] = "ball"
                    self.curr_position += 1
                    self.data.append(ball)
                    for b in self.session_breaks[i]:
                        if b["ball"] == k["_id"]:
                            if b["duration"] == -1:
                                ibreak = {"type": b["type"], "clock_start": self.clock, "clock_end": b["day"] * self.day_clock_limit}
                                self.clock = b["day"] * self.day_clock_limit
                            else:
                                ibreak = {"type": b["type"], "clock_start": self.clock, "clock_end": self.clock + b["duration"]}
                                self.clock += b["duration"]
                            self.data.append(ibreak)
                            self.curr_position += 1
            self.end_inning[i] = self.curr_position - 1
            if i < self.inning_count - 1:
                if self.inningbreak_duration[i] == -1:
                    ibreak = {"type": "ibreak_stumps", "clock_start": self.clock, "clock_end": b["day"] * self.day_clock_limit}
                    self.clock = b["day"] * self.day_clock_limit
                else:
                    ibreak = {"type": "ibreak", "clock_start": self.clock, "clock_end": self.clock + self.inningbreak_duration[i]}
                    self.clock += self.inningbreak_duration[i]
                self.data.append(ibreak)
                self.curr_position += 1
        self.max_clock = self.clock
        if len(self.data) < 1:
            self.max_clock = self.clock - self.ball_clock
        self.clock = curr_clock
        if self.clock > self.max_clock:
            self.clock = self.max_clock
        self.load_curr_position()
        if self.curr_position >= self.end_inning[self.inning_count - 1]:
            self.curr_position = self.end_inning[self.inning_count - 1]
            self.gameover = True

    def load_curr_position(self):
        for i, e in enumerate(self.data):
            if self.clock <= e["clock_end"]:
                self.curr_position = i
                return
        self.curr_position = self.end_inning[1]

    def status(self):
        if self.curr_position >= self.end_inning[self.inning_count - 1]:
            if self.winner is not None and self.winner != "":
                s = Team(self.winner).name()
                s += " are victorious"
            else:
                s = str(self.margin)
        elif self.data[self.curr_position]["type"] == "ibreak":
            if self.clock < self.data[self.curr_position]["clock_end"]:
                diff_clock = self.data[self.curr_position]["clock_end"] - self.clock
                s = "Innings break (" + break_to_verbose(diff_clock) + " remaining)"
            else:
                s = "Live"
        elif self.data[self.curr_position]["type"] == "ibreak_stumps":
            if self.clock < self.data[self.curr_position]["clock_end"]:
                diff_clock = self.data[self.curr_position]["clock_end"] - self.clock
                s = "Innings break (next day coverage in " + break_to_verbose(diff_clock) + ")"
            else:
                s = "Live"
        elif self.data[self.curr_position]["type"] == "sbreak_lunch":
            if self.clock < self.data[self.curr_position]["clock_end"]:
                diff_clock = self.data[self.curr_position]["clock_end"] - self.clock
                s = "Lunch break (" + break_to_verbose(diff_clock) + " remaining)"
            else:
                s = "Live"
        elif self.data[self.curr_position]["type"] == "sbreak_tea":
            if self.clock < self.data[self.curr_position]["clock_end"]:
                diff_clock = self.data[self.curr_position]["clock_end"] - self.clock
                s = "Tea break (" + break_to_verbose(diff_clock) + " remaining)"
            else:
                s = "Live"
        elif self.data[self.curr_position]["type"] == "sbreak_stumps":
            if self.clock < self.data[self.curr_position]["clock_end"]:
                diff_clock = self.data[self.curr_position]["clock_end"] - self.clock
                s = "Stumps (next day coverage begins in " + break_to_verbose(diff_clock) + ")"
            else:
                s = "Live"
        else:
            s = "Live"
        return s
    
    def init_position(self):
        return {
            "name": self.name,
            "size": 2,
            "data": [
                {
                    "side": 0,
                    "bat": self.team1_name,
                    "bowl": self.team2_name,
                    "score": 0,
                    "wickets": 0,
                    "balls": 0,
                    "score_formatted": self.format_score(0, 0, 0),
                    "declare": False,
                    "played": True
                },
                {
                    "side": 1,
                    "bat": self.team2_name,
                    "bowl": self.team1_name,
                    "score": 0,
                    "wickets": 0,
                    "balls": 0,
                    "score_formatted": self.format_score(0, 0, 0),
                    "declare": False,
                    "played": False
                }
            ],
            "eval": {
                "white": 0.5,
                "draw": 0,
                "black": 0.5,
                "eval_verbose": "0.0"
            },
            "status": "Live",
            "engine_name": self.engine_name
        }
    
    def fetch(self):
        if self.margin == "Match Cancelled":
            data = self.init_position()
            data["data"][0]["played"] = False
            data["eval"]["eval_verbose"] = "Ø"
            data["status"] = "Match Cancelled"
            return data
        if self.margin.lower() in ["walkover", "disciplinary forfeit"]:
            data = self.init_position()
            data["data"][0]["played"] = False
            if self.winner == self.team1:
                data["eval"] = {
                    "white": 1,
                    "draw": 0,
                    "black": 0,
                    "eval_verbose": "1-0"
                }
            if self.winner == self.team2:
                data["eval"] = {
                    "white": 0,
                    "draw": 0,
                    "black": 1,
                    "eval_verbose": "0-1"
                }
            data["status"] = str(
                Team(self.winner).name()
                + " are victorious"
            )
            return data
        if self.clock < self.ball_clock:
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
            score2 = 0
            balls2 = 0
            wickets2 = 0
            score3 = 0
            balls3 = 0
            wickets3 = 0
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
            elif ball["inning"] == 2:
                ball0 = self.data[self.end_inning[0]]
                ball1 = self.data[self.end_inning[1]]
                score0 = ball0["total_score"]
                balls0 = ball0["total_balls"]
                wickets0 = ball0["total_wickets"]
                score1 = ball1["total_score"]
                balls1 = ball1["total_balls"]
                wickets1 = ball1["total_wickets"]
                score2 = ball["total_score"]
                balls2 = ball["total_balls"]
                wickets2 = ball["total_wickets"]
            elif ball["inning"] == 3:
                ball0 = self.data[self.end_inning[0]]
                ball1 = self.data[self.end_inning[1]]
                ball2 = self.data[self.end_inning[2]]
                score0 = ball0["total_score"]
                balls0 = ball0["total_balls"]
                wickets0 = ball0["total_wickets"]
                score1 = ball1["total_score"]
                balls1 = ball1["total_balls"]
                wickets1 = ball1["total_wickets"]
                score2 = ball2["total_score"]
                balls2 = ball2["total_balls"]
                wickets2 = ball2["total_wickets"]
                score3 = ball["total_score"]
                balls3 = ball["total_balls"]
                wickets3 = ball["total_wickets"]
            data = {
                "name": self.name,
                "size": ball["inning"] + 1,
                "data": [
                    {
                        "side": 0,
                        "bat": self.team1_name,
                        "bowl": self.team2_name,
                        "score": score0,
                        "wickets": wickets0,
                        "balls": balls0,
                        "declare": False,
                        "played": True
                    },
                    {
                        "side": 1,
                        "bat": self.team2_name,
                        "bowl": self.team1_name,
                        "score": score1,
                        "wickets": wickets1,
                        "balls": balls1,
                        "declare": False,
                        "played": bool(ball["inning"] >= 1)
                    }
                ],
                "eval": ball["evaluation"],
                "status": "Live",
                "engine_name": ball["evaluation"]["name"]
            }
            if ball["inning"] >= 2:
                if self.follow_on:
                    data["data"].append(
                        {
                            "side": 1,
                            "bat": self.team2_name,
                            "bowl": self.team1_name,
                            "score": score2,
                            "wickets": wickets2,
                            "balls": balls2,
                            "declare": False,
                            "played": True
                        }
                    )
                    data["data"].append(
                        {
                            "side": 0,
                            "bat": self.team1_name,
                            "bowl": self.team2_name,
                            "score": score3,
                            "wickets": wickets3,
                            "balls": balls3,
                            "declare": False,
                            "played": bool(ball["inning"] >= 3)
                        }
                    )
                else:
                    data["data"].append(
                        {
                            "side": 0,
                            "bat": self.team1_name,
                            "bowl": self.team2_name,
                            "score": score2,
                            "wickets": wickets2,
                            "balls": balls2,
                            "declare": False,
                            "played": True
                        }
                    )
                    data["data"].append(
                        {
                            "side": 1,
                            "bat": self.team2_name,
                            "bowl": self.team1_name,
                            "score": score3,
                            "wickets": wickets3,
                            "balls": balls3,
                            "declare": False,
                            "played": bool(ball["inning"] >= 3)
                        }
                    )
            for i in range(0, ball["inning"]):
                data["data"][i]["declare"] = self.declarations[i]
            if self.data[self.curr_position]["type"] == "ibreak":
                i = ball["inning"]
                data["data"][i]["declare"] = self.declarations[i]
            if self.data[self.curr_position]["type"] == "ibreak_stumps":
                i = ball["inning"]
                data["data"][i]["declare"] = self.declarations[i]
            data["status"] = self.status()
            for i in data["data"]:
                i["score_formatted"] = self.format_score(
                    i["score"],
                    i["wickets"],
                    i["declare"]
                )
            return data
        
    def next(self):
        max_position = self.end_inning[self.inning_count - 1]
        if self.curr_position < max_position:
            self.curr_position += 1
    
    def previous(self):
        if self.curr_position > -1:
            self.curr_position -= 1

    def format_score(self, score, wickets, declared=False):
        return render_score(score, wickets, declared)
