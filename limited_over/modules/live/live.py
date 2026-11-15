from modules.live.controllers.game import newGame
# from modules.live.controllers.innings import nextDelivery
from modules.live.controllers.innings_automate import nextDeliveryAutomated



def liveGame(request):
    try:
        # 1 - pre-match comment
        # 2 - 1 inning
        # 3 - inning comment
        # 4 - 2 inning
        # 5 - post match comment
        # return nextDelivery(request)
        return nextDeliveryAutomated(request)
    except TypeError:
        return newGame(request)
