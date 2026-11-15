import random
from bin.models.team import AbstractPlayer
from modules.live_automated.controllers.common import run_rate_to_score, run_rate_to_score_with_mandatory


def fetch_raw_score_options(bat_rating, score_options=None):
    """ Raw score by aggression rating """

    if bat_rating <= 100:
        return [0]
    if bat_rating >= 2900:
        return [6]
    if bat_rating >= 2800:
        # 35 at 2800, 36 at 2900
        return run_rate_to_score(run_rate=0.01 * bat_rating + 7, scoring_options=[4, 6])
    if bat_rating >= 2500:
        # 31.25 at 2500, 35 at 2800
        return run_rate_to_score(bat_rating / 80, scoring_options=[2, 4, 6])
    if bat_rating >= 2400:
        # 30 at 2400, 31.25 at 2500
        return run_rate_to_score_with_mandatory(bat_rating / 80, scoring_options=[1, 2, 4, 6], mandatory=[4, 6])
    if bat_rating >= 2200:
        # 24 at 2200, 30 at 2400
        return run_rate_to_score_with_mandatory(0.03 * bat_rating - 42, mandatory=[4, 6])
    if bat_rating >= 2000:
        # 20 at 2000, 24 at 2200
        return run_rate_to_score_with_mandatory(0.02 * bat_rating - 20, mandatory=[4, 6])
    if bat_rating >= 1800:
        # 18 at 1800, 20 at 2000
        return run_rate_to_score_with_mandatory(bat_rating / 100, mandatory=[0, 1, 4, 6])
    if bat_rating >= 1500:
        # 10.5 at 1500, 18 at 1800
        return run_rate_to_score_with_mandatory(0.025 * bat_rating - 27, mandatory=[0, 1, 4, 6])
    if bat_rating >= 1400:
        # 7.5 at 1400, 10.5 at 1500
        return run_rate_to_score_with_mandatory(0.03 * bat_rating - 34.5, mandatory=[0, 1, 4, 6])
    # Beyond 1400 sixes are expected
    if score_options is None:
        score_options = [0, 1, 2, 4, 6]
    if bat_rating >= 1300:
        # 6 at 1300, 7.5 at 1400
        mandatory = [0, 1]
        if 4 in score_options:
            mandatory.append(4)
        if 6 in score_options:
            mandatory.append(6)
        return run_rate_to_score_with_mandatory(
            0.015 * bat_rating - 13.5,
            mandatory=mandatory,
            scoring_options=score_options
            )
    if bat_rating >= 1000:
        # 4.5 at 1000, 6 at 1300
        mandatory = [0, 1]
        if 4 in score_options:
            mandatory.append(4)
        if 6 in score_options:
            mandatory.append(6)
        return run_rate_to_score_with_mandatory(
            0.005 * bat_rating - 0.5,
            mandatory=mandatory,
            scoring_options=score_options
            )
    if True:
        # 0 at 100, 4.5 at 1000
        return run_rate_to_score_with_mandatory(
            0.005 * bat_rating - 0.5,
            mandatory=[0, 1],
            scoring_options=score_options
            )


def fetch_score_options(bat_rating, bowl_rating, score_options=None):
    if bat_rating >= 2900:
        return [6]
    elif bowl_rating >= 2900:
        return [0]
    elif bat_rating >= 2650 and bat_rating >= bowl_rating:
        return fetch_raw_score_options(bat_rating)
    elif bowl_rating >= 2650 and bowl_rating > bat_rating:
        if bat_rating >= 1400:
            return [0, 0, 1]
        return [0]
    elif bat_rating >= bowl_rating:
        return fetch_raw_score_options(bat_rating, score_options)
    else:
        return fetch_raw_score_options(2 * bat_rating - bowl_rating, score_options)


