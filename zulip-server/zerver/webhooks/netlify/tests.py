from zerver.lib.test_classes import WebhookTestCase


class NetlifyHookTests(WebhookTestCase):
    STREAM_NAME = 'netlify'
    URL_TEMPLATE = "/api/v1/external/netlify?stream={stream}&api_key={api_key}"
    FIXTURE_DIR_NAME = "netlify"

    def test_building_message(self) -> None:
        expected_topic = "master"
        expected_message = 'The build [objective-jepsen-35fbb2](http://objective-jepsen-35fbb2.netlify.com) on branch master is now building.'

        self.send_and_test_stream_message('deploy_building', expected_topic, expected_message,
                                          content_type="application/json")

    def test_created_message(self) -> None:
        expected_topic = "master"
        expected_message = 'The build [objective-jepsen-35fbb2](http://objective-jepsen-35fbb2.netlify.com) on branch master is now ready.'

        self.send_and_test_stream_message('deploy_created', expected_topic, expected_message,
                                          content_type="application/json")

    def test_failed_message(self) -> None:
        expected_topic = "master"
        expected_message = ("The build [objective-jepsen-35fbb2](http://objective-jepsen-35fbb2.netlify.com) "
                            "on branch master failed during stage 'building site': Build script returned non-zero exit code: 127"
                            )

        self.send_and_test_stream_message('deploy_failed', expected_topic, expected_message,
                                          content_type="application/json")

    def test_locked_message(self) -> None:
        expected_topic = "master"
        expected_message = ("The build [objective-jepsen-35fbb2](http://objective-jepsen-35fbb2.netlify.com) "
                            "on branch master is now locked."
                            )

        self.send_and_test_stream_message('deploy_locked', expected_topic, expected_message,
                                          content_type="application/json")

    def test_unlocked_message(self) -> None:
        expected_topic = "master"
        expected_message = ("The build [objective-jepsen-35fbb2](http://objective-jepsen-35fbb2.netlify.com) "
                            "on branch master is now unlocked."
                            )

        self.send_and_test_stream_message('deploy_unlocked', expected_topic, expected_message,
                                          content_type="application/json")

    def get_body(self, fixture_name: str) -> str:
        return self.webhook_fixture_data("netlify", fixture_name, file_type="json")
