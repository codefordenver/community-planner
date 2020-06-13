import re
from functools import partial
from inspect import signature
from typing import Any, Dict, Optional

from django.http import HttpRequest, HttpResponse

from zerver.decorator import api_key_only_webhook_view
from zerver.lib.request import REQ, has_request_variables
from zerver.lib.response import json_success
from zerver.lib.webhooks.common import (
    UnexpectedWebhookEventType,
    check_send_webhook_message,
    get_http_headers_from_filename,
    validate_extract_webhook_http_header,
)
from zerver.lib.webhooks.git import (
    CONTENT_MESSAGE_TEMPLATE,
    TOPIC_WITH_BRANCH_TEMPLATE,
    TOPIC_WITH_PR_OR_ISSUE_INFO_TEMPLATE,
    get_commits_comment_action_message,
    get_issue_event_message,
    get_pull_request_event_message,
    get_push_commits_event_message,
    get_push_tag_event_message,
    get_release_event_message,
    get_setup_webhook_message,
)
from zerver.models import UserProfile

fixture_to_headers = get_http_headers_from_filename("HTTP_X_GITHUB_EVENT")

class UnknownEventType(Exception):
    pass

def get_opened_or_update_pull_request_body(payload: Dict[str, Any],
                                           include_title: Optional[bool]=False) -> str:
    pull_request = payload['pull_request']
    action = payload['action']
    if action == 'synchronize':
        action = 'updated'
    assignee = None
    if pull_request.get('assignee'):
        assignee = pull_request['assignee']['login']

    return get_pull_request_event_message(
        get_sender_name(payload),
        action,
        pull_request['html_url'],
        target_branch=pull_request['head']['ref'],
        base_branch=pull_request['base']['ref'],
        message=pull_request['body'],
        assignee=assignee,
        number=pull_request['number'],
        title=pull_request['title'] if include_title else None,
    )

def get_assigned_or_unassigned_pull_request_body(payload: Dict[str, Any],
                                                 include_title: Optional[bool]=False) -> str:
    pull_request = payload['pull_request']
    assignee = pull_request.get('assignee')
    if assignee is not None:
        assignee = assignee.get('login')

    base_message = get_pull_request_event_message(
        get_sender_name(payload),
        payload['action'],
        pull_request['html_url'],
        number=pull_request['number'],
        title=pull_request['title'] if include_title else None,
    )
    if assignee is not None:
        return f"{base_message[:-1]} to {assignee}."
    return base_message

def get_closed_pull_request_body(payload: Dict[str, Any],
                                 include_title: Optional[bool]=False) -> str:
    pull_request = payload['pull_request']
    action = 'merged' if pull_request['merged'] else 'closed without merge'
    return get_pull_request_event_message(
        get_sender_name(payload),
        action,
        pull_request['html_url'],
        number=pull_request['number'],
        title=pull_request['title'] if include_title else None,
    )

def get_membership_body(payload: Dict[str, Any]) -> str:
    action = payload['action']
    member = payload['member']
    team_name = payload['team']['name']

    return "{sender} {action} [{username}]({html_url}) {preposition} the {team_name} team.".format(
        sender=get_sender_name(payload),
        action=action,
        username=member['login'],
        html_url=member['html_url'],
        preposition='from' if action == 'removed' else 'to',
        team_name=team_name,
    )

def get_member_body(payload: Dict[str, Any]) -> str:
    return "{} {} [{}]({}) to [{}]({}).".format(
        get_sender_name(payload),
        payload['action'],
        payload['member']['login'],
        payload['member']['html_url'],
        get_repository_name(payload),
        payload['repository']['html_url'],
    )

def get_issue_body(payload: Dict[str, Any],
                   include_title: Optional[bool]=False) -> str:
    action = payload['action']
    issue = payload['issue']
    assignee = issue['assignee']
    return get_issue_event_message(
        get_sender_name(payload),
        action,
        issue['html_url'],
        issue['number'],
        issue['body'],
        assignee=assignee['login'] if assignee else None,
        title=issue['title'] if include_title else None,
    )

