from django.shortcuts import render
from bin.mongodb import mongolivematchclient
from modules.live.forms.commentary import MidCommentary


def addComment(request):
    if request.method == "POST":
        form = MidCommentary(request.POST)
        if form.is_valid():
            comment_collection = mongolivematchclient.get_mid_commentary()
            comment = form.cleaned_data
            comment_id = str(comment["innings"]) + "." + comment["ball_id"]
            comment_data = {
                "_id": comment_id,
                "comments": []
            }
            comment_body = {
                "key": comment["comment_type"],
                "value": ""
            }
            if comment["comment_type"] == "Text":
                comment_body["value"] = comment["comments"]
            elif comment["comment_type"] == "Image":
                comment_body["value"] = comment["image_location"]
            if comment_collection.find_one(comment_id) is None:
                comment_data["comments"].append(comment_body)
                comment_collection.insert_one(comment_data)
            else:
                comment_collection.update_one(
                    {'_id': comment_id},
                    {
                        '$push': {
                            'comments': comment_body
                        }
                    }
                )
            return render(
                request,
                "live_comment.html",
                {
                    "title": "New Comment",
                    "form": MidCommentary(),
                }
            )
        else:
            return render(
                request,
                "live_comment.html",
                {
                    "title": "New Comment",
                    "form": MidCommentary(),
                }
            )
    else:
        return render(
            request,
            "live_comment.html",
            {
                "title": "New Comment",
                "form": MidCommentary(),
            }
        )