class Ball():

    def __init__(self, ball_data: dict) -> None:
        self.__data = ball_data

    def as_dict(self):
        return self.__data

    def is_valid(self):
        return self.__data.get("legal_delivery", True)
    
    def score_bat(self):
        return self.__data.get("score_bat", self.__data.get("score_int"))
    
    def score_int(self):
        return self.__data.get("score_int")
    
    def extra_bowler(self):
        return int(
            self.score_bat()
            + self.__data.get("wide")
            + self.__data.get("no_ball")
            + self.__data.get("penalty")
        )
    
    def wicket(self):
        return bool(self.__data.get("dismissed_batter") != "")
    
    def get(self, key):
        return self.__data.get(key)


class Over():

    def __init__(self, over_data) -> None:
        self.__data = over_data
        self.__score = 0
        self.__ball = 0
        self.__wicket = 0
        self.__maiden = True
        if len(self.__data) > 0:
            for i in self.__data:
                self.add_ball(i)

    def as_list(self):
        return [ball.as_dict() for ball in self.__data]

    def balls(self):
        return self.__data
    
    def legal_balls(self):
        return [i for i in self.balls() if i.is_valid()]
    
    def add_ball(self, ball: Ball):
        if not isinstance(ball, Ball):
            ball = Ball(ball)
        self.__data.append(ball)
        self.__score += ball.score_int()
        self.__ball += int(ball.is_valid())
        self.__wicket += int(ball.wicket())
        if ball.extra_bowler() > 0:
            self.__maiden = False

    def maiden(self):
        return self.__maiden
    
    def six_sixes(self):
        if self.__ball < 6:
            return False
        legal_balls = self.legal_balls()
        for i in legal_balls:
            if i.score_bat < 6:
                return False
        return True


class Inning():

    def __init__(self) -> None:
        pass


class Game():

    def __init__(self) -> None:
        pass