def get_issue_comment_body(payload: Dict[str, Any],
                           include_title: Optional[bool]=False) -> str:
    action = payload['action']
    comment = payload['comment']
    issue = payload['issue']

    if action == 'created':
        action = '[commented]'
    else:
        action = f'{action} a [comment]'
    action += '({}) on'.format(comment['html_url'])

    return get_issue_event_message(
        get_sender_name(payload),
        action,
        issue['html_url'],
        issue['number'],
        comment['body'],
        title=issue['title'] if include_title else None,
    )

def get_fork_body(payload: Dict[str, Any]) -> str:
    forkee = payload['forkee']
    return "{} forked [{}]({}).".format(
        get_sender_name(payload),
        forkee['name'],
        forkee['html_url'],
    )

def get_deployment_body(payload: Dict[str, Any]) -> str:
    return f'{get_sender_name(payload)} created new deployment.'

def get_change_deployment_status_body(payload: Dict[str, Any]) -> str:
    return 'Deployment changed status to {}.'.format(
        payload['deployment_status']['state'],
    )

def get_create_or_delete_body(payload: Dict[str, Any], action: str) -> str:
    ref_type = payload['ref_type']
    return '{} {} {} {}.'.format(
        get_sender_name(payload),
        action,
        ref_type,
        payload['ref'],
    ).rstrip()

def get_commit_comment_body(payload: Dict[str, Any]) -> str:
    comment = payload['comment']
    comment_url = comment['html_url']
    commit_url = comment_url.split('#', 1)[0]
    action = f'[commented]({comment_url})'
    return get_commits_comment_action_message(
        get_sender_name(payload),
        action,
        commit_url,
        comment.get('commit_id'),
        comment['body'],
    )

def get_push_tags_body(payload: Dict[str, Any]) -> str:
    return get_push_tag_event_message(
        get_sender_name(payload),
        get_tag_name_from_ref(payload['ref']),
        action='pushed' if payload.get('created') else 'removed',
    )

def get_push_commits_body(payload: Dict[str, Any]) -> str:
    commits_data = [{
        'name': (commit.get('author').get('username') or
                 commit.get('author').get('name')),
        'sha': commit['id'],
        'url': commit['url'],
        'message': commit['message'],
    } for commit in payload['commits']]
    return get_push_commits_event_message(
        get_sender_name(payload),
        payload['compare'],
        get_branch_name_from_ref(payload['ref']),
        commits_data,
        deleted=payload['deleted'],
    )

def get_public_body(payload: Dict[str, Any]) -> str:
    return "{} made [the repository]({}) public.".format(
        get_sender_name(payload),
        payload['repository']['html_url'],
    )

def get_wiki_pages_body(payload: Dict[str, Any]) -> str:
    wiki_page_info_template = "* {action} [{title}]({url})\n"
    wiki_info = ''
    for page in payload['pages']:
        wiki_info += wiki_page_info_template.format(
            action=page['action'],
            title=page['title'],
            url=page['html_url'],
        )
    return f"{get_sender_name(payload)}:\n{wiki_info.rstrip()}"

def get_watch_body(payload: Dict[str, Any]) -> str:
    return "{} starred [the repository]({}).".format(
        get_sender_name(payload),
        payload['repository']['html_url'],
    )

def get_repository_body(payload: Dict[str, Any]) -> str:
    return "{} {} [the repository]({}).".format(
        get_sender_name(payload),
        payload.get('action'),
        payload['repository']['html_url'],
    )

def get_add_team_body(payload: Dict[str, Any]) -> str:
    return "[The repository]({}) was added to team {}.".format(
        payload['repository']['html_url'],
        payload['team']['name'],
    )

