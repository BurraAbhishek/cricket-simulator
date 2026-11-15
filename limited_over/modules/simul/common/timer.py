def time_to_verbose(seconds):
    v = ""
    h, m, s = time_to_components(seconds)
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
