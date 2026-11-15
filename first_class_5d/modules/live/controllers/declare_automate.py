import random


# Criteria for declaration
# min score 200
# 360 or 420 overs depending on the team.
# you - sum(opponent) > 200
# no batter in the 90s.

def can_declare(
        bat_team,
        bowl_team,
        first_bat_team,
        bat_score,
        bat_balls,
        bat_wickets, 
        bat1_runs, 
        bat2_runs, 
        curr_out, 
        net_score,
        ref_score,
        bat_rating,
        bowl_rating
        ):
    # Rated >= 2900
    if bat_rating >= 2900:
        if first_bat_team == bat_team:
            if bat_score >= 216:
                return True
            return False
        else:
            if bat_score >= 6:
                return True
            return False
    # Basic sanity check wickets < 10
    if bat_wickets >= 10:
        return False
    # Basic sanity check has enough score
    if bat_team == first_bat_team:
        if net_score < 200:
            return False
    else:
        if net_score > -200:
            return False
    # And has sufficient score to defend
    if bat_team != first_bat_team and bat_score <= 2 * ref_score + 1:
        return False
    elif bat_team != first_bat_team and bat_score <= 3 * ref_score and bat_balls < 1080:
        return False
    elif bat_team == first_bat_team and bat_score <= 2 * ref_score:
        return False
    # Rated >= 2650
    if bat_rating >= 2650:
        target_balls = 1800 - (0.6 * bat_rating)
        if bowl_rating <= 1000:
            target_balls = min(120, target_balls)
        if bat_balls >= target_balls:
            return True
        return False
    # Don't prolong matches
    if bat_balls >= 2160:
        return True
    # All other teams
    declare_threshold = 0.9
    if bat_score % 100 > 80:
        return False
    if bat1_runs % 100 > 90 or bat2_runs % 100 > 90:
        return False
    elif (bat1_runs > 100 and bat1_runs % 100 > 80) or (bat2_runs > 100 and bat2_runs % 100 > 80):
        return False
    # End of over
    if bat_balls % 6 > 0:
        return False
    # <=1000 Bowlers
    if bowl_rating <= 1000:
        target_balls = 2160
        if bat_rating >= 1800:
            target_balls = 120
        elif bat_rating >= 1600:
            target_balls = 180
        elif bat_rating >= 1500:
            target_balls = 240
        elif bat_rating >= 1400:
            target_balls = 360
        elif bat_rating >= 1100:
            target_balls = 980
        else:
            target_balls = 2160
        return False
    # Rating specific
    if bat_rating >= 1800 and abs(bat_rating - bowl_rating) <= 500:
        if bat_balls >= 720:
            return True
        return False
    # Specific
    # Broad
    if bat_rating >= 1100:
        # 20 at 2800, 30 at 2700 etc.
        target_balls = int((3000 - bat_rating) * 3 / 5)
        if bat_rating == 2899:
            target_balls = 60
        if bat_balls >= target_balls:
            return True
        return False
    if curr_out:
        declare_threshold *= 0.75
    submission = random.random() * random.random() * random.random()
    return submission > declare_threshold
