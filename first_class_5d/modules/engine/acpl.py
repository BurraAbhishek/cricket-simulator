from math import exp
from statistics import stdev, harmonic_mean
from bin.models.team import Team


class ConstrainedNumber():

    def __init__(self, value):
        if not isinstance(value, int) and not isinstance(value, float):
            raise TypeError("Cannot convert " + str(value) + " into a number.")
        self.value = value
        self.ulimit = value
        self.llimit = value

    def at_most(self, limit):
        self.ulimit = limit
        if limit < self.value:
            self.value = limit
        return self
    
    def at_least(self, limit):
        self.llimit = limit
        if limit > self.value:
            self.value = limit
        return self
    
    def as_percent(self):
        return str(self.value * 100) + "%"
    
    def for_harmonic(self):
        return self.value + (10 ** -7)
    
    def d(self):
        if isinstance(self.value, int):
            return int(self.value)
        return float(self.value)


class ColorEvaluationMetrics():

    def __init__(self) -> None:
        self._blunder_thresholds = [0.01, 0.05, 0.1]
        self._blunder_thresholds.sort()
        self._acpl_factor = 2000
        self.inaccuracy = 0
        self.mistake = 0
        self.blunder = 0
        self.acpl = 0
        self.inaccuracy_balls = []
        self.mistake_balls = []
        self.blunder_balls = []
        self.accuracy = 1
        self._winpercents = []
        self._loss = []
        self._weight = []
        self._lasteval = None
        self._wicket_eval = 1
        self._ball_count = 0
        self._wawa = []
        self._harmonicmeans = []
        self.rawloss = 0

    def export(self, name):
        return {
            "name": name,
            "inaccuracy": self.inaccuracy,
            "mistake": self.mistake,
            "blunder": self.blunder,
            "acpl": self.acpl * self._acpl_factor,
            "inaccuracy_balls": self.inaccuracy_balls,
            "mistake_balls": self.mistake_balls,
            "blunder_balls": self.blunder_balls,
            "accuracy": self.accuracy,
            "accuracypercent": self.accuracy * 100
        }
    
    def set_wicket_eval(self, value):
        if isinstance(value, int) or isinstance(value, float):
            self._wicket_eval = value
        
    def add_eval(self, value, ball_id: dict|None=None):
        if self._lasteval is None:
            self._lasteval = value
            return
        # Weights for weighted mean
        if self._lasteval > value:
            self._weight.append(stdev([self._lasteval, value]))
        else:
            self._weight.append(0)
        # Win percents
        wp = ConstrainedNumber(lossByWinPercents(self._lasteval, value)).at_least(0).at_most(1).d()
        self._winpercents.append(wp)
        # Classification
        loss = self._lasteval - value
        if loss > self._blunder_thresholds[2]:
            self.blunder += 1
            self.blunder_balls.append(ball_id)
        elif loss > self._blunder_thresholds[1]:
            self.mistake += 1
            self.mistake_balls.append(ball_id)
        elif loss > self._blunder_thresholds[0]:
            self.inaccuracy += 1
            self.inaccuracy_balls.append(ball_id)
        # set values
        self._lasteval = value

    def _wicket_eval_by_rating(self, your_rating, opponent_rating):
        rating_cap = 3000
        rdiff = your_rating - opponent_rating
        rval = ConstrainedNumber(3 * (rating_cap - rdiff) / (rating_cap)).at_least(0).at_most(6).d()
        return rval
    
    def wicket_eval_by_team(self, your_team, opponent_team):
        your_rating = Team(your_team).get_rating()
        opponent_rating = Team(opponent_team).get_rating()
        self.set_wicket_eval(self._wicket_eval_by_rating(your_rating, opponent_rating))

    def record_loss(self, score_int, dismissed=False, batting=False):
        self._ball_count += 1
        if dismissed and bool(score_int < 1):
            if batting:
                self.rawloss += 6 + self._wicket_eval
        else:
            if batting:
                self.rawloss += max(0, 6 - score_int)
            else:
                self.rawloss += score_int + self._wicket_eval

    def wa(self):
        if self._ball_count <= 0:
            return
        self.acpl = self.rawloss / (self._ball_count * (6 + self._wicket_eval))
        s = sum(self._weight)
        if s > 0:
            for i in range(0, len(self._winpercents)):
                self._wawa.append(self._winpercents[i] * self._weight[i] / s)
        else:
            self._wawa = [i / len(self._winpercents) for i in self._winpercents]
        for i in self._winpercents:
            self._harmonicmeans.append(i + (10 ** -7))
        harmonicwinpct = max(0, harmonic_mean(self._harmonicmeans) - (10 ** -7))
        wawawinpct = sum(self._wawa)
        self.accuracy = (wawawinpct + harmonicwinpct) * ((1 - self.acpl) ** 0.5) / 2
        # Win a perfect game
        if self.acpl == 0:
            self.accuracy = 1
        # Lose by a perfect game = play only wrong moves
        elif self.acpl == 1:
            self.accuracy = 0


def acpl(game):
    white_eval = ColorEvaluationMetrics()
    black_eval = ColorEvaluationMetrics()
    white_eval.add_eval(game["prediction"]["white"])
    black_eval.add_eval(game["prediction"]["black"])
    for i, e in enumerate(game["innings"]):
        for j in e["data"]:
            for k in j:
                ball_id = {
                    "inning": i,
                    "over": k["over"],
                    "ball_id": k["ball"]
                }
                white_eval.add_eval(k["evaluation"]["white"], ball_id)
                black_eval.add_eval(k["evaluation"]["black"], ball_id)
                if k["legal_delivery"]:
                    dismissed = bool(k["dismissed_batter"] is not None and k["dismissed_batter"] != "")
                    white_eval.record_loss(k["score_int"], dismissed, bool(e["batting_team"] == game["team1"]))
                    black_eval.record_loss(k["score_int"], dismissed, bool(e["batting_team"] == game["team2"]))
    # Max ACPL = 2000.
    white_eval.wa()
    black_eval.wa()
    evals = {
        "white": white_eval.export(Team(game["team1"]).name()),
        "black": black_eval.export(Team(game["team2"]).name())
    }
    return evals


def lossByWinPercents(before, after):
    if after >= before:
        return 1
    winDiff = before - after
    factor = 103.1668 * exp(-4 * winDiff) - 3.1668
    if factor >= 100:
        return 1
    if factor <= 0:
        return 0
    return factor / 100
