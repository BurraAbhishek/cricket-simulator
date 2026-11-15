from django.http import JsonResponse, FileResponse
from django.core.exceptions import PermissionDenied
from django.contrib.staticfiles import finders
from bin.mongoinserts.load_games import fetch_game


def raw_match_data(request, clas, id):
    game = fetch_game(clas, id)
    if game is None:
        raise PermissionDenied
    try:
        return JsonResponse(game)
    except TypeError:
        raise PermissionDenied

