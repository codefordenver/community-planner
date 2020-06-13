var common = require('../casper_lib/common.js');

common.start_and_log_in();

casper.waitUntilVisible('#zhome', function () {
    casper.test.info('compose box visible');
    casper.page.sendEvent('keypress', "c"); // brings up the compose box
});

casper.then(function () {
    casper.fill('form[action^="/json/messages"]', {
        stream_message_recipient_stream: 'Verona',
        stream_message_recipient_topic: 'Test mention all',
    });
});
common.select_item_via_typeahead('#compose-textarea', '@**all**', 'all');

casper.then(function () {
    common.turn_off_press_enter_to_send();
    casper.test.info("Checking for all everyone warning");
    var stream_size = this.evaluate(function () {
        return stream_data.get_sub('Verona').subscribers.size;
    });
    casper.test.info(stream_size);
    var threshold = this.evaluate(function () {
        compose.all_everyone_warn_threshold = 5;
        return compose.all_everyone_warn_threshold;
    });
    casper.test.assertTrue(stream_size > threshold);
    casper.test.info('Click Send Button');
    casper.click('#compose-send-button');
});

casper.then(function () {
    common.wait_for_text(".compose-all-everyone-msg", "Are you sure you want to mention all", function () {
        casper.test.info('Warning message appears when mentioning @**all**');
        casper.test.assertSelectorHasText('.compose-all-everyone-msg', 'Are you sure you want to mention all');
        casper.click('.compose-all-everyone-confirm');
    });

    casper.waitWhileVisible('.compose-all-everyone-confirm', function () {
        casper.test.info('Check that error messages are gone.');
        casper.test.assertNotVisible('.compose-all-everyone-msg');
        casper.test.assertNotVisible('#compose-send-status');
    });
});

casper.then(function () {
    common.expected_messages('zhome', ['Verona > Test mention all'],
                             ["<p><span class=\"user-mention user-mention-me\" " +
                              "data-user-id=\"*\">@all</span></p>"]);
});


common.then_log_out();

casper.run(function () {
    casper.test.done();
});