def get_team_body(payload: Dict[str, Any]) -> str:
    changes = payload["changes"]
    if "description" in changes:
        actor = payload["sender"]["login"]
        new_description = payload["team"]["description"]
        return f"**{actor}** changed the team description to:\n```quote\n{new_description}\n```"
    if "name" in changes:
        original_name = changes["name"]["from"]
        new_name = payload["team"]["name"]
        return f"Team `{original_name}` was renamed to `{new_name}`."
    if "privacy" in changes:
        new_visibility = payload["team"]["privacy"]
        return f"Team visibility changed to `{new_visibility}`"
    else:  # nocoverage
        raise UnexpectedWebhookEventType("GitHub", f"Team Edited: {changes.keys()}")

def get_release_body(payload: Dict[str, Any]) -> str:
    data = {
        'user_name': get_sender_name(payload),
        'action': payload['action'],
        'tagname': payload['release']['tag_name'],
        # Not every GitHub release has a "name" set; if not there, use the tag name.
        'release_name': payload['release']['name'] or payload['release']['tag_name'],
        'url': payload['release']['html_url'],
    }

    return get_release_event_message(**data)

def get_page_build_body(payload: Dict[str, Any]) -> str:
    build = payload['build']
    status = build['status']
    actions = {
        'null': 'has yet to be built',
        'building': 'is being built',
        'errored': 'has failed{}',
        'built': 'has finished building',
    }

    action = actions.get(status, f'is {status}')
    action.format(
        CONTENT_MESSAGE_TEMPLATE.format(message=build['error']['message']),
    )

    return "Github Pages build, triggered by {}, {}.".format(
        payload['build']['pusher']['login'],
        action,
    )

def get_status_body(payload: Dict[str, Any]) -> str:
    if payload['target_url']:
        status = '[{}]({})'.format(
            payload['state'],
            payload['target_url'],
        )
    else:
        status = payload['state']
    return "[{}]({}) changed its status to {}.".format(
        payload['sha'][:7],  # TODO
        payload['commit']['html_url'],
        status,
    )

def get_pull_request_ready_for_review_body(payload: Dict[str, Any],
                                           include_title: Optional[bool]=False) -> str:

    message = "**{sender}** has marked [PR #{pr_number}]({pr_url}) as ready for review."
    return message.format(
        sender = get_sender_name(payload),
        pr_number = payload['pull_request']['number'],
        pr_url = payload['pull_request']['html_url'],
    )

def get_pull_request_review_body(payload: Dict[str, Any],
                                 include_title: Optional[bool]=False) -> str:
    title = "for #{} {}".format(
        payload['pull_request']['number'],
        payload['pull_request']['title'],
    )
    return get_pull_request_event_message(
        get_sender_name(payload),
        'submitted',
        payload['review']['html_url'],
        type='PR Review',
        title=title if include_title else None,
    )

def get_pull_request_review_comment_body(payload: Dict[str, Any],
                                         include_title: Optional[bool]=False) -> str:
    action = payload['action']
    message = None
    if action == 'created':
        message = payload['comment']['body']

    title = "on #{} {}".format(
        payload['pull_request']['number'],
        payload['pull_request']['title'],
    )

    return get_pull_request_event_message(
        get_sender_name(payload),
        action,
        payload['comment']['html_url'],
        message=message,
        type='PR Review Comment',
        title=title if include_title else None,
    )

def get_pull_request_review_requested_body(payload: Dict[str, Any],
                                           include_title: Optional[bool]=False) -> str:
    requested_reviewer = [payload['requested_reviewer']] if 'requested_reviewer' in payload else []
    requested_reviewers = (payload['pull_request']['requested_reviewers'] or requested_reviewer)

    requested_team = [payload['requested_team']] if 'requested_team' in payload else []
    requested_team_reviewers = (payload['pull_request']['requested_teams'] or requested_team)

    sender = get_sender_name(payload)
    pr_number = payload['pull_request']['number']
    pr_url = payload['pull_request']['html_url']
    message = "**{sender}** requested {reviewers} for a review on [PR #{pr_number}]({pr_url})."
    message_with_title = ("**{sender}** requested {reviewers} for a review on "
                          "[PR #{pr_number} {title}]({pr_url}).")
    body = message_with_title if include_title else message

    all_reviewers = []

    for reviewer in requested_reviewers:
        all_reviewers.append("[{login}]({html_url})".format(**reviewer))

    for team_reviewer in requested_team_reviewers:
        all_reviewers.append("[{name}]({html_url})".format(**team_reviewer))

    reviewers = ""
    if len(all_reviewers) == 1:
        reviewers = all_reviewers[0]
    else:
        reviewers = "{} and {}".format(', '.join(all_reviewers[:-1]), all_reviewers[-1])

    return body.format(
        sender=sender,
        reviewers=reviewers,
        pr_number=pr_number,
        pr_url=pr_url,
        title=payload['pull_request']['title'] if include_title else None,
    )

