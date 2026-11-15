from random import choice
from bin.models.team import AbstractPlayer


def init_commentary_data():
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
            "The batter looks to go over deep cover but toe ends the shot. The ball falls in front of the fielder. Three runs taken.",
            "The batter looks to go over deep square but toe ends the shot. The ball falls in front of the fielder. Three runs taken."
        ],
        "4": [
            "Playing with the field now! This is full and outside off. The batter lofts it over covers and it races to the fence.",
            "The batter lofts it over covers and it races into the fence.",
            "The batter goes downtown and the ball races to the long off fence for a boundary.",
            "The batter goes down the track and it races to the fence like a tracer bullet.",
            "The batter shuffles in the crease and slashes it to deep cover for a boundary.",
            "The batter whacks it past deep mid-wicket and it goes all the way for four.",
            "The batter hits it straight down the ground and it races to the fence like a tracer bullet."
        ],
        "5": [
            ""
        ],
        "6": [
            "The batter jumps down the track and smashes this over the bowler's head for a huge maximum.",
            "The batter stands tall and slaps it with a flat bat sending the ball over long on for a maximum.",
            "The batter picks the bones out of that, flat bats it down the ground and gets it over the long off fence for a biggie.",
            "The batter hammers this over long off and it flies to the stands for a biggie.",
            "This is just pummeled away into the leg side and it clears the fence for a maximum.",
            "That was slammed over long on and it goes all the way to the stands for a maximum.",
            "The batter flicks it past deep mid-wicket and it sails into the stands for a biggie.",
            "This is swatted away to the leg side and it goes all the way into the stands for a maximum!",
            "This is swatted away to the off side and it goes all the way into the stands for a maximum!"
        ],
        "b": [
            "CHOPPED ON! The batter tries to flick it away but it nips back in enough to catch the inside edge before crashing back into the stumps.",
            "The batter tries to smash it over deep mid-wicket but misses. The ball sneaks beneath the bat and crashes into the stumps.",
            "It is bowled straight as an arrow aimed at its target. The batter tries to flick but ends up nicking it towards the stumps.",
            "The batter tries to flick this one but it brushes past the edge of the bat and crashes into the stumps."
        ],
        "c": [
            "The batter tries to hit it but does so uppishly. The ball goes straight up and into the safe hands of a fielder.",
            "The batter tries to hit this over long on but finds a fielder who takes a clean catch.",
            "The batter tries to hit this over deep cover but finds a fielder who takes a clean catch.",
        ],
        "cb": [
            "It goes straight back to the bowler who completes the return catch."
        ],
        "cw": [
            "The batter tries to slash at it but gets a thick edge that carries all the way to the keeper.",
            "There is a big edge and it carries all the way to the keeper."
        ],
        "lbw": [
            "The batter misses and gets hit on the front pad, trapped stone-cold in front of the middle stump. Ball Tracking confirms three reds.",
        ],
        "st": [
            "The batter is outside the batting crease. Before the batter can return, the keeper whips the bails off."
        ],
        "hitwicket": [
            "The batter ends up knocking the stumps over and has to depart now."
        ],
        "runoutb0": [
            "The batters attempt to cross for a run. The fielder grabs the ball and fires it at the stumps at the non-striker's end as it hits bull's eye. Replays show that the batter failed to reach safely on time and the batter is run out.",
            "The batters attempt to cross for a run. The fielder grabs the ball and throws it to the bowler. The bowler collects the ball and whips the bails off. Replays show that the batter failed to reach safely on time and the batter is run out."
        ],
        "runoutkr0": [
            "The batters attempt to cross for a run but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder fires it at the stumps at the striker's end and it hits bull's eye. Replays show that the batter failed to return safely on time and the batter is run out.",
            "The batters attempt to cross for a run but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder throws it to the keeper. The keeper collects the ball and whips the bails off. Replays show that the batter failed to return safely on time and the batter is run out."
        ],
        "runoutk0": [
            "The batters attempt to cross for a run. The fielder grabs the ball and fires it at the stumps at the striker's end as it hits bull's eye. Replays show that the non-striker failed to reach safely on time and the non-striker is run out.",
            "The batters attempt to cross for a run. The fielder grabs the ball and throws it to the keeper. The keeper collects the ball and whips the bails off. Replays show that the non-striker failed to reach safely on time and the non-striker is run out."
        ],
        "runoutbr0": [
            "The batters attempt to cross for a run but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder fires it at the stumps at the non-striker's end and it hits bull's eye. Replays show that the non-striker failed to return safely on time and the non-striker is run out.",
            "The batters attempt to cross for a run but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder throws it to the bowler. The bowler collects the ball and whips the bails off. Replays show that the non-striker failed to return safely on time and the non-striker is run out."
            # "The non-striker is far away from the crease to cover less distance while running. The bowler, instead of releasing the ball, whips the bails off. The non-striker is run out."
        ],
        "runoutb1": [
            "The batters cross for a run and go for a second. The fielder grabs the ball and fires it at the stumps at the non-striker's end as it hits bull's eye. Replays show that the batter at the non-striker's end failed to reach safely on time and that batter is run out.",
            "The batters cross for a run and go for a second. The fielder grabs the ball and throws it to the bowler. The bowler collects the ball and whips the bails off. Replays show that the batter at the non-striker's end failed to reach safely on time and that batter is run out."
        ],
        "runoutk1": [
            "The batters cross for a run and go for a second. The fielder grabs the ball and fires it at the stumps at the striker's end as it hits bull's eye. Replays show that the batter failed to reach safely on time and the batter is run out.",
            "The batters cross for a run and go for a second. The fielder grabs the ball and throws it to the keeper. The keeper collects the ball and whips the bails off. Replays show that the batter failed to reach safely on time and the batter is run out."
        ],
        "runoutbr1": [
            "The batters complete one run and attempt to cross for a second but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder fires it at the stumps at the non-striker's end and it hits bull's eye. Replays show that the batter failed to return safely on time and the batter is run out.",
            "The batters complete one run and attempt to cross for a second but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder throws it to the bowler. The bowler collects the ball and whips the bails off. Replays show that the batter failed to return safely on time and the batter is run out."
        ],
        "runoutkr1": [
            "The batters complete one run and attempt to cross for a second but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder fires it at the stumps at the striker's end and it hits bull's eye. Replays show that the non-striker failed to return safely on time and the non-striker is run out.",
            "The batters complete one run and attempt to cross for a second but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder throws it to the keeper. The keeper collects the ball and whips the bails off. Replays show that the non-striker failed to return safely on time and the non-striker is run out."
        ],
        "runoutb2": [
            "The batters complete two runs and go for a third. The fielder grabs the ball and fires it at the stumps at the non-striker's end as it hits bull's eye. Replays show that the batter failed to reach safely on time and the batter is run out.",
            "The batters complete for two runs and go for a third. The fielder grabs the ball and throws it to the bowler. The bowler collects the ball and whips the bails off. Replays show that the batter failed to reach safely on time and the batter is run out."
        ],
        "runoutk2": [
            "The batters complete two runs and go for a third. The fielder grabs the ball and fires it at the stumps at the striker's end as it hits bull's eye. Replays show that the non-striker failed to reach safely on time and the non-striker is run out.",
            "The batters complete for two runs and go for a third. The fielder grabs the ball and throws it to the keeper. The keeper collects the ball and whips the bails off. Replays show that the non-striker failed to reach safely on time and the non-striker is run out."
        ],
        "runoutkr2": [
            "The batters complete two runs and attempt to cross for a third but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder fires it at the stumps at the striker's end and it hits bull's eye. Replays show that the batter failed to return safely on time and the batter is run out.",
            "The batters complete two runs and attempt to cross for a third but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder throws it to the keeper. The keeper collects the ball and whips the bails off. Replays show that the batter failed to return safely on time and the batter is run out."
        ],
        "runoutbr2": [
            "The batters complete two runs and attempt to cross for a third but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder fires it at the stumps at the non-striker's end and it hits bull's eye. Replays show that the non-striker failed to return safely on time and the non-striker is run out.",
            "The batters complete two runs and attempt to cross for a third but turn around as the fielder grabs the ball and the batters haven't crossed over yet. The fielder throws it to the bowler. The bowler collects the ball and whips the bails off. Replays show that the non-striker failed to return safely on time and the non-striker is run out."
        ],
        "obstructing": [
            "The fielding side appeals for obstructing the field and the batter is subsequently dismissed."
        ],
        "hittheballtwice": [
            "The batter hits the ball twice and is promptly dismissed."
        ],
        "W": [
            ""
        ],
        "0wd": [
            "The ball goes way beyond the tramline and the keeper collects it. Wide signalled.",
            "The ball goes well above the batter and the keeper collects it. Wide signalled."
        ],
        "1wd": [
            "The ball goes way beyond the tramline. By the time the fielders return the ball, the batters take a run. Two wides signalled.",
            "The ball goes well above the batter. By the time the fielders return the ball, the batters take a run. Two wides signalled."
        ],
        "2wd": [
            "The ball goes way beyond the tramline. By the time the fielders return the ball, the batters take two runs. Three wides signalled.",
            "The ball goes well above the batter. By the time the fielders return the ball, the batters take two runs. Three wides signalled."
        ],
        "3wd": [
            "The ball goes way beyond the tramline. By the time the fielders return the ball, the batters take three runs. Four wides signalled.",
            "The ball goes well above the batter. By the time the fielders return the ball, the batters take three runs. Four wides signalled."
        ],
        "4wd": [
            "The ball goes way beyond the tramline. The fielders go after the ball in vain as the ball races away to the fence. Five wides signalled.",
            "The ball goes well above the batter. The fielders go after the ball in vain as the ball races away to the fence. Five wides signalled."
        ],
        "ex_nb0": [
            " Oh, wait! The bowler has overstepped here and it is a No Ball."
            # " That is clearly a dangerous ball and it is a No Ball."
        ],
        "ex_nb1": [
            " Oh, dear! On top of that, the bowler has overstepped here and it is a No Ball."
            # " On top of that, that is clearly a dangerous ball and it is a No Ball."
        ],
        "1b": [
            "The batter misses and it goes past some fielders. By the time the fielders return the ball, the batters steal a bye."
        ],
        "2b": [
            "The batter misses and it goes past some fielders. By the time the fielders return the ball, the batters steal two byes."
        ],
        "3b": [
            "The batter misses and it goes past some fielders. By the time the fielders return the ball, the batters steal three byes."
        ],
        "4b": [
            "The batter misses and it goes past the fielders as it races away to the fence. Four byes awarded to the batting side."
        ],
        "1lb": [
            "The batter misses and gets hit on the pads. The ball is deflected away from the pads. By the time the fielders return the ball, the batters steal a bye. Replays show that the ball is missing the wickets anyway."
        ],
        "2lb": [
            "The batter misses and gets hit on the pads. The ball is deflected away from the pads. By the time the fielders return the ball, the batters steal two byes. Replays show that the ball is missing the wickets anyway."
        ],
        "3lb": [
            "The batter misses and gets hit on the pads. The ball is deflected away from the pads. By the time the fielders return the ball, the batters steal three byes. Replays show that the ball is missing the wickets anyway."
        ],
        "4lb": [
            "The batter misses and gets hit on the pads. The ball is deflected away from the pads and races away to the fence. Replays show that the ball is missing the wickets and four leg byes are awarded to the batting side."
        ]
    }
    return commentary_data


