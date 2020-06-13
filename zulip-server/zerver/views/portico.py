import ujson
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse

from version import LATEST_DESKTOP_VERSION
from zerver.context_processors import get_realm_from_request, latest_info_context
from zerver.decorator import add_google_analytics, redirect_to_login
from zerver.models import Realm


@add_google_analytics
def apps_view(request: HttpRequest, _: str) -> HttpResponse:
    if settings.ZILENCER_ENABLED:
        return TemplateResponse(
            request,
            'zerver/apps.html',
            context={
                "page_params": {
                    'electron_app_version': LATEST_DESKTOP_VERSION,
                },
            },
        )
    return HttpResponseRedirect('https://zulip.com/apps/', status=301)

@add_google_analytics
def plans_view(request: HttpRequest) -> HttpResponse:
    realm = get_realm_from_request(request)
    realm_plan_type = 0
    free_trial_days = settings.FREE_TRIAL_DAYS
    if realm is not None:
        realm_plan_type = realm.plan_type
        if realm.plan_type == Realm.SELF_HOSTED and settings.PRODUCTION:
            return HttpResponseRedirect('https://zulip.com/plans')
        if not request.user.is_authenticated:
            return redirect_to_login(next="plans")
    return TemplateResponse(
        request,
        "zerver/plans.html",
        context={"realm_plan_type": realm_plan_type, 'free_trial_days': free_trial_days},
    )

@add_google_analytics
def team_view(request: HttpRequest) -> HttpResponse:
    if not settings.ZILENCER_ENABLED:
        return HttpResponseRedirect('https://zulip.com/team/', status=301)

    try:
        with open(settings.CONTRIBUTOR_DATA_FILE_PATH) as f:
            data = ujson.load(f)
    except FileNotFoundError:
        data = {'contrib': {}, 'date': "Never ran."}

    return TemplateResponse(
        request,
        'zerver/team.html',
        context={
            'page_params': {
                'contrib': data['contrib'],
            },
            'date': data['date'],
        },
    )

def get_isolated_page(request: HttpRequest) -> bool:
    '''Accept a GET param `?nav=no` to render an isolated, navless page.'''
    return request.GET.get('nav') == 'no'

@add_google_analytics
def landing_view(request: HttpRequest, template_name: str) -> HttpResponse:
    return TemplateResponse(request, template_name)

@add_google_analytics
def hello_view(request: HttpRequest) -> HttpResponse:
    return TemplateResponse(request, 'zerver/hello.html', latest_info_context())

@add_google_analytics
def terms_view(request: HttpRequest) -> HttpResponse:
    return TemplateResponse(
        request, 'zerver/terms.html',
        context={'isolated_page': get_isolated_page(request)},
    )

@add_google_analytics
def privacy_view(request: HttpRequest) -> HttpResponse:
    return TemplateResponse(
        request, 'zerver/privacy.html',
        context={'isolated_page': get_isolated_page(request)},
    )
