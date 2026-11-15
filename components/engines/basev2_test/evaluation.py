from math import inf, log, exp
from bin.models.team import Team


class BaseRFTestCricketEngine():

    def __init__(self, game) -> None:
        self.name = "BaseRFEngine v12 HCE"
        self.game = game
        self.team1 = game["team1"]
        self.team2 = game["team2"]
        self.followon = game["follow_on"]
        self.max_inning = len(game["innings"])
        self.winner = game["winner"]
        self.margin = game["margin"]
        self.score0 = 0
        self.balls0 = 0
        self.wickets0 = 0
        self.score1 = 0
        self.balls1 = 0
        self.wickets1 = 0
        self.score2 = 0
        self.balls2 = 0
        self.wickets2 = 0
        self.score3 = 0
        self.balls3 = 0
        self.wickets3 = 0
        self.curr_inning = 0
        self.draw_factor = 0.998
        self.gamestart = False
        self.gameover = False
        self.team1model = []
        self.team2model = []
        self.max_wickets = game["wickets"]
        self.ballindex1 = 0
        self.ballindex2 = 0
        self.chase_eval = None
        self._load_models()

    def max_balls(self):
        max_ball = 0
        for i in self.game["innings"]:
            for j in i["data"]:
                max_ball += len(j)
        return max(2700, max_ball)
    
    def last_ball_id(self):
        return self.game["innings"][self.max_inning - 1]["data"][-1][-1]["_id"]
    
    def _load_models(self):
        self.team1model = [0.5] * 540
        self.team2model = [0.5] * 540

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
        base = int(sum(self.team1model) / 2) * self.wicket_factor(self.wickets0)
        if self.followon:
            base += int(sum(self.team1model) / 2) * self.wicket_factor(self.wickets3)
        else:
            base += int(sum(self.team1model) / 2) * self.wicket_factor(self.wickets2)
        return base
        # return int(sum(self.team1model))

    def predict_score2(self):
        base = int(sum(self.team2model) / 2) * self.wicket_factor(self.wickets1)
        if self.followon:
            base += int(sum(self.team2model) / 2) * self.wicket_factor(self.wickets2)
        else:
            base += int(sum(self.team2model) / 2) * self.wicket_factor(self.wickets3)
        return base
        # return int(sum(self.team2model))
    
    def wicket_factor(self, wicket=0):
        return ((11 - wicket) / (self.max_wickets + 1)) ** 1.5
    
    def _raw_predict(self):
        remaining_balls = self.max_balls() - self.ballindex1 - self.ballindex2
        draw_wt = (self.draw_factor) ** (remaining_balls)
        inverse_draw_wt = 1 - draw_wt
        white_wt = self.predict_score1()
        black_wt = self.predict_score2()
        denominator = white_wt + black_wt
        try:
            white_eval = white_wt * inverse_draw_wt / denominator
            black_eval = black_wt * inverse_draw_wt / denominator
            if white_eval < 0.001:
                diff = 0.001 - white_eval
                white_eval = 0.001
                black_eval = black_eval - diff
            if black_eval < 0.001:
                diff = 0.001 - black_eval
                black_eval = 0.001
                white_eval = white_eval - diff
        except ZeroDivisionError:
            white_eval = 0.5 - (draw_wt / 2)
            black_eval = 0.5 - (draw_wt / 2)
        return {
            "white": white_eval,
            "draw": draw_wt,
            "black": black_eval,
        }
    
    def _raw_predict_chase(self):
        remaining_balls = self.max_balls() - self.ballindex1 - self.ballindex2
        draw_wt = (self.draw_factor) ** (remaining_balls)
        inverse_draw_wt = 1 - draw_wt
        if self.followon:
            target = 1 + self.score1 + self.score2 - self.score0
        else:
            target = 1 + self.score0 + self.score2 - self.score1
        remaining_score = target - self.score3
        if remaining_score <= 0:
            if self.followon:
                return {
                    "white": 0.998,
                    "draw": 0.001,
                    "black": 0.001
                }
            else:
                return {
                    "white": 0.001,
                    "draw": 0.001,
                    "black": 0.998
                }
        elif remaining_score == 1:
            if self.followon:
                return {
                    "white": inverse_draw_wt,
                    "draw": draw_wt,
                    "black": 0
                }
            else:
                return {
                    "white": 0,
                    "draw": draw_wt,
                    "black": inverse_draw_wt
                }        # return self._raw_predict()
        if self.chase_eval is None:
            self.chase_eval = self._raw_predict()
            return self.chase_eval
        # 1. Calculate resources remaining
        wickets_left = 10 - self.wickets3
        completion_ratio = self.score3 / target
        # Calculate how many runs are needed per remaining wicket
        avg_runs_per_remaining_wicket = remaining_score / max(1, wickets_left)
        # 2. Compute the smooth blend factor using a sigmoid curve
        # Inflection point at 3.0 runs per wicket, with a steepness factor of 1.5
        k = 1.5
        x0 = 3.0
        sigmoid_blend = 1 / (1 + exp(-k * (avg_runs_per_remaining_wicket - x0)))
        # 3. Calculate the raw underlying wicket factor
        raw_wicket_factor = self.wicket_factor(
            self.wickets3
        )
        # 4. Smoothly blend the penalty: 
        # If remaining runs per wicket are very low, sigmoid_blend -> 0, making wicket_pressure_penalty -> 1.0
        # If remaining runs per wicket are high, sigmoid_blend -> 1, making wicket_pressure_penalty -> raw_wicket_factor
        wicket_pressure_penalty = (1.0 - sigmoid_blend) + (sigmoid_blend * raw_wicket_factor)
        if self.followon:
            chase_eval_white = self.chase_eval["white"] + draw_wt / 2
            white_wt = chase_eval_white + ((1 - chase_eval_white) * completion_ratio)
            white_wt = white_wt * wicket_pressure_penalty
            black_wt = 1 - white_wt - (draw_wt / 2)
        else:
            chase_eval_black = self.chase_eval["black"] + draw_wt / 2
            black_wt = chase_eval_black + ((1 - chase_eval_black) * completion_ratio)
            black_wt = black_wt * wicket_pressure_penalty
            white_wt = 1 - black_wt - (draw_wt / 2)
        # Ensure weights remain mathematically valid before normalization
        white_wt = max(0.001, white_wt)
        black_wt = max(0.001, black_wt)
        white_eval = white_wt * inverse_draw_wt / (white_wt + black_wt)
        black_eval = black_wt * inverse_draw_wt / (white_wt + black_wt)
        # Clip outputs safely within your engine boundaries
        if white_eval < 0.001:
            diff = 0.001 - white_eval
            white_eval = 0.001
            black_eval = max(0.001, black_eval - diff)
        if black_eval < 0.001:
            diff = 0.001 - black_eval
            black_eval = 0.001
            white_eval = max(0.001, white_eval - diff)
        return {
            "white": white_eval,
            "draw": draw_wt,
            "black": black_eval,
        }

    def predict(self):
        if not self.gamestart:
            return {
                    "white": 0.498,
                    "draw": 0.004,
                    "black": 0.498,
                    "eval": 0.0,
                    "eval_verbose": "0.0"
                }
        if self.perfect_game() == 1:
            if self.curr_inning == 0:
                wdl = {
                    "white": 0.996,
                    "draw": 0.002,
                    "black": 0.002
                }
                wdl["eval"] = self.wdl_to_eval(0.996, 0.002, 0.002)
                wdl["eval_verbose"] = "+" + str(int(wdl["eval"] * 10) / 10)
                # Innings declaration
                if self.score0 >= 216:
                    wdl = {
                        "white": 0.998,
                        "draw": 0.001,
                        "black": 0.001,
                        "eval": inf,
                        "eval_verbose": self.white_mates_in(20)
                    }
            elif self.curr_inning == 1:
                wdl = {
                    "white": 0.998,
                    "draw": 0.001,
                    "black": 0.001,
                    "eval": inf,
                    "eval_verbose": self.white_mates_in(10 + (10 - self.wickets1))
                }
            elif self.curr_inning == 2:
                wdl = {
                    "white": 0.998,
                    "draw": 0.001,
                    "black": 0.001,
                    "eval": inf,
                    "eval_verbose": self.white_mates_in(10 - self.wickets2)
                }
        elif self.perfect_game() == -1:
            if self.curr_inning == 0:
                wdl = {
                    "white": 0.001,
                    "draw": 0.001,
                    "black": 0.998,
                    "eval": -inf,
                    "eval_verbose": self.black_mates_in(11 + (10 - self.wickets0))
                }
            elif self.curr_inning == 1:
                wdl = {
                    "white": 0.001,
                    "draw": 0.001,
                    "black": 0.998,
                    "eval": -inf,
                    "eval_verbose": self.black_mates_in(10 + (1 - self.balls1))
                }
            elif self.curr_inning == 2:
                wdl = {
                    "white": 0.001,
                    "draw": 0.001,
                    "black": 0.998,
                    "eval": -inf,
                    "eval_verbose": self.black_mates_in(10 - self.wickets2)
                }
        else:
            if self.curr_inning == 3:
                wdl = self._raw_predict_chase()
            else:
                wdl = self._raw_predict()
            wdl["eval"] = self.wdl_to_eval(wdl["white"], wdl["draw"], wdl["black"])
            wdl["eval_verbose"] = str(int(wdl["eval"] * 10) / 10)
            if wdl["eval"] >= 0.1 and wdl["white"] < 1:
                wdl["eval_verbose"] = "+" + wdl["eval_verbose"]
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
            elif str(self.margin).lower() == "double forfeit":
                wdl["eval_verbose"] = "Ø"
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
            self.wickets1 += (1 if ball["dismissed_batter"] is not None and ball["dismissed_batter"] != "" else 0)
            self.add_outcome(ball, chasing=True)
        if self.curr_inning == 2:
            self.score2 += ball["score_int"]
            self.balls2 += (1 if ball["legal_delivery"] else 0)
            self.wickets2 += (1 if ball["dismissed_batter"] is not None and ball["dismissed_batter"] != "" else 0)
            self.add_outcome(ball, chasing=self.followon)
        if self.curr_inning == 3:
            self.score3 += ball["score_int"]
            self.balls3 += (1 if ball["legal_delivery"] else 0)
            self.wickets3 += (1 if ball["dismissed_batter"] is not None and ball["dismissed_batter"] != "" else 0)
            self.add_outcome(ball, chasing=bool(not self.followon))
    
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

    def increment_inning(self):
        if self.curr_inning < self.max_inning:
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
        return log((white + draw / 2) / (black + draw / 2)) / 0.368208
