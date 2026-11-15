from django.shortcuts import render
from bin.mongodb import mongoclient
from modules.live.forms.phasedetails import PhaseDetails


def add_test_phase(request):
    if request.method == "POST":
        form = PhaseDetails(request.POST)
        if form.is_valid():
            match_phase_collection = mongoclient.live_db_get_collection(
                mongoclient.CURRENT_MATCH_PHASE
            )
            formdata = form.cleaned_data
            capture_end = bool(formdata["capture_end"])
            session_data = {
                "_id": int(formdata["match_session_id"]),
                "start_inning": int(formdata["start_inning"]),
                "start_ball": str(formdata["start_ball"]),
                "end_inning": int(formdata["end_inning"]),
                "end_ball": str(formdata["end_ball"]),
                "capture_end": capture_end
            }
            if not capture_end:
                session_data["end_comments"] = []
            try:
                match_phase_collection.insert_one(session_data)
            except Exception:
                pass
            return render(
                request,
                "live_comment.html",
                {
                    "title": "Add Match Session Data",
                    "form": PhaseDetails(),
                }
            )
        else:
            return render(
                request,
                "live_comment.html",
                {
                    "title": "Add Match Session Data",
                    "form": PhaseDetails(),
                }
            )
    else:
        return render(
            request,
            "live_comment.html",
            {
                "title": "Add Match Session Data",
                "form": PhaseDetails(),
            }
        )