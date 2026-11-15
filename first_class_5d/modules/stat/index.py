from django.shortcuts import render


def stat_index(request) -> render:
    return render(
        request,
        "stat_index.html"
    )
