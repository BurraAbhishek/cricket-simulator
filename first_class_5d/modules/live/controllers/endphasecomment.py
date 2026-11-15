from django.shortcuts import render
from bin.mongodb import mongoclient
from modules.live.forms.phasecommentary import MidPhaseCommentary


def add_phase_comment(request):
    if request.method == "POST":
        form = MidPhaseCommentary(request.POST)
        if form.is_valid():
            comment_collection = mongoclient.live_db_get_collection(
                mongoclient.CURRENT_MATCH_PHASE
            )
            comment = form.cleaned_data
            comment_id = int(comment["match_session_id"])
            comment_body = {
                "key": comment["comment_type"],
                "value": ""
            }
            if comment["comment_type"] == "Text":
                comment_body["value"] = comment["comments"]
            elif comment["comment_type"] == "Image":
                comment_body["value"] = comment["image_location"]
            phase_data = comment_collection.find_one(comment_id)
            if phase_data is not None and phase_data["capture_end"] is False:
                comment_collection.update_one(
                    {'_id': comment_id},
                    {
                        '$push': {
                            'end_comments': comment_body
                        }
                    }
                )
            return render(
                request,
                "live_comment.html",
                {
                    "title": "New Comment",
                    "form": MidPhaseCommentary(),
                }
            )
        else:
            return render(
                request,
                "live_comment.html",
                {
                    "title": "New Comment",
                    "form": MidPhaseCommentary(),
                }
            )
    else:
        return render(
            request,
            "live_comment.html",
            {
                "title": "New Comment",
                "form": MidPhaseCommentary(),
            }
        )