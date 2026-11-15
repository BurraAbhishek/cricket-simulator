from random import choice


commentary_data = {
    "0": [
        "Swing and a miss.",
        "The batter defends it off the back foot.",
        "The batter leaves it alone and lets it go through to the keeper.",
        "Straight at the stumps, the batter blocks it off.",
        "Pitched up outside the off stump and shaping away, the batter leaves this one alone.",
    ],
    "1": [
        "The batter tries to loft it towards deep square but it falls just short of the fielder. A run taken.",
        "Full and outside off, this is driven to long off for a single.",
        "Chipped away to square, the batters cross for a run.",
        "The batter chips it to long on for a single.",
        "The batter flicks it to deep mid-wicket for a single.",
        "The batter drills it to long off for a single.",
        "The batter drills it to long on and finds a fielder. They take a run.",
        "That was chipped to long off for a single.",
        "The batter pushes it through covers for a single.",
        "This is pushed past point for a single.",
        "This is hit to long on for a single."
    ],
    "2": [
        "The batter looks to go over cover but toe ends the shot. The ball falls in front of the fielder. Two runs taken.",
        "The batter slaps it wide of deep cover for two runs.",
        "The batter flicks it through mid-wicket for two runs.",
        "The batter punches through covers for a couple."
    ],
    "3": [
        ""
    ],
    "4": [
        #"Playing with the field now! This is full and outside off. The batter lofts it over covers and it races to the fence.",
        "The batter lofts it over covers and it races into the fence.",
        "The batter goes downtown and the ball races to the long off fence for a boundary.",
        "The batter goes down the track and it races to the fence like a tracer bullet.",
        "The batter shuffles in the crease and slashes it to deep cover for a boundary.",
        #"Slammed hard towards deep cover, it races to the fence.",
        #"The batter whacks it past deep mid-wicket for a boundary.",
        #"The batter scoops it over fine leg for a boundary.",
        "The batter hits it straight down the ground and it races to the fence like a tracer bullet.",
        #"The batter thrashes that through the off side for four!",
        #"Just short of the ropes! The batter tried to go for the helicopter shot but didn't get enough distance to send it straight out of the park. Instead, it fell just millimeters short of the ropes and it will be four instead."
    ],
    "5": [
        ""
    ],
    "6": [
        "The batter jumps down the track and smashes this over the bowler's head for a huge maximum.",
        "The batter stands tall and slaps it with a flat bat sending the ball over long on for a maximum.",
        "The batter picks the bones out of that, flat bats it down the ground and gets it over the long off fence for a biggie.",
        "The batter hammers this over long off for a biggie and it flies to the third tier of the stadium.",
        "This is just pummeled away into the leg side and it clears the fence for a maximum.",
        "That was slammed over long on and it goes all the way to the third tier of the stadium for a huge maximum.",
        "The batter flicks it past deep mid-wicket and it sails into the stands for a biggie.",
        # "The batter slogs it over deep square leg for a biggie."
        "This is swatted away to the leg side and it goes all the way into the third tier of the stadium for a maximum!",
        "This is swatted away to the off side and it goes all the way into the third tier of the stadium for a maximum!"
    ],
    "b": [
        ""
    ],
    "c": [
        "CAUGHT BEHIND! ",
        "TAKEN! "
    ],
    "lbw": [
        "The batter is trapped plumb in front. No spike on UltraEdge and Ball Tracking shows three reds.",
        "The batter misses and gets trapped plumb in front. No spike on UltraEdge and Ball Tracking shows three reds."
    ],
    "st": [
        ""
    ],
    "W": [
        ""
    ]
}


def fetch_commentary_data(score_string: str) -> str:
    return choice(commentary_data[score_string])