def fetch_wicket_threshold(bat_rating, bowl_rating, w_thresholds=None):
    if bat_rating >= 2900 and bowl_rating >= 2900:
        return 0.5
    if bat_rating >= 2650 and bat_rating > bowl_rating:
        return 20
    if bowl_rating <= 1000:
        return 20
    if bat_rating == bowl_rating:
        return 0.5
    if bowl_rating >= 2900 and bowl_rating > bat_rating:
        return 0
    if w_thresholds is None:
        w_thresholds = {
            1000: 1,
            bat_rating: 0.5,
            2900: 0
        }
    else:
        w_thresholds_1 = {}
        for i in w_thresholds.keys():
            w_thresholds_1[i] = w_thresholds[i]
        w_thresholds = {}
        for i in w_thresholds_1.keys():
            w_thresholds[int(i)] = w_thresholds_1[i]
    w_threshold_points = sorted(w_thresholds.items())
    if bowl_rating < int(w_threshold_points[0][0]):
        return 10
    if bowl_rating > int(w_threshold_points[-1][0]):
        return 0
    if bowl_rating in w_thresholds.keys():
        return w_thresholds[bowl_rating]
    for i in range(len(w_threshold_points) - 1):
        x1, y1 = w_threshold_points[i]
        x2, y2 = w_threshold_points[i + 1]
        x1, x2, y1, y2 = int(x1), int(x2), float(y1), float(y2)
        if x1 < bowl_rating and bowl_rating < x2:
            try:
                y = y1 + (y2 - y1) * (bowl_rating - x1) / (x2 - x1)
                return y
            except ZeroDivisionError:
                y = y1 + (y2 - y1) * (bowl_rating - x1) * (10 ** 7)
                return y
    return 0.5


def fetch_scorer(
        batter,
        nonstriker,
        bowler,
        chasing=False,
        to_win=0,
        to_balls=1
    ):

    # Default
    batter_score_options = [0, 1, 2, 3, 4, 6]
    b_w_threshold = 0.57
    extra = {
        "wide": 0,
        "no_ball": 0,
        "penalty": 0,
        "bye": 0,
        "run_in_wide": False
    } # 0 to disable extras. 0 if bat_rating >= 2200

    # The new objects
    bat_object1 = AbstractPlayer(batter)
    bat_object2 = AbstractPlayer(nonstriker)
    bowl_object = AbstractPlayer(bowler)

    bat_rating = bat_object1.get("rating_bat", 1800)
    bowl_rating = bowl_object.get("rating_bowl",  1800)
    try:
        bot_bowler = bowl_object.parent_team().ai()
    except AttributeError:
        bot_bowler = False

    # bat_score_options
    batter_score_options = fetch_score_options(
        bat_rating=bat_object1.aggression_rating(),
        bowl_rating=bowl_rating
    )

    # Wicket threshold
    b_w_threshold = fetch_wicket_threshold(
        bat_rating=bat_rating,
        bowl_rating=bowl_rating,
        w_thresholds=bat_object1.get("w_threshold")
    )

    # Extras - bye and leg bye
    if bat_rating == 1400:
        extra["bye"] = 0.1
    if bat_rating < 1400 and bat_rating > 1000:
        extra["bye"] = 0.1 * (bat_rating - 1000) / 400
    if bat_rating < 1800 and bat_rating > 1400:
        extra["bye"] = 0.1 * (1800 - bat_rating) / 400

    # Extras - wides, no-balls
    # Not if bowl rating exceeds 1800 as it is 1800 level expectation to avoid
    # Bot bowlers rated >= 1400 will not bowl wides or no-balls.
    # Not if bat rating exceeds 2200 as they will go after em
    # Wide is [0, 0.4] and no ball is [0, 0.1]
    if bat_rating < 2200 and bowl_rating < 1800:
        if bot_bowler:
            if bowl_rating < 1400:
                extra["wide"] = 0.001 * (1400 - bowl_rating)
            if bowl_rating < 1000:
                extra["wide"] = 0.4
        else:
            if bowl_rating < 1800:
                extra["wide"] = 0.0005 * (1800 - bowl_rating)
                extra["no_ball"] = 0.1 * (1800 - bowl_rating) / 800
            if bowl_rating < 1000:
                extra["wide"] = 0.4
                extra["no_ball"] = 0.1

    # Any player-specific options go here
    # End custom

    # In crunch chase
    if chasing:
        to_win_new = to_win - 1
        to_balls_new = to_balls - 1
        if to_win_new <= 6 * to_balls and to_win > 6 * to_balls_new:
            total_choices = len(batter_score_options)
            six_choices = batter_score_options.count(6)
            batter_score_options = [6]
            # wicket threshold
            if total_choices < 1 or six_choices < 1:
                batter_score_options = [0]
                b_w_threshold = 0
            else:
                b_w_threshold = b_w_threshold * six_choices / total_choices

    # finally
    return batter_score_options, b_w_threshold, extra