def get_check_run_body(payload: Dict[str, Any]) -> str:
    template = """
Check [{name}]({html_url}) {status} ({conclusion}). ([{short_hash}]({commit_url}))
""".strip()

    kwargs = {
        'name': payload['check_run']['name'],
        'html_url': payload['check_run']['html_url'],
        'status': payload['check_run']['status'],
        'short_hash': payload['check_run']['head_sha'][:7],
        'commit_url': "{}/commit/{}".format(
            payload['repository']['html_url'],
            payload['check_run']['head_sha'],
        ),
        'conclusion': payload['check_run']['conclusion'],
    }

    return template.format(**kwargs)

def get_star_body(payload: Dict[str, Any]) -> str:
    template = "{user} {action} the repository."
    return template.format(
        user=payload['sender']['login'],
        action='starred' if payload['action'] == 'created' else 'unstarred',
    )

def get_ping_body(payload: Dict[str, Any]) -> str:
    return get_setup_webhook_message('GitHub', get_sender_name(payload))

def get_repository_name(payload: Dict[str, Any]) -> str:
    return payload['repository']['name']

def get_organization_name(payload: Dict[str, Any]) -> str:
    return payload['organization']['login']

def get_sender_name(payload: Dict[str, Any]) -> str:
    return payload['sender']['login']

def get_branch_name_from_ref(ref_string: str) -> str:
    return re.sub(r'^refs/heads/', '', ref_string)

def get_tag_name_from_ref(ref_string: str) -> str:
    return re.sub(r'^refs/tags/', '', ref_string)

def is_commit_push_event(payload: Dict[str, Any]) -> bool:
    return bool(re.match(r'^refs/heads/', payload['ref']))

def get_subject_based_on_type(payload: Dict[str, Any], event: str) -> str:
    if 'pull_request' in event:
        return TOPIC_WITH_PR_OR_ISSUE_INFO_TEMPLATE.format(
            repo=get_repository_name(payload),
            type='PR',
            id=payload['pull_request']['number'],
            title=payload['pull_request']['title'],
        )
    elif event.startswith('issue'):
        return TOPIC_WITH_PR_OR_ISSUE_INFO_TEMPLATE.format(
            repo=get_repository_name(payload),
            type='Issue',
            id=payload['issue']['number'],
            title=payload['issue']['title'],
        )
    elif event.startswith('deployment'):
        return "{} / Deployment on {}".format(
            get_repository_name(payload),
            payload['deployment']['environment'],
        )
    elif event == 'membership':
        return "{} organization".format(payload['organization']['login'])
    elif event == 'team':
        return "team {}".format(payload['team']['name'])
    elif event == 'push_commits':
        return TOPIC_WITH_BRANCH_TEMPLATE.format(
            repo=get_repository_name(payload),
            branch=get_branch_name_from_ref(payload['ref']),
        )
    elif event == 'gollum':
        return TOPIC_WITH_BRANCH_TEMPLATE.format(
            repo=get_repository_name(payload),
            branch='Wiki Pages',
        )
    elif event == 'ping':
        if payload.get('repository') is None:
            return get_organization_name(payload)
    elif event == 'check_run':
        return f"{get_repository_name(payload)} / checks"

    return get_repository_name(payload)

