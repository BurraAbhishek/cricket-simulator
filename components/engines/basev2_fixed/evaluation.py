from math import inf, log, exp, e
from bin.models.team import Team


class BaseLimitedOverCricketEngine():

    def __init__(self, game) -> None:
        self.name = "BaseRFEngine v12 HCE"
        self.game = game
        self.team1 = game["team1"]
        self.team2 = game["team2"]
        self.max_inning = 2
        self.winner = game["winner"]
        self.score0 = 0
        self.balls0 = 0
        self.wickets0 = 0
        self.score1 = 0
        self.balls1 = 0
        self.wickets1 = 0
        self.whitestopeval = 0.5
        self.blackstopeval = 0.5
        self.target = game["target"]
        self.curr_inning = 0
        self.draw_factor = 0
        self.gamestart = False
        self.gameover = False
        self.out = False
        self.team1model = []
        self.team2model = []
        self.max_wickets = game["wickets"]
        self.ballindex1 = 0
        self.ballindex2 = 0
        self._load_models()

    def max_balls(self):
        return self.game["overs"] * 6
    
    def last_ball_id(self):
        return self.game["innings"][1]["data"][-1][-1]["_id"]
    
    def _load_models(self):
        self.team1model = [3] * self.max_balls()
        self.team2model = [3] * self.max_balls()

    def perfect_game(self):
        # Corrects evaluations of perfect games.
        # Return 0 for team independence
        team1 = Team(self.team1)
        team2 = Team(self.team2)
        if bool(
            team1.init_rating() >= 2900
            and team2.init_rating() < 2900
        ):
            return 1
        if bool(
            team1.init_rating() < 2900
            and team2.init_rating() >= 2900
        ):
            return -1
        return 0

    def predict_score1(self):
        # base = sum(self.team1model) * self.wicket_factor(self.wickets0)
        base = sum(self.team1model[:self.ballindex1])
        try:
            base += sum(self.team1model[self.ballindex1:]) * self.wicket_factor(self.wickets0)
        except IndexError:
            pass
        return base
        # return int(sum(self.team1model))

    def predict_score2(self):
        # base = sum(self.team2model) * self.wicket_factor(self.wickets1)
        base = sum(self.team2model[:self.ballindex2])
        try:
            base += sum(self.team2model[self.ballindex2:]) * self.wicket_factor(self.wickets1)
        except IndexError:
            pass
        return base
        # return int(sum(self.team2model))
    
    def wicket_factor(self, wicket=0):
        return ((11 - wicket) / (self.max_wickets + 1)) ** 1.5
    
    def _raw_predict(self):
        white_wt = self.predict_score1()
        black_wt = self.predict_score2()
        white_eval = 1 / (1 + e ** (-0.015 * (white_wt - black_wt)))
        black_eval = 1 - white_eval
        #white_eval = white_wt / (white_wt + black_wt)
        #black_eval = black_wt / (white_wt + black_wt)
        return {
            "white": white_eval,
            "draw": 0,
            "black": black_eval
        }

    def predict(self):
        if not self.gamestart:
            return {
                    "white": 0.5,
                    "draw": 0,
                    "black": 0.5,
                    "eval": 0.0,
                    "eval_verbose": "0.0"
                }
        if self.perfect_game() == 1:
            if self.curr_inning == 0:
                wdl = {
                    "white": 0.999,
                    "draw": 0,
                    "black": 0.001,
                    "eval": inf,
                    "eval_verbose": self.white_mates_in(10 + (self.max_balls() - self.balls0))
                }
            elif self.curr_inning == 1:
                wdl = {
                    "white": 0.999,
                    "draw": 0,
                    "black": 0.001,
                    "eval": inf,
                    "eval_verbose": self.white_mates_in(10 - self.wickets1)
                }
        elif self.perfect_game() == -1:
            if self.curr_inning == 0:
                if self.wickets0 == 10:
                    wdl = {
                        "white": 0.001,
                        "draw": 0,
                        "black": 0.999,
                        "eval": -inf,
                        "eval_verbose": self.black_mates_in(1)
                    }
                else:
                    wdl = {
                        "white": 0.001,
                        "draw": 0,
                        "black": 0.999,
                        "eval": -inf,
                        "eval_verbose": self.black_mates_in(11 - self.wickets0)
                    }
            elif self.curr_inning == 1:
                wdl = {
                    "white": 0.001,
                    "draw": 0,
                    "black": 0.999,
                    "eval": -inf,
                    "eval_verbose": self.black_mates_in(1)
                }
        else:
            if self.curr_inning >= self.max_inning - 1:
                wdl = self.predict_chase()
                # wdl = self._raw_predict()
            else:
                wdl = self._raw_predict()
            wdl["eval"] = self.wdl_to_eval(wdl["white"], wdl["draw"], wdl["black"])
            try:
                wdl["eval_verbose"] = str(int(wdl["eval"] * 10) / 10)
            except OverflowError:
                # wdl["eval"] = self.wdl_to_eval(wdl["white"], wdl["draw"], wdl["black"])
                # wdl["eval_verbose"] = str(int(wdl["eval"] * 10) / 10)
                pass
            if self.score0 == self.score1:
                if self.curr_inning == 1 or self.wickets0 == 10 or self.balls0 == self.max_balls:
                    wdl = {
                        "white": 0.001,
                        "draw": 0,
                        "black": 0.999,
                        "eval": -inf,
                        "eval_verbose": self.black_mates_in(1)
                    }
            if wdl["eval"] >= 0.1 and wdl["white"] < 1:
                wdl["eval_verbose"] = "+" + wdl["eval_verbose"]
            if wdl["white"] > 0.999:
                wdl["white"] = 0.999
                wdl["black"] = 0.001
            if wdl["black"] > 0.999:
                wdl["black"] = 0.999
                wdl["white"] = 0.001
        if not self.gamestart:
            wdl["eval"] = 0.0
            wdl["eval_verbose"] = "0.0"
        if self.gameover:
            if self.winner == self.team1:
                wdl = {
                    "white": 1,
                    "draw": 0,
                    "black": 0,
                    "eval": inf,
                    "eval_verbose": "1-0"
                }
            elif self.winner == self.team2:
                wdl = {
                    "white": 0,
                    "draw": 0,
                    "black": 1,
                    "eval": -inf,
                    "eval_verbose": "0-1"
                }
            else:
                wdl = {
                    "white": 0,
                    "draw": 1,
                    "black": 0,
                    "eval": 0.0,
                    "eval_verbose": "½-½"
                }
        return wdl
    
    def record_event(self, ball):
        self.gamestart = True
        if self.curr_inning == self.max_inning - 1 and ball["_id"] == self.last_ball_id():
            self.gameover = True
        if self.curr_inning == 0:
            self.score0 += ball["score_int"]
            self.balls0 += (1 if ball["legal_delivery"] else 0)
            self.wickets0 += (1 if ball["dismissed_batter"] is not None and ball["dismissed_batter"] != "" else 0)
            self.add_outcome(ball)
        if self.curr_inning == 1:
            self.score1 += ball["score_int"]
            self.balls1 += (1 if ball["legal_delivery"] else 0)
            if ball["dismissed_batter"] is not None and ball["dismissed_batter"] != "":
                self.wickets1 += 1
                self.out = True
            self.add_outcome(ball, chasing=True)
    
    def add_outcome(self, ball, chasing=False):
        if chasing:
            try:
                self.team2model[self.ballindex2] = ball.get("score_int", self.team2model[self.ballindex2])
            except IndexError:
                self.team2model.append(ball.get("score_int", 0))
            self.ballindex2 += 1
        else:
            try:
                self.team1model[self.ballindex1] = ball.get("score_int", self.team1model[self.ballindex1])
            except IndexError:
                self.team1model.append(ball.get("score_int", 0))
            self.ballindex1 += 1


    def predict_chase(self):
        wdl = {
            "white": 0.0,
            "draw": 0.0,
            "black": 0.0,
            "eval": 0.0,
            "eval_verbose": ""
        }
        to_win = self.target - self.score1
        to_balls = self.max_balls() - self.balls1
        to_wickets = self.max_wickets - self.wickets1
        try:
            required_rate = 6 * to_win / to_balls
        except ZeroDivisionError:
            required_rate = 0 if to_win < 1 else self.target * 6
        # start_required_rate = 6 * self.target / self.max_balls()
        # 1. Immediate termination boundary overrides
        if to_win <= 1:
            wdl["white"] = 0
            wdl["draw"] = 0
            wdl["black"] = 1
            wdl["eval_verbose"] = self.black_mates_in(1)
            return wdl
        if required_rate > 36:
            wdl["white"] = 1
            wdl["draw"] = 0
            wdl["black"] = 0
            wdl["eval_verbose"] = self.white_mates_in(min(to_balls, to_wickets))
            return wdl
        if to_win <= 0:
            wdl["black"], wdl["white"] = 0.999, 0.001
            return wdl
        if to_balls <= 0 or to_wickets <= 0:
            if to_win == 1: # Tie criteria
                wdl["draw"] = 1.0
            else:
                wdl["white"], wdl["black"] = 0.999, 0.001
            return wdl
        # 2. Derive combined resource capacities 
        # Wickets are exponentially more valuable as they deplete
        wicket_resource = (to_wickets / self.max_wickets) ** 2.5
        ball_resource = to_balls / self.max_balls()
        total_resources_left = 0.5 * (wicket_resource + ball_resource)
        # 3. Calculate pressure index (Required runs vs Leftover resources)
        # Scaled against what was expected at the start of the innings
        expected_runs_for_resources = self.target * total_resources_left
        if expected_runs_for_resources == 0:
            pressure = 1.0
        else:
            pressure = to_win / expected_runs_for_resources
        # 4. Standardize probabilities using a logistics sigmoid curve
        margin = 1.0 - pressure
        black_win_prob = 1.0 / (1.0 + exp(-3.5 * margin))
        # 5. Scaling probabilities to WDL scale
        wdl["black"] = max(0.001, min(0.999, black_win_prob))
        wdl["white"] = 1.0 - wdl["black"] 
        # 6. Scaling with respect to evaluation at run chase.
        # Only makes sense if the eval isn't 0.0 to begin the chase
        if self.whitestopeval > self.blackstopeval:
            # white has advantage - use white metrics
            if wdl["white"] <= wdl["black"]:
                wdl["white"] = 2 * wdl["white"] * self.whitestopeval
            else:
                slope = 2 * (1 - self.whitestopeval)
                intercept = 1 - slope
                wdl["white"] = slope * wdl["white"] + intercept
            wdl["white"] = max(0.001, min(0.999, wdl["white"]))
            wdl["black"] = 1 - wdl["white"]
        if self.blackstopeval > self.whitestopeval:
            # black has advantage - use black metrics
            if wdl["black"] <= wdl["white"]:
                wdl["black"] = 2 * wdl["black"] * self.blackstopeval
            else:
                slope = 2 * (1 - self.blackstopeval)
                intercept = 1 - slope
                wdl["black"] = slope * wdl["black"] + intercept
            wdl["black"] = max(0.001, min(0.999, wdl["black"]))
            wdl["white"] = 1 - wdl["black"]
        return wdl

    def increment_inning(self):
        if self.curr_inning < self.max_inning - 1:
            evald = self.evaluate()
            self.whitestopeval = evald["white"]
            self.blackstopeval = evald["black"]
            self.curr_inning += 1
    
    def evaluate(self):
        return self.predict()
    
    def evaluate_json_standard(self):
        evaluation = self.predict()
        evaluation["name"] = self.name
        try:
            evaluation["w1"] = self.predict_score1()
            evaluation["b1"] = self.predict_score2()
        except ZeroDivisionError:
            pass
        if "eval_verbose" not in evaluation.keys():
            eval_value = self.wdl_to_eval(
                evaluation["white"],
                evaluation["draw"],
                evaluation["black"]
            )
            evaluation["eval_verbose"] = str(int(round(eval_value * 10)) / 10)
        elif evaluation["eval_verbose"] is None or evaluation["eval_verbose"] == "":
            eval_value = self.wdl_to_eval(
                evaluation["white"],
                evaluation["draw"],
                evaluation["black"]
            )
            evaluation["eval_verbose"] = str(int(round(eval_value * 10)) / 10)
        try:
            del evaluation["eval"]
        except TypeError:
            pass
        return evaluation

    def white_mates_in(self, m):
        return "#" + str(m)
    
    def black_mates_in(self, m):
        return "#-" + str(m)

    def wdl_to_eval(self, white, draw, black):
        if white == black:
            return 0
        if white == 0 and draw == 1 and black == 0:
            return 0
        if white == 1 and draw == 0 and black == 0:
            return inf
        if white == 0 and draw == 0 and black == 1:
            return -inf
        # Using Tangent
        # return tan((white - black) * pi / 2)
        # Using log
        try:
            return log((white + draw / 2) / (black + draw / 2)) / 0.368208
        except ValueError:
            return -100
