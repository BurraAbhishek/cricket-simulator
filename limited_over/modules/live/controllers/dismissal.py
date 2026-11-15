def fetch_dismissal_type(
        batting_team="",
        bowling_team="",
        batter="",
        bowler="",
        nonstriker="",
        bat_rating=1800,
        bowl_rating=1800,
        field_rating=2200
    ):
    
    default_wicket_types = ["b", "c", "lbw", "cw"]

    practical_wicket_types = [
        "b", "c", "cw", "lbw", "st",
        "b", "c", "cw", "lbw", "st",
        "b", "c", "cw", "lbw", "st",
        "b", "c", "cw", "lbw", "st",
        "b", "c", "cw", "lbw", "st",
        "b", "c", "cw", "lbw", "st",
        "b", "c", "cw", "lbw", "st",
        "b", "c", "cw", "lbw", "st",
        "runoutb0", "runoutk0", "runoutb1", "runoutk1",
        "runoutbr0", "runoutkr0", "runoutbr1", "runoutkr1"
    ] # repetition because random selection

    # Bare "runout" is not recommended for use.
    all_wicket_types = [
        "b",
        "c", "cw", "cb",
        "lbw",
        "st",
        "hitwicket",
        "runoutb0", "runoutk0", "runoutb1", "runoutk1", "runoutb2", "runoutk2",
        "runoutbr0", "runoutkr0", "runoutbr1", "runoutkr1", "runoutbr2", "runoutkr2"
        "obstructing",
        "timeout",
        "hittheballtwice",
        "retired"
    ]

    if batting_team == "" and bowling_team == "" and batter == "" and bowler == "":
        return default_wicket_types
    
    if bowl_rating >= 2800:
        return default_wicket_types
    
    if bowl_rating >= 2200 and field_rating < 2200:
        return ["b"]

    if bowl_rating >= 2200:
        return default_wicket_types
    
    return practical_wicket_types