def process_commentary_data(batter, bowler, fielder=None):

    if fielder is None:
        fielder = bowler

    bat_rating = AbstractPlayer(batter).get("rating_bat")
    bowl_rating = AbstractPlayer(bowler).get("rating_bowl")
    field_rating = AbstractPlayer(fielder).get("rating_field")

    # Get initial comms
    commentary_data = init_commentary_data()
    club_fielder = bool(
        (field_rating >= 1400 and field_rating < 2200 and AbstractPlayer(fielder).parent_team().ai())
        )
    club_bowler = bool(
        (bowl_rating >= 1400 and bowl_rating < 2200 and AbstractPlayer(bowler).parent_team().ai())
        )

    # Expectations at 2900+
    if bat_rating >= 2900:
        commentary_data["6"] = [
            "That's a helicopter shot going straight and out of the park!",
            "That's a helicopter shot over long on and out of the park!",
            "That's a helicopter shot over long off and out of the park!"
        ]
        return commentary_data

    # Expectations at 2200+ level
    if bat_rating >= 2200:
        commentary_data["0"] = [
            "Swing and a miss."
        ]
        commentary_data["1"] = [
            "The batter tries to loft it towards deep square but it falls just short of the fielder. A run taken."
        ]
        commentary_data["2"] = [
            "The batter looks to go over deep cover but toe ends the shot. The ball falls in front of the fielder. Two runs taken.",
            "The batter looks to go over deep square but toe ends the shot. The ball falls in front of the fielder. Two runs taken."
        ]
        commentary_data["6"] = [
            "The batter jumps down the track and smashes this over the bowler's head for a monstrous six.",
            "The batter stands tall and slaps it with a flat bat sending the ball over long on for a huge maximum that goes all the way to the third tier of the stadium.",
            "The batter picks the bones out of that, flat bats it down the ground and gets it over the roof for a huge maximum.",
            "The batter hammers this over long off for a biggie and it flies to the third tier of the stadium for a monstrous six.",
            "This is just pummeled away into the leg side and it goes all the way to the third tier of the stadium for a huge maximum.",
            "That was slammed over long on and it goes all the way to the third tier of the stadium for a huge maximum.",
            "The batter flicks it past deep mid-wicket with a helicopter shot and it sails into the third tier of the stadium for a monstrous six.",
            "This is swatted away to the leg side and it goes all the way into the third tier of the stadium for a huge maximum!",
            "This is swatted away to the off side and it goes all the way into the third tier of the stadium for a huge maximum!",
            "The batter goes airborne falling backward and hammers it over fine leg all the way into the third tier of the stadium for a huge maximum!",
            "The batter goes for a full length slide and slices it over extra cover and all the way into the third tier of the stadium for a monstrous six."
        ]
        if bowl_rating < 2200:
            commentary_data["b"] = [
                "The batter tries to go for the big hit but misses. The ball sneaks beneath the bat and crashes into the stumps.",
                "The batter tries to smash it over deep mid-wicket but misses. The ball sneaks beneath the bat and crashes into the stumps.",
                "The batter tries to smash it over deep cover with a reverse hit but misses. The ball sneaks beneath the bat and crashes into the stumps."
            ]
            commentary_data["cb"] = [
                "It goes straight back to the bowler who completes the return catch."
            ]
            commentary_data["cw"] = [
                "This is a slower delivery outside off and shaping away. The batter tries to slash at it but it gets an outside edge. The keeper dives towards the off side and collects it safely.",
                "The batter tries to slash at it but gets a thick edge that carries all the way to the keeper.",
                "The batter tries to hit it towards deep point but only gets the edge of the bat. The keeper dives to that side and takes a one-handed catch to send the batter back.",
                "There is a big edge and it carries all the way to the keeper."
            ]
            commentary_data["lbw"] = [
                "The batter tries to smash this one out of the park but misses and gets hit on the pad, trapped stone-cold in front of the middle stump. Ball Tracking confirms three reds."
            ]
            commentary_data["c"] = [
                "The batter tries to hammer this over long on but the fielder takes a clean catch just as it is about to go over the ropes.",
                "The batter tries to hammer this over long off but the fielder takes a clean catch just as it is about to go over the ropes.",
                "The batter tries to flick this away past deep square but the fielder takes a clean catch just as it is about to go over the ropes.",
                "The batter tries to flick this away past deep mid-wicket but the fielder takes a clean catch just as it is about to go over the ropes.",
                "The batter tries to thrash this over deep point but the fielder takes a clean catch just as it is about to go over the ropes.",
                "The batter tries to thrash this over deep cover but the fielder takes a clean catch just as it is about to go over the ropes."
            ]
        # Rated more than 2650
        if bat_rating >= 2650:
            commentary_data["4"] = [
                "Just short of the ropes! The batter tried to go for the helicopter shot but didn't get enough distance to send it straight out of the park. Instead, it fell just millimeters short of the ropes and it will be four instead."
            ]

        # 2400+
        if bat_rating >= 2400 and bat_rating < 2650:
            commentary_data["4"] = [
                "Playing with the field now! This is full and outside off. The batter lofts it over covers and it races to the fence. It bounces before going past the fence and it will be four instead.",
                "The batter lofts it over covers and it races into the fence but it bounces before clearing it and it will be four instead.",
                "The batter goes down the track and it races into the fence but it bounces before clearing it and it will be four instead.",
                "The batter shuffles in the crease and slashes it towards deep cover but it bounces before clearing the boundary.",
                "The batter hits it straight down the ground and it races to the fence like a tracer bullet but it bounces before clearing it and it will be four instead.",
                "Just short of the ropes! The batter tried to go for the helicopter shot but didn't get enough distance to send it straight out of the park. Instead, it fell just millimeters short of the ropes and it will be four instead."
            ]

    # Expectations at 2000+ level
    if bowl_rating >= 2200:
        if field_rating >= 2200 or club_fielder:
            commentary_data["b"] = [
                "The ball crashes into the stumps at full speed, sending the entire arrangement flying towards the keeper. The keeper grabs all flying objects with a dive."
            ]
        else:
            commentary_data["b"] = [
                "The ball crashes into the stumps at full speed, sending the entire arrangement flying towards the keeper. The keeper ducks for cover as the arrangement flies away. The umpires rearrange the stumps."
            ]
            commentary_data["b"] = [
                "The ball crashes into the stumps at full speed, sending the entire arrangement flying towards the keeper. The keeper grabs all flying objects with a dive."
            ]
        commentary_data["cb"] = [
            "It goes straight back to the bowler who completes the return catch."
        ]
        if bat_rating <= 100:
            commentary_data["b"] = [
                "This is a basic yet serious batting mistake. The batter exposes the stumps and leaves it alone out of fear that the bones might break. The ball crashes into the stumps at full speed, sending the entire arrangement flying towards the keeper. The keeper grabs all flying objects with a dive.",
                "The ball crashes into the stumps at full speed, sending the entire arrangement flying towards the keeper. The keeper grabs all flying objects with a dive."
            ]
            commentary_data["cw"] = [
                "The batter tries to get bat on ball but gets an outside edge that carries to the keeper."
            ]
            commentary_data["lbw"] = [
                "The ball hits the pads at full speed and the batter screams out of fear that the legs are broken, indicating that the ball has indeed hit the pads. Ball Tracking confirms three reds."
            ]
        if bowl_rating >= 2400:
            if field_rating >= 2000:
                commentary_data["b"] = [
                    "The ball crashes into the stumps at full speed, sending the entire arrangement flying towards the keeper. The keeper grabs all flying objects with an instantaneous dive."
                ]
            elif club_fielder:
                commentary_data["b"] = [
                    "The ball crashes into the stumps at full speed, sending the entire arrangement flying towards the keeper. The keeper grabs all flying objects with a dive."
                ]
            else:
                commentary_data["b"] = [
                    "The ball crashes into the stumps at full speed, sending the entire arrangement flying towards the keeper. The keeper ducks for cover as the arrangement flies away. The umpires rearrange the stumps."
                ]

    if field_rating >= 2200:
        commentary_data["cw"] = [
            "This is a slower delivery outside off and shaping away. The batter tries to slash at it but it gets an outside edge. The keeper dives towards the off side and collects it safely.",
            "The batter tries to slash at it but gets a thick edge that carries all the way to the keeper.",
            "The batter tries to hit it towards deep point but only gets the edge of the bat. The keeper dives to that side and takes a one-handed catch to send the batter back.",
            "There is a big edge and it carries all the way to the keeper."
        ]
        commentary_data["c"] = [
            "The batter tries to slice it away to the right, but the fielder leaps up, sticks the right hand out, snaffles the ball, tumbles on the ground but maintains the ball in the hand to dismiss the batter. The fielder then sits and poses for photographers en crosse to rub more salt into the wounds!",
            "The batter tries to slice it away to the left, but the fielder leaps up, sticks the left hand out, snaffles the ball, tumbles on the ground but maintains the ball in the hand to dismiss the batter. The fielder then sits and poses for photographers en crosse to rub more salt into the wounds!",
            "The batter looks to slice it past backward point but the fielder dives left and plucks that with the left hand.",
            "The fielder leaps full stretch backward to the right and plucks it with the right hand! The fielder then poses for the photographers to rub more salt into the wounds!",
            "The fielder leaps full stretch backward to the left and plucks it with the left hand! The fielder then poses for the photographers to rub more salt into the wounds!",
            "The ball goes low and to the left of point where the fielder dives, stretches the left hand out and takes it inches above the ground.",
            "The fielder does a back-flip, throwing the ball into the playing field. Then the fielder goes towards the ball while in the playing field, dives forward and grabs it with both hands stretched forward."
        ]
        if bat_rating <= 100:
            commentary_data["cw"] = [
                "The batter tries to get bat on ball but gets an outside edge that carries to the keeper."
            ]
    
    # Expectations at 1400-2000 level. 1000 don't know to pick up wickets.
    if club_bowler:  
        commentary_data["b"] = [
            "The ball crashes into the stumps, sending the entire arrangement flying towards the keeper. The keeper grabs all flying objects with a dive."
        ]
        commentary_data["cw"] = [
            "This is a slower delivery outside off and shaping away. The batter tries to slash at it but it gets an outside edge. The keeper dives towards the off side and collects it safely.",
            "The batter tries to hit it towards deep point but only gets the edge of the bat. The keeper dives to that side and takes a one-handed catch to send the batter back."
        ]
        if bat_rating <= 100:
            commentary_data["b"] = [
                "This is a basic yet serious batting mistake. The batter exposes the stumps and leaves it alone. The ball crashes into the stumps."
            ]
            commentary_data["cw"] = [
                "The batter tries to get bat on ball but gets an outside edge that carries to the keeper."
            ]
            commentary_data["lbw"] = [
                "The ball hits the pads and the batter screams out of fear that the legs are broken, indicating that the ball has indeed hit the pads. Ball Tracking confirms three reds.",
            ]
            commentary_data["runoutb0"] = [
                "The batter walks too slowly and continues walking at a snail's pace. Meanwhile, a fielder fires the ball at the stumps at the non-striker's end as it hits bull's eye. The batter had barely left the crease at the striker's end and is consequently run out.",
                "The batter walks too slowly and continues walking at a snail's pace. Meanwhile, a fielder grabs the ball and throws it to the bowler. The bowler collects the ball and whips the bails off. The batter had barely left the crease at the striker's end and is consequently run out."
            ]
            commentary_data["runoutk0"] = [
                "The batter at the non-striker's end walks too slowly and continues walking at a snail's pace. Meanwhile, a fielder fires the ball at the stumps at the striker's end as it hits bull's eye. That batter had barely left the crease at the non-striker's end and is consequently run out.",
                "The batter at the non-striker's end walks too slowly and continues walking at a snail's pace. Meanwhile, a fielder grabs the ball and throws it to the keeper. The keeper collects the ball and whips the bails off. That batter had barely left the crease at the non-striker's end and is consequently run out."
            ]
            commentary_data["runoutkr0"] = [
                "The batter walks too slowly and continues walking at a snail's pace. Meanwhile, a fielder grabs the ball. The batters turn around and make their way back at a snail's pace. The fielder fires the ball at the stumps at the striker's end and it hits bull's eye. The batter had barely left the crease at the striker's end but is too slow to make it back in time. Consequently, the batter is run out.",
                "The batter walks too slowly and continues walking at a snail's pace. Meanwhile, a fielder grabs the ball. The batters turn around and make their way back at a snail's pace. The fielder throws the ball to the keeper who collects it and whips the bails off. The batter had barely left the crease at the striker's end but is too slow to make it back in time. Consequently, the batter is run out."
            ]
            commentary_data["runoutbr0"] = [
                "The batter at the non-striker's end walks too slowly and continues walking at a snail's pace. Meanwhile, a fielder grabs the ball. The batters turn around and make their way back at a snail's pace. The fielder fires the ball at the stumps at the non-striker's end and it hits bull's eye. The non-striker had barely left the crease at the non-striker's end but is too slow to make it back in time. Consequently, the non-striker is run out.",
                "The batter at the non-striker's end walks too slowly and continues walking at a snail's pace. Meanwhile, a fielder grabs the ball. The batters turn around and make their way back at a snail's pace. The fielder throws the ball to the bowler who collects it and whips the bails off. The non-striker had barely left the crease at the non-striker's end but is too slow to make it back in time. Consequently, the non-striker is run out."
            ]

    '''
    DISTINCT BATTING STYLES

    # slow scorers
    if batter in "slow-scorers": # change based on batter ID(s)
        commentary_data["0"] = [
            "The batter defends it off the back foot.",
            "The batter leaves it alone and lets it go through to the keeper.",
            "Straight at the stumps, the batter blocks it off.",
            "Pitched up outside the off stump and shaping away, the batter leaves this one alone.",
        ]
        commentary_data["1"] = [
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
        ]
        commentary_data["2"] =  [
            "The batter slaps it wide of deep cover for two runs.",
            "The batter flicks it through mid-wicket for two runs.",
            "The batter punches through covers for a couple."
        ]
        commentary_data["4"] = [
            "The batter goes downtown and the ball races to the long off fence for a boundary.",
            "The batter goes down the track and it races to the fence like a tracer bullet.",
            "The batter shuffles in the crease and slashes it to deep cover for a boundary.",
            "Slammed hard towards deep cover, it races to the fence.",
            "The batter whacks it past deep mid-wicket for a boundary.",
            "The batter hits it straight down the ground and it races to the fence like a tracer bullet.",
            "The batter thrashes that through the off side for four!"
        ]

    # One-handed batters
    if batter == "one-handed": # change the string based on batter ID(s)
        commentary_data["0"] = [
            "The batter swings holding the bat with just one hand but misses."
        ]
        commentary_data["1"] = [
            "The batter tries to loft it towards long on with a one-handed bat but it falls just short of the fielder. A run taken.",
            "The batter tries to loft it towards long off with a one-handed bat but it falls just short of the fielder. A run taken."
        ]
        commentary_data["2"] = [
            "The batter looks to go over long off with a one-handed bat but toe ends the shot. The ball falls in front of the fielder. Two runs taken.",
            "The batter looks to go over long on with a one-handed bat but toe ends the shot. The ball falls in front of the fielder. Two runs taken."
        ]
        commentary_data["4"] = [
            "Playing with the field now! This is full and outside off. The batter lofts it over covers with a one-handed bat and it races to the fence.",
            "The batter lofts it over covers with a one-handed bat and it races into the fence.",
            "The batter goes downtown with a one-handed bat and the ball races to the long off fence for a boundary.",
            "The batter goes down the track with a one-handed bat and it races to the fence like a tracer bullet.",
            "The batter shuffles in the crease and slashes it to deep cover with a one-handed bat for a boundary.",
            "The batter whacks it past deep mid-wicket with a one-handed bat and it goes all the way for four.",
            "The batter hits it straight down the ground with a one-handed bat and it races to the fence like a tracer bullet."
        ]
        commentary_data["6"] = [
            "The batter jumps down the track and smashes this over the bowler's head with a one-handed bat for a huge maximum.",
            "The batter stands tall and slaps it with a one-handed flat bat sending the ball over long on for a maximum.",
            "The batter picks the bones out of that, flat bats it down the ground with one hand and gets it over the long off fence for a biggie.",
            "The batter hammers this over long off with a one-handed bat and it flies to the stands for a biggie.",
            "That was slammed over long on with a one-handed bat and it goes all the way to the stands for a maximum."
        ]

    # Two-handed wide leg batter
    if batter == "wide-legged anomaly": # change the string based on batter ID(s)
        commentary_data["0"] = [
            "Pitched up outside the off stump and shaping away, the batter tries to reach it but misses.",
            "Swing and a miss."
        ]
        commentary_data["1"] = [
            "The batter tries to loft it towards long on but it falls just short of the fielder. A run taken.",
            "The batter tries to loft it towards long off but it falls just short of the fielder. A run taken."
        ]
        commentary_data["2"] = [
            "The batter looks to go over long off but toe ends the shot. The ball falls in front of the fielder. Two runs taken.",
            "The batter looks to go over long on but toe ends the shot. The ball falls in front of the fielder. Two runs taken."
        ]
        commentary_data["4"] = [
            "The batter lofts it over long on and it races into the fence but it bounces before clearing it and it will be four instead.",
            "The batter goes down the track and it races into the fence but it bounces before clearing it and it will be four instead.",
            "The batter lofts it over long off and it races into the fence but it bounces before clearing it and it will be four instead.",
            "The batter hits it straight down the ground and it races to the fence like a tracer bullet but it bounces before clearing it and it will be four instead."
        ]
        commentary_data["6"] = [
            "The batter jumps down the track and smashes this over the bowler's head for a huge maximum.",
            "The batter stands tall and slaps it with a flat bat sending the ball over long on for a maximum.",
            "The batter picks the bones out of that, flat bats it down the ground and gets it over the long off fence for a biggie.",
            "The batter scoops this all the way over fine leg for a huge maximum.",
            "The batter hammers this over long off and it flies to the stands for a biggie.",
            "That was slammed over long on and it goes all the way to the stands for a maximum."
        ]
        commentary_data["hitwicket"] = [
            "The batter tries to swing hard at it but ends up hitting the arrangement behind the batter instead. The batter ends up hitting it away but that is irrelevant now. Though the ball falls short of the fielders, the batter has to depart now."
        ]
        commentary_data["cw"] = [
            "The batter hits it straight up. It goes all the way behind to the keeper who makes no mistake."
        ]
        commentary_data["cb"] = [
            "The batter hits it straight up. It goes back all the way to the bowler who completes the catch."
        ]
        if bowl_rating >= 2200:
            commentary_data["c"] = [
                "The fielder does a back-flip, throwing the ball into the playing field. Then the fielder goes towards the ball while in the playing field, dives forward and grabs it with both hands stretched forward."
            ]
        else:
            commentary_data["c"] = [
                "The batter tries to hit it but does so uppishly. The ball goes straight up and into the safe hands of a fielder.",
                "The batter tries to hit this over long on but finds a fielder who takes a clean catch."
            ]
    

    # Hardcore Purists.
    if "hardcore_purist" in batter: # change the string based on batter id(s)
        commentary_data["0"] = [
            "The batter lunges forward and presents a dead bat as the ball drops onto the pitch.",
            "The batter leaves it alone and lets it go through to the keeper.",
            "The batter defends this one off the back foot by presenting a dead bat as the ball drops onto the pitch.",
            "The batter plays that with soft hands, meeting the ball and letting it drop onto the pitch."
        ]
        commentary_data["1"] = [
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
        ]
        commentary_data["2"] =  [
            "The batter slaps it wide of deep cover for two runs.",
            "The batter flicks it through mid-wicket for two runs.",
            "The batter punches through covers for a couple."
        ]
        commentary_data["4"] = [
            "The batter goes for a straight drive and the ball goes all the way to the long off fence for a boundary.",
            "The batter goes for a cover drive and the ball goes all the way to the deep cover fence for a boundary."
        ]   
        commentary_data["cw"] = [
            "This is a slower delivery outside off and shaping away. The batter tries to defend but it gets an outside edge. The keeper dives towards the off side and collects it safely.",
            "The batter tries to defend but gets a thick edge that carries all the way to the keeper."
        ]
        if field_rating >= 2200: 
            commentary_data["c"] = [
                "The batter tries a soft-handed defensive but it goes away to the right, and the fielder leaps up, sticks the right hand out, snaffles the ball, tumbles on the ground but maintains the ball in the hand to dismiss the batter. The fielder then sits and poses for photographers en crosse to rub more salt into the wounds!",
                "The batter tries a soft-handed defensive but it goes away to the left, and the fielder leaps up, sticks the left hand out, snaffles the ball, tumbles on the ground but maintains the ball in the hand to dismiss the batter. The fielder then sits and poses for photographers en crosse to rub more salt into the wounds!",
                "The batter tries a soft-handed defensive but it goes past backward point and the fielder dives left and plucks that with the left hand.",
                "The fielder leaps full stretch backward to the right and plucks it with the right hand! The fielder then poses for the photographers to rub more salt into the wounds!",
                "The fielder leaps full stretch backward to the left and plucks it with the left hand! The fielder then poses for the photographers to rub more salt into the wounds!",
                "The batter tries a soft-handed defensive but it goes low and to the left of point where the fielder dives, stretches the left hand out and takes it inches above the ground."
            ]
        else:
            commentary_data["c"] = [
                "The batter tries to play it with soft hands and a dead bat but it ends up edged and goes straight to the fielder.",
            ]
        if bowl_rating < 2200 and not club_bowler:
            commentary_data["b"] = [
                "The batter tries to defend with soft hands and a dead bat but misses and the ball crashes into the stumps."
            ]
'''

    return commentary_data


def fetch_commentary_data(score_string: str) -> str:
    commentary_data = process_commentary_data("", "", "", "")
    return choice(commentary_data[score_string])


def fetch_commentary_data_teamwise(
        score_string: str,
        batter: str="",
        bowler: str="",
        fielder: str|None=None
    ) -> str:
    if fielder is None:
        fielder = bowler
    commentary_data = process_commentary_data(batter, bowler, fielder)
    if score_string.endswith("nb"):
        c1 = choice(commentary_data.get(score_string[0]))
        if int(score_string[0]) >= 4:
            c2 = choice(commentary_data.get("ex_nb1"))
        else:
            c2 = choice(commentary_data.get("ex_nb0"))
        return c1 + c2
    if commentary_data.get(score_string) is None:
        return ""
    return choice(commentary_data.get(score_string))
