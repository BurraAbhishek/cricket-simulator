from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS


def hours(seconds):
    return 3600 * seconds


DAY_BREAK = TOURNAMENT_SETTINGS.get("end_of_day_seconds", hours(8))


def time_to_verbose(seconds):
    v = "Day "
    d = 1 + (seconds // DAY_BREAK)
    if d < 1:
        d = 1
    if d > 5:
        d = 5
    v += str(d)
    v += ", "
    if d < 5:
        h, m, s = time_to_components(seconds % DAY_BREAK)
    else:
        h, m, s = time_to_components(seconds - (4 * DAY_BREAK))
    v += str(h)
    v += ":"
    v += f"{m:02d}"
    v += ":"
    v += f"{s:02d}"
    return v


def time_to_components(seconds):
    hour = seconds // 3600
    minute = (seconds % 3600) // 60
    second = seconds % 60
    return hour, minute, second


def break_to_verbose(seconds):
    minute = (seconds % 3600) // 60
    second = seconds % 60
    return f"{minute:02d}" + ":" + f"{second:02d}"
