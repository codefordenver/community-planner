from django.http import HttpRequest, HttpResponse

from zerver.decorator import api_key_only_webhook_view, has_request_variables
from zerver.lib.response import json_success
from zerver.lib.webhooks.common import check_send_webhook_message
from zerver.models import UserProfile


@api_key_only_webhook_view('Dropbox', notify_bot_owner_on_invalid_json=False)
@has_request_variables
def api_dropbox_webhook(request: HttpRequest, user_profile: UserProfile) -> HttpResponse:
    if request.method == 'POST':
        topic = 'Dropbox'
        check_send_webhook_message(request, user_profile, topic,
                                   "File has been updated on Dropbox!")
        return json_success()
    else:
        return HttpResponse(request.GET['challenge'])
