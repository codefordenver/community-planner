from unittest.mock import MagicMock, patch

from zerver.lib.test_classes import WebhookTestCase
from zerver.lib.webhooks.git import COMMITS_LIMIT


class GithubWebhookTest(WebhookTestCase):
    STREAM_NAME = 'github'
    URL_TEMPLATE = "/api/v1/external/github?stream={stream}&api_key={api_key}"
    FIXTURE_DIR_NAME = 'github'
    EXPECTED_TOPIC_REPO_EVENTS = "public-repo"
    EXPECTED_TOPIC_ISSUE_EVENTS = "public-repo / Issue #2 Spelling error in the README file"
    EXPECTED_TOPIC_PR_EVENTS = "public-repo / PR #1 Update the README with new information"
    EXPECTED_TOPIC_DEPLOYMENT_EVENTS = "public-repo / Deployment on production"
    EXPECTED_TOPIC_ORGANIZATION_EVENTS = "baxterandthehackers organization"
    EXPECTED_TOPIC_BRANCH_EVENTS = "public-repo / changes"
    EXPECTED_TOPIC_WIKI_EVENTS = "public-repo / Wiki Pages"

    def test_ping_event(self) -> None:
        expected_message = "GitHub webhook has been successfully configured by TomaszKolek."
        self.send_and_test_stream_message('ping', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_star_event(self) -> None:
        expected_message = "Codertocat starred the repository."
        expected_topic = "Hello-World"
        self.send_and_test_stream_message('star', expected_topic, expected_message)

    def test_ping_organization_event(self) -> None:
        expected_message = "GitHub webhook has been successfully configured by eeshangarg."
        self.send_and_test_stream_message('ping__organization', 'zulip-test-org', expected_message)

    def test_push_delete_branch(self) -> None:
        expected_message = "eeshangarg [deleted](https://github.com/eeshangarg/public-repo/compare/2e8cf535fb38...000000000000) the branch feature."
        self.send_and_test_stream_message('push__delete_branch', "public-repo / feature", expected_message)

    def test_push_local_branch_without_commits(self) -> None:
        expected_message = "eeshangarg [pushed](https://github.com/eeshangarg/public-repo/compare/feature) the branch feature."
        self.send_and_test_stream_message('push__local_branch_without_commits', "public-repo / feature", expected_message)

    def test_push_1_commit(self) -> None:
        expected_message = "baxterthehacker [pushed](https://github.com/baxterthehacker/public-repo/compare/9049f1265b7d...0d1a26e67d8f) 1 commit to branch changes.\n\n* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))"
        self.send_and_test_stream_message('push__1_commit', self.EXPECTED_TOPIC_BRANCH_EVENTS, expected_message)

    def test_push_1_commit_without_username(self) -> None:
        expected_message = "eeshangarg [pushed](https://github.com/eeshangarg/public-repo/compare/0383613da871...2e8cf535fb38) 1 commit to branch changes. Commits by John Snow (1).\n\n* Update the README ([2e8cf53](https://github.com/eeshangarg/public-repo/commit/2e8cf535fb38a3dab2476cdf856efda904ad4c94))"
        self.send_and_test_stream_message('push__1_commit_without_username', self.EXPECTED_TOPIC_BRANCH_EVENTS, expected_message)

    def test_push_1_commit_filtered_by_branches(self) -> None:
        self.url = self.build_webhook_url('master,changes')
        expected_message = "baxterthehacker [pushed](https://github.com/baxterthehacker/public-repo/compare/9049f1265b7d...0d1a26e67d8f) 1 commit to branch changes.\n\n* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))"
        self.send_and_test_stream_message('push__1_commit', self.EXPECTED_TOPIC_BRANCH_EVENTS, expected_message)

    def test_push_multiple_comitters(self) -> None:
        commits_info = '* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))\n'
        expected_message = f"""baxterthehacker [pushed](https://github.com/baxterthehacker/public-repo/compare/9049f1265b7d...0d1a26e67d8f) 6 commits to branch changes. Commits by Tomasz (3), Ben (2) and baxterthehacker (1).\n\n{commits_info * 5}* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))"""

        self.send_and_test_stream_message('push__multiple_committers', self.EXPECTED_TOPIC_BRANCH_EVENTS, expected_message)

    def test_push_multiple_comitters_with_others(self) -> None:
        commits_info = '* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))\n'
        expected_message = f"""baxterthehacker [pushed](https://github.com/baxterthehacker/public-repo/compare/9049f1265b7d...0d1a26e67d8f) 10 commits to branch changes. Commits by Tomasz (4), Ben (3), James (2) and others (1).\n\n{commits_info * 9}* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))"""

        self.send_and_test_stream_message('push__multiple_committers_with_others', self.EXPECTED_TOPIC_BRANCH_EVENTS, expected_message)

    def test_push_multiple_comitters_filtered_by_branches(self) -> None:
        self.url = self.build_webhook_url('master,changes')
        commits_info = '* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))\n'
        expected_message = f"""baxterthehacker [pushed](https://github.com/baxterthehacker/public-repo/compare/9049f1265b7d...0d1a26e67d8f) 6 commits to branch changes. Commits by Tomasz (3), Ben (2) and baxterthehacker (1).\n\n{commits_info * 5}* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))"""

        self.send_and_test_stream_message('push__multiple_committers', self.EXPECTED_TOPIC_BRANCH_EVENTS, expected_message)

    def test_push_multiple_comitters_with_others_filtered_by_branches(self) -> None:
        self.url = self.build_webhook_url('master,changes')
        commits_info = '* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))\n'
        expected_message = f"""baxterthehacker [pushed](https://github.com/baxterthehacker/public-repo/compare/9049f1265b7d...0d1a26e67d8f) 10 commits to branch changes. Commits by Tomasz (4), Ben (3), James (2) and others (1).\n\n{commits_info * 9}* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))"""

        self.send_and_test_stream_message('push__multiple_committers_with_others', self.EXPECTED_TOPIC_BRANCH_EVENTS, expected_message)

    def test_push_50_commits(self) -> None:
        commit_info = "* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))\n"
        expected_message = f"baxterthehacker [pushed](https://github.com/baxterthehacker/public-repo/compare/9049f1265b7d...0d1a26e67d8f) 50 commits to branch changes.\n\n{commit_info * COMMITS_LIMIT}[and 30 more commit(s)]"
        self.send_and_test_stream_message('push__50_commits', self.EXPECTED_TOPIC_BRANCH_EVENTS, expected_message)

    def test_push_50_commits_filtered_by_branches(self) -> None:
        self.url = self.build_webhook_url(branches='master,changes')
        commit_info = "* Update README.md ([0d1a26e](https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c))\n"
        expected_message = f"baxterthehacker [pushed](https://github.com/baxterthehacker/public-repo/compare/9049f1265b7d...0d1a26e67d8f) 50 commits to branch changes.\n\n{commit_info * COMMITS_LIMIT}[and 30 more commit(s)]"
        self.send_and_test_stream_message('push__50_commits', self.EXPECTED_TOPIC_BRANCH_EVENTS, expected_message)

    def test_commit_comment_msg(self) -> None:
        expected_message = "baxterthehacker [commented](https://github.com/baxterthehacker/public-repo/commit/9049f1265b7d61be4a8904a9a27120d2064dab3b#commitcomment-11056394) on [9049f12](https://github.com/baxterthehacker/public-repo/commit/9049f1265b7d61be4a8904a9a27120d2064dab3b):\n~~~ quote\nThis is a really good change! :+1:\n~~~"
        self.send_and_test_stream_message('commit_comment', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_create_msg(self) -> None:
        expected_message = "baxterthehacker created tag 0.0.1."
        self.send_and_test_stream_message('create', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_delete_msg(self) -> None:
        expected_message = "baxterthehacker deleted tag simple-tag."
        self.send_and_test_stream_message('delete', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_deployment_msg(self) -> None:
        expected_message = "baxterthehacker created new deployment."
        self.send_and_test_stream_message('deployment', self.EXPECTED_TOPIC_DEPLOYMENT_EVENTS, expected_message)

    def test_deployment_status_msg(self) -> None:
        expected_message = "Deployment changed status to success."
        self.send_and_test_stream_message('deployment_status', self.EXPECTED_TOPIC_DEPLOYMENT_EVENTS, expected_message)

    def test_fork_msg(self) -> None:
        expected_message = "baxterandthehackers forked [public-repo](https://github.com/baxterandthehackers/public-repo)."
        self.send_and_test_stream_message('fork', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_issue_comment_msg(self) -> None:
        expected_message = "baxterthehacker [commented](https://github.com/baxterthehacker/public-repo/issues/2#issuecomment-99262140) on [Issue #2](https://github.com/baxterthehacker/public-repo/issues/2):\n\n~~~ quote\nYou are totally right! I'll get this fixed right away.\n~~~"
        self.send_and_test_stream_message('issue_comment', self.EXPECTED_TOPIC_ISSUE_EVENTS, expected_message)

    def test_issue_comment_deleted_msg(self) -> None:
        expected_topic = "Scheduler / Issue #5 This is a new issue"
        expected_message = "eeshangarg deleted a [comment](https://github.com/eeshangarg/Scheduler/issues/5#issuecomment-425164194) on [Issue #5](https://github.com/eeshangarg/Scheduler/issues/5):\n\n~~~ quote\nThis is a comment on this new issue.\n~~~"
        self.send_and_test_stream_message('issue_comment__deleted', expected_topic, expected_message)

    def test_issue_comment_msg_with_custom_topic_in_url(self) -> None:
        self.url = self.build_webhook_url(topic='notifications')
        expected_topic = "notifications"
        expected_message = "baxterthehacker [commented](https://github.com/baxterthehacker/public-repo/issues/2#issuecomment-99262140) on [Issue #2 Spelling error in the README file](https://github.com/baxterthehacker/public-repo/issues/2):\n\n~~~ quote\nYou are totally right! I'll get this fixed right away.\n~~~"
        self.send_and_test_stream_message('issue_comment', expected_topic, expected_message)

    def test_issue_msg(self) -> None:
        expected_message = "baxterthehacker opened [Issue #2](https://github.com/baxterthehacker/public-repo/issues/2):\n\n~~~ quote\nIt looks like you accidentally spelled 'commit' with two 't's.\n~~~"
        self.send_and_test_stream_message('issues', self.EXPECTED_TOPIC_ISSUE_EVENTS, expected_message)

    def test_issue_msg_with_custom_topic_in_url(self) -> None:
        self.url = self.build_webhook_url(topic='notifications')
        expected_topic = "notifications"
        expected_message = "baxterthehacker opened [Issue #2 Spelling error in the README file](https://github.com/baxterthehacker/public-repo/issues/2):\n\n~~~ quote\nIt looks like you accidentally spelled 'commit' with two 't's.\n~~~"
        self.send_and_test_stream_message('issues', expected_topic, expected_message)

    def test_membership_msg(self) -> None:
        expected_message = "baxterthehacker added [kdaigle](https://github.com/kdaigle) to the Contractors team."
        self.send_and_test_stream_message('membership', self.EXPECTED_TOPIC_ORGANIZATION_EVENTS, expected_message)

    def test_membership_removal_msg(self) -> None:
        expected_message = "baxterthehacker removed [kdaigle](https://github.com/kdaigle) from the Contractors team."
        self.send_and_test_stream_message('membership__removal', self.EXPECTED_TOPIC_ORGANIZATION_EVENTS, expected_message)

    def test_member_msg(self) -> None:
        expected_message = "baxterthehacker added [octocat](https://github.com/octocat) to [public-repo](https://github.com/baxterthehacker/public-repo)."
        self.send_and_test_stream_message('member', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_pull_request_opened_msg(self) -> None:
        expected_message = "baxterthehacker opened [PR #1](https://github.com/baxterthehacker/public-repo/pull/1) from `changes` to `master`:\n\n~~~ quote\nThis is a pretty simple change that we need to pull into master.\n~~~"
        self.send_and_test_stream_message('pull_request__opened', self.EXPECTED_TOPIC_PR_EVENTS, expected_message)

    def test_pull_request_opened_with_preassigned_assignee_msg(self) -> None:
        expected_topic = "Scheduler / PR #4 Improve README"
        expected_message = "eeshangarg opened [PR #4](https://github.com/eeshangarg/Scheduler/pull/4) (assigned to eeshangarg) from `improve-readme-2` to `master`."
        self.send_and_test_stream_message('pull_request__opened_with_preassigned_assignee', expected_topic, expected_message)

    def test_pull_request_opened_msg_with_custom_topic_in_url(self) -> None:
        self.url = self.build_webhook_url(topic='notifications')
        expected_topic = "notifications"
        expected_message = "baxterthehacker opened [PR #1 Update the README with new information](https://github.com/baxterthehacker/public-repo/pull/1) from `changes` to `master`:\n\n~~~ quote\nThis is a pretty simple change that we need to pull into master.\n~~~"
        self.send_and_test_stream_message('pull_request__opened', expected_topic, expected_message)

    def test_pull_request_synchronized_msg(self) -> None:
        expected_message = "baxterthehacker updated [PR #1](https://github.com/baxterthehacker/public-repo/pull/1) from `changes` to `master`."
        self.send_and_test_stream_message('pull_request__synchronized', self.EXPECTED_TOPIC_PR_EVENTS, expected_message)

    def test_pull_request_closed_msg(self) -> None:
        expected_message = "baxterthehacker closed without merge [PR #1](https://github.com/baxterthehacker/public-repo/pull/1)."
        self.send_and_test_stream_message('pull_request__closed', self.EXPECTED_TOPIC_PR_EVENTS, expected_message)

    def test_pull_request_closed_msg_with_custom_topic_in_url(self) -> None:
        self.url = self.build_webhook_url(topic='notifications')
        expected_topic = "notifications"
        expected_message = "baxterthehacker closed without merge [PR #1 Update the README with new information](https://github.com/baxterthehacker/public-repo/pull/1)."
        self.send_and_test_stream_message('pull_request__closed', expected_topic, expected_message)

    def test_pull_request_merged_msg(self) -> None:
        expected_message = "baxterthehacker merged [PR #1](https://github.com/baxterthehacker/public-repo/pull/1)."
        self.send_and_test_stream_message('pull_request__merged', self.EXPECTED_TOPIC_PR_EVENTS, expected_message)

    def test_public_msg(self) -> None:
        expected_message = "baxterthehacker made [the repository](https://github.com/baxterthehacker/public-repo) public."
        self.send_and_test_stream_message('public', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_wiki_pages_msg(self) -> None:
        expected_message = "jasonrudolph:\n* created [Home](https://github.com/baxterthehacker/public-repo/wiki/Home)\n* created [Home](https://github.com/baxterthehacker/public-repo/wiki/Home)"
        self.send_and_test_stream_message('gollum__wiki_pages', self.EXPECTED_TOPIC_WIKI_EVENTS, expected_message)

    def test_watch_msg(self) -> None:
        expected_message = "baxterthehacker starred [the repository](https://github.com/baxterthehacker/public-repo)."
        self.send_and_test_stream_message('watch__repository', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_repository_msg(self) -> None:
        expected_message = "baxterthehacker created [the repository](https://github.com/baxterandthehackers/public-repo)."
        self.send_and_test_stream_message('repository', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_team_add_msg(self) -> None:
        expected_message = "[The repository](https://github.com/baxterandthehackers/public-repo) was added to team github."
        self.send_and_test_stream_message('team_add', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_release_msg(self) -> None:
        expected_message = "baxterthehacker published release [0.0.1](https://github.com/baxterthehacker/public-repo/releases/tag/0.0.1) for tag 0.0.1."
        self.send_and_test_stream_message('release', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_page_build_msg(self) -> None:
        expected_message = "Github Pages build, triggered by baxterthehacker, has finished building."
        self.send_and_test_stream_message('page_build', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_status_msg(self) -> None:
        expected_message = "[9049f12](https://github.com/baxterthehacker/public-repo/commit/9049f1265b7d61be4a8904a9a27120d2064dab3b) changed its status to success."
        self.send_and_test_stream_message('status', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_status_with_target_url_msg(self) -> None:
        expected_message = "[9049f12](https://github.com/baxterthehacker/public-repo/commit/9049f1265b7d61be4a8904a9a27120d2064dab3b) changed its status to [success](https://example.com/build/status)."
        self.send_and_test_stream_message('status__with_target_url', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_pull_request_review_msg(self) -> None:
        expected_message = "baxterthehacker submitted [PR Review](https://github.com/baxterthehacker/public-repo/pull/1#pullrequestreview-2626884)."
        self.send_and_test_stream_message('pull_request_review', self.EXPECTED_TOPIC_PR_EVENTS, expected_message)

    def test_pull_request_review_msg_with_custom_topic_in_url(self) -> None:
        self.url = self.build_webhook_url(topic='notifications')
        expected_topic = "notifications"
        expected_message = "baxterthehacker submitted [PR Review for #1 Update the README with new information](https://github.com/baxterthehacker/public-repo/pull/1#pullrequestreview-2626884)."
        self.send_and_test_stream_message('pull_request_review', expected_topic, expected_message)

    def test_pull_request_review_comment_msg(self) -> None:
        expected_message = "baxterthehacker created [PR Review Comment](https://github.com/baxterthehacker/public-repo/pull/1#discussion_r29724692):\n\n~~~ quote\nMaybe you should use more emojji on this line.\n~~~"
        self.send_and_test_stream_message('pull_request_review_comment', self.EXPECTED_TOPIC_PR_EVENTS, expected_message)

    def test_pull_request_review_comment_with_custom_topic_in_url(self) -> None:
        self.url = self.build_webhook_url(topic='notifications')
        expected_topic = "notifications"
        expected_message = "baxterthehacker created [PR Review Comment on #1 Update the README with new information](https://github.com/baxterthehacker/public-repo/pull/1#discussion_r29724692):\n\n~~~ quote\nMaybe you should use more emojji on this line.\n~~~"
        self.send_and_test_stream_message('pull_request_review_comment', expected_topic, expected_message)

    def test_push_tag_msg(self) -> None:
        expected_message = "baxterthehacker pushed tag abc."
        self.send_and_test_stream_message('push__tag', self.EXPECTED_TOPIC_REPO_EVENTS, expected_message)

    def test_pull_request_edited_msg(self) -> None:
        expected_message = "baxterthehacker edited [PR #1](https://github.com/baxterthehacker/public-repo/pull/1) from `changes` to `master`."
        self.send_and_test_stream_message('pull_request__edited', self.EXPECTED_TOPIC_PR_EVENTS, expected_message)

    def test_pull_request_assigned_msg(self) -> None:
        expected_message = "baxterthehacker assigned [PR #1](https://github.com/baxterthehacker/public-repo/pull/1) to baxterthehacker."
        self.send_and_test_stream_message('pull_request__assigned', self.EXPECTED_TOPIC_PR_EVENTS, expected_message)

    def test_pull_request_assigned_msg_with_custom_topic_in_url(self) -> None:
        self.url = self.build_webhook_url(topic='notifications')
        expected_topic = "notifications"
        expected_message = "baxterthehacker assigned [PR #1 Update the README with new information](https://github.com/baxterthehacker/public-repo/pull/1) to baxterthehacker."
        self.send_and_test_stream_message('pull_request__assigned', expected_topic, expected_message)

    def test_pull_request_unassigned_msg(self) -> None:
        expected_message = "eeshangarg unassigned [PR #1](https://github.com/zulip-test-org/helloworld/pull/1)."
        self.send_and_test_stream_message('pull_request__unassigned', 'helloworld / PR #1 Mention that Zulip rocks!', expected_message)

    def test_pull_request_ready_for_review_msg(self) -> None:
        expected_message = "**Hypro999** has marked [PR #2](https://github.com/Hypro999/temp-test-github-webhook/pull/2) as ready for review."
        self.send_and_test_stream_message('pull_request__ready_for_review', 'temp-test-github-webhook / PR #2 Test', expected_message)

    def test_pull_request_review_requested_msg(self) -> None:
        expected_message = "**eeshangarg** requested [showell](https://github.com/showell) for a review on [PR #1](https://github.com/eeshangarg/Scheduler/pull/1)."
        self.send_and_test_stream_message('pull_request__review_requested', 'Scheduler / PR #1 This is just a test commit', expected_message)

    def test_pull_request_review_requested_singular_key_msg(self) -> None:
        expected_message = "**eeshangarg** requested [rishig](https://github.com/rishig) for a review on [PR #6](https://github.com/eeshangarg/Scheduler/pull/6)."
        self.send_and_test_stream_message('pull_request__review_requested_singular_key',
                                          'Scheduler / PR #6 Mention how awesome this project is in ...',
                                          expected_message)

    def test_pull_request_review_requested_multiple_reviwers_msg(self) -> None:
        expected_message = "**eeshangarg** requested [showell](https://github.com/showell) and [timabbott](https://github.com/timabbott) for a review on [PR #1](https://github.com/eeshangarg/Scheduler/pull/1)."
        self.send_and_test_stream_message('pull_request__review_requested_multiple_reviewers',
                                          'Scheduler / PR #1 This is just a test commit',
                                          expected_message)

    def test_pull_request__review_requested_team_reviewer_msg(self) -> None:
        expected_message = "**singhsourabh** requested [shreyaskargit](https://github.com/shreyaskargit), [bajaj99prashant](https://github.com/bajaj99prashant), [review-team](https://github.com/orgs/test-org965/teams/review-team), [authority](https://github.com/orgs/test-org965/teams/authority) and [management](https://github.com/orgs/test-org965/teams/management) for a review on [PR #4](https://github.com/test-org965/webhook-test/pull/4)."
        self.send_and_test_stream_message('pull_request__review_requested_team_reviewer',
                                          'webhook-test / PR #4 testing webhook',
                                          expected_message)

    def test_pull_request_review_requested_with_custom_topic_in_url(self) -> None:
        self.url = self.build_webhook_url(topic='notifications')
        expected_topic = "notifications"
        expected_message = "**eeshangarg** requested [showell](https://github.com/showell) for a review on [PR #1 This is just a test commit](https://github.com/eeshangarg/Scheduler/pull/1)."
        self.send_and_test_stream_message('pull_request__review_requested', expected_topic, expected_message)

    def test_check_run(self) -> None:
        expected_topic = "hello-world / checks"
        expected_message = """
Check [randscape](http://github.com/github/hello-world/runs/4) completed (success). ([d6fde92](http://github.com/github/hello-world/commit/d6fde92930d4715a2b49857d24b940956b26d2d3))
""".strip()
        self.send_and_test_stream_message('check_run__completed', expected_topic, expected_message)

    def test_team_edited_description(self) -> None:
        expected_topic = "team Testing"
        expected_message = """\
**Hypro999** changed the team description to:
```quote
A temporary team so that I can get some webhook fixtures!
```"""
        self.send_and_test_stream_message('team__edited_description', expected_topic, expected_message)

    def test_team_edited_name(self) -> None:
        expected_topic = "team Testing Team"
        expected_message = """Team `Testing` was renamed to `Testing Team`."""
        self.send_and_test_stream_message('team__edited_name', expected_topic, expected_message)

    def test_team_edited_privacy(self) -> None:
        expected_topic = "team Testing Team"
        expected_message = """Team visibility changed to `secret`"""
        self.send_and_test_stream_message('team__edited_privacy_secret', expected_topic, expected_message)

    @patch('zerver.webhooks.github.view.check_send_webhook_message')
    def test_check_run_in_progress_ignore(
            self, check_send_webhook_message_mock: MagicMock) -> None:
        payload = self.get_body('check_run__in_progress')
        result = self.client_post(self.url, payload,
                                  HTTP_X_GITHUB_EVENT='check_run',
                                  content_type="application/json")
        self.assertFalse(check_send_webhook_message_mock.called)
        self.assert_json_success(result)

    @patch('zerver.webhooks.github.view.check_send_webhook_message')
    def test_pull_request_labeled_ignore(
            self, check_send_webhook_message_mock: MagicMock) -> None:
        payload = self.get_body('pull_request__labeled')
        result = self.client_post(self.url, payload, HTTP_X_GITHUB_EVENT='pull_request', content_type="application/json")
        self.assertFalse(check_send_webhook_message_mock.called)
        self.assert_json_success(result)

    @patch('zerver.webhooks.github.view.check_send_webhook_message')
    def test_pull_request_unlabeled_ignore(
            self, check_send_webhook_message_mock: MagicMock) -> None:
        payload = self.get_body('pull_request__unlabeled')
        result = self.client_post(self.url, payload, HTTP_X_GITHUB_EVENT='pull_request', content_type="application/json")
        self.assertFalse(check_send_webhook_message_mock.called)
        self.assert_json_success(result)

    @patch('zerver.webhooks.github.view.check_send_webhook_message')
    def test_pull_request_request_review_remove_ignore(
            self, check_send_webhook_message_mock: MagicMock) -> None:
        payload = self.get_body('pull_request__request_review_removed')
        result = self.client_post(self.url, payload, HTTP_X_GITHUB_EVENT='pull_request', content_type="application/json")
        self.assertFalse(check_send_webhook_message_mock.called)
        self.assert_json_success(result)

    @patch('zerver.webhooks.github.view.check_send_webhook_message')
    def test_push_1_commit_filtered_by_branches_ignore(
            self, check_send_webhook_message_mock: MagicMock) -> None:
        self.url = self.build_webhook_url(branches='master,development')
        payload = self.get_body('push__1_commit')
        result = self.client_post(self.url, payload, content_type="application/json", HTTP_X_GITHUB_EVENT="push")
        self.assertFalse(check_send_webhook_message_mock.called)
        self.assert_json_success(result)

    @patch('zerver.webhooks.github.view.check_send_webhook_message')
    def test_push_50_commits_filtered_by_branches_ignore(
            self, check_send_webhook_message_mock: MagicMock) -> None:
        self.url = self.build_webhook_url(branches='master,development')
        payload = self.get_body('push__50_commits')
        result = self.client_post(self.url, payload, content_type="application/json", HTTP_X_GITHUB_EVENT="push")
        self.assertFalse(check_send_webhook_message_mock.called)
        self.assert_json_success(result)

    @patch('zerver.webhooks.github.view.check_send_webhook_message')
    def test_push_multiple_comitters_filtered_by_branches_ignore(
            self, check_send_webhook_message_mock: MagicMock) -> None:
        self.url = self.build_webhook_url(branches='master,development')
        payload = self.get_body('push__multiple_committers')
        result = self.client_post(self.url, payload, content_type="application/json", HTTP_X_GITHUB_EVENT="push")
        self.assertFalse(check_send_webhook_message_mock.called)
        self.assert_json_success(result)

    @patch('zerver.webhooks.github.view.check_send_webhook_message')
    def test_push_multiple_comitters_with_others_filtered_by_branches_ignore(
            self, check_send_webhook_message_mock: MagicMock) -> None:
        self.url = self.build_webhook_url(branches='master,development')
        payload = self.get_body('push__multiple_committers_with_others')
        result = self.client_post(self.url, payload, content_type="application/json", HTTP_X_GITHUB_EVENT="push")
        self.assertFalse(check_send_webhook_message_mock.called)
        self.assert_json_success(result)

    @patch('zerver.webhooks.github.view.check_send_webhook_message')
    def test_repository_vulnerability_alert_ignore(
            self, check_send_webhook_message_mock: MagicMock) -> None:
        self.url = self.build_webhook_url()
        payload = self.get_body('repository_vulnerability_alert')
        result = self.client_post(self.url, payload,
                                  HTTP_X_GITHUB_EVENT='repository_vulnerability_alert',
                                  content_type="application/json")
        self.assertFalse(check_send_webhook_message_mock.called)
        self.assert_json_success(result)