EVENT_FUNCTION_MAPPER = {
    'commit_comment': get_commit_comment_body,
    'closed_pull_request': get_closed_pull_request_body,
    'create': partial(get_create_or_delete_body, action='created'),
    'check_run': get_check_run_body,
    'delete': partial(get_create_or_delete_body, action='deleted'),
    'deployment': get_deployment_body,
    'deployment_status': get_change_deployment_status_body,
    'fork': get_fork_body,
    'gollum': get_wiki_pages_body,
    'issue_comment': get_issue_comment_body,
    'issues': get_issue_body,
    'member': get_member_body,
    'membership': get_membership_body,
    'opened_or_update_pull_request': get_opened_or_update_pull_request_body,
    'assigned_or_unassigned_pull_request': get_assigned_or_unassigned_pull_request_body,
    'page_build': get_page_build_body,
    'ping': get_ping_body,
    'public': get_public_body,
    'pull_request_ready_for_review': get_pull_request_ready_for_review_body,
    'pull_request_review': get_pull_request_review_body,
    'pull_request_review_comment': get_pull_request_review_comment_body,
    'pull_request_review_requested': get_pull_request_review_requested_body,
    'push_commits': get_push_commits_body,
    'push_tags': get_push_tags_body,
    'release': get_release_body,
    'repository': get_repository_body,
    'star': get_star_body,
    'status': get_status_body,
    'team': get_team_body,
    'team_add': get_add_team_body,
    'watch': get_watch_body,
}

IGNORED_EVENTS = [
    'repository_vulnerability_alert',
    'project_card',
    'check_suite',
    'organization',
    'milestone',
    'meta',
    'label',
]

@api_key_only_webhook_view('GitHub', notify_bot_owner_on_invalid_json=True)
@has_request_variables
def api_github_webhook(
        request: HttpRequest, user_profile: UserProfile,
        payload: Dict[str, Any]=REQ(argument_type='body'),
        branches: Optional[str]=REQ(default=None),
        user_specified_topic: Optional[str]=REQ("topic", default=None)) -> HttpResponse:
    event = get_event(request, payload, branches)
    if event is not None:
        subject = get_subject_based_on_type(payload, event)
        body_function = get_body_function_based_on_type(event)
        if 'include_title' in signature(body_function).parameters:
            body = body_function(
                payload,
                include_title=user_specified_topic is not None,
            )
        else:
            body = body_function(payload)
        check_send_webhook_message(request, user_profile, subject, body)
    return json_success()

def get_event(request: HttpRequest, payload: Dict[str, Any], branches: Optional[str]) -> Optional[str]:
    event = validate_extract_webhook_http_header(request, 'X_GITHUB_EVENT', 'GitHub')
    if event == 'pull_request':
        action = payload['action']
        if action in ('opened', 'synchronize', 'reopened', 'edited'):
            return 'opened_or_update_pull_request'
        if action in ('assigned', 'unassigned'):
            return 'assigned_or_unassigned_pull_request'
        if action == 'closed':
            return 'closed_pull_request'
        if action == 'review_requested':
            return f'{event}_{action}'
        if action == 'ready_for_review':
            return 'pull_request_ready_for_review'
        # Unsupported pull_request events
        if action in ('labeled', 'unlabeled', 'review_request_removed'):
            return None
    elif event == 'push':
        if is_commit_push_event(payload):
            if branches is not None:
                branch = get_branch_name_from_ref(payload['ref'])
                if branches.find(branch) == -1:
                    return None
            return "push_commits"
        else:
            return "push_tags"
    elif event == 'check_run':
        if payload['check_run']['status'] != 'completed':
            return None
        return event
    elif event in list(EVENT_FUNCTION_MAPPER.keys()) or event == 'ping':
        return event
    elif event in IGNORED_EVENTS:
        return None

    complete_event = "{}:{}".format(event, payload.get("action", "???"))  # nocoverage
    raise UnexpectedWebhookEventType('GitHub', complete_event)

def get_body_function_based_on_type(type: str) -> Any:
    return EVENT_FUNCTION_MAPPER.get(type)
