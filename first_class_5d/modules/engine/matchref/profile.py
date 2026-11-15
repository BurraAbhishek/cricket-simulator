from django.shortcuts import render


def match_officials(request):
    games_per_head = 6
    referee_name = "RefereeBot"
    umpire1_name = "O.F. UmpireBot"
    umpire3_name = "T.V. UmpireBot"
    umpire4_name = "R.F. UmpireBot"
    officials = {
        "referee": {
            "name": referee_name,
            "avatar": "images/bot/face/referee.png",
            "about": str(
                referee_name
                + " is a class of 3000-rated former elite multi-sport" 
                + " competitors and world-record holders who transitioned"
                + " from sports fields to the regulatory chairs. "
                + referee_name
                + " ensures that peak athletic efficiency and performance are"
                + " never compromised for commercial duration. "
                + referee_name
                + "'s sign-off is the final forensic guarantee that a result" 
                + " is the product of absolute sporting truth. "
                + " There are "
                + str(games_per_head + 1)
                + " such referees, ranging from "
                + referee_name
                + "0 to "
                + referee_name
                + str(games_per_head)
                + ".\n"
                + referee_name
                + "0 is currently serving as the Chair, President and CEO of"
                + " the Proctoring Unit."
            )
        },
        "umpires": [
            {
                "name": umpire1_name,
                "avatar": "images/bot/face/umpire.png",
                "about": str(
                    umpire1_name
                    + " is a class of umpires that serve as one of the two"
                    + " on-field umpires. In this role, "
                    + umpire1_name
                    + " specializes in real-time adjudication of delivery"
                    + " metrics and dismissal physics in accordance with the"
                    + " Tournament Playing Conditions. In addition, "
                    + umpire1_name
                    + " monitors the crease kinetics and the clock. There are "
                    + str(2 * games_per_head)
                    + " such umpires."
                )
            },
            {
                "name": umpire3_name,
                "avatar": "images/bot/face/umpire.png",
                "about": str(
                    umpire3_name
                    + " is a class of umpires that operate from the"
                    + " digital perimeter, serving as the"
                    + " lead analyst and the Third Umpire. Utilizing"
                    + " high-ratinglity television feeds and advanced edge"
                    + " detection capabilities, "
                    + umpire3_name
                    + " provides the absolute verification required for"
                    + " complex on-field reviews and verifies each"
                    + " boundary, catch and DRS challenge."
                    + " By synchronizing ball-tracking and haptics, "
                    + umpire3_name
                    + " ensures that every decision is rendered with 100%"
                    + " technical certainty. There are "
                    + str(games_per_head)
                    + " such umpires."
                )
            },
            {
                "name": umpire4_name,
                "avatar": "images/bot/face/umpire.png",
                "about": str(
                    umpire4_name
                    + " is a class of umpires that serve as the Fourth Umpire"
                    + " , the primary enforcer of tactical and logistical"
                    + " integrity. Stationed between the team dugouts, "
                    + umpire4_name
                    + " oversees the playing area, conducting mandatory"
                    + " equipment audits and monitoring the stop clock from"
                    + " the boundary. "
                    + umpire4_name
                    + " ensures that no unauthorized interference reaches the"
                    + " playing area. As the designated emergency backup, "
                    + umpire4_name
                    + " ensures the continuity of the Forensic Data Stream"
                    + " throughout the Contest. There are "
                    + str(games_per_head)
                    + " such umpires."
                )
            },
        ]
    }
    return render(
        request,
        "match_officials.html",
        {
            "officials": officials
        }
    )
