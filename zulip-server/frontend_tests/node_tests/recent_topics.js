zrequire('message_util');

const noop = () => {};
set_global('$', global.make_zjquery({
    silent: true,
}));
set_global('hashchange', {
    exit_overlay: noop,
});
set_global('stream_data', {
    get_sub: () => {
        return {
            color: "",
            invite_only: false,
            is_web_public: true,
        };
    },
    is_muted: () => {
        // We only test via muted topics for now.
        // TODO: Make muted streams and test them.
        return false;
    },
});
set_global('overlays', {
    open_overlay: (opts) => {
        overlays.close_callback = opts.on_close;
    },
    recent_topics_open: () => {
        return true;
    },
});
set_global('people', {
    is_my_user_id: function (id) {
        return id === 1;
    },
    sender_info_with_small_avatar_urls_for_sender_ids: (ids) => {
        return ids;
    },
});
set_global('XDate', zrequire('XDate', 'xdate'));
set_global('timerender', {
    last_seen_status_from_date: () => {
        return "Just now";
    },
});
set_global('unread', {
    unread_topic_counter: {
        get: (stream_id, topic) => {
            if (stream_id === 1 && topic === "topic-1") {
                // Only stream1, topic-1 is read.
                return 0;
            }
            return 1;
        },
    },
});
set_global('hash_util', {
    by_stream_uri: () => {
        return "https://www.example.com";
    },
    by_stream_topic_uri: () => {
        return "https://www.example.com";
    },
});
set_global('recent_senders', {
    get_topic_recent_senders: () => { return [1, 2]; },
});
set_global('list_render', {
    modifier: noop,
    create: (container, mapped_topic_values, opts) => {
        const formatted_topics = [];
        list_render.modifier = opts.modifier;
        for (const item of mapped_topic_values) {
            formatted_topics.push(opts.modifier(item));
            opts.filter.predicate(item);
        }
        // Just for coverage, the mechanisms
        // are tested in list_render
        if (mapped_topic_values.length >= 2) {
            opts.sort_fields.stream_sort(mapped_topic_values[0], mapped_topic_values[1]);
            opts.sort_fields.stream_sort(mapped_topic_values[1], mapped_topic_values[0]);
            opts.sort_fields.stream_sort(mapped_topic_values[0], mapped_topic_values[0]);
            opts.sort_fields.topic_sort(mapped_topic_values[0], mapped_topic_values[1]);
            opts.sort_fields.topic_sort(mapped_topic_values[1], mapped_topic_values[0]);
            opts.sort_fields.topic_sort(mapped_topic_values[0], mapped_topic_values[0]);
        }
        return list_render;
    },
    hard_redraw: noop,
    render_item: (item) => {
        return list_render.modifier(item);
    },
});

// Custom Data

// New stream
const stream1 = 1;
const stream2 = 2;
const stream3 = 3;
const stream4 = 4;

// Topics in the stream, all unread except topic1 & stream1.
const topic1 = "topic-1";  // No Other sender & read.
const topic2 = "topic-2";  // Other sender
const topic3 = "topic-3";  // User not present
const topic4 = "topic-4";  // User not present
const topic5 = "topic-5";  // other sender
const topic6 = "topic-6";  // other sender
const topic7 = "topic-7";  // muted topic
const topic8 = "topic-8";
const topic9 = "topic-9";
const topic10 = "topic-10";

set_global('muting', {
    is_topic_muted: (stream_id, topic) => {
        if (stream_id === stream1 && topic === topic7) {
            return true;
        }
        return false;
    },
});

// sender1 == current user
// sender2 == any other user
const sender1 = 1;
const sender2 = 2;

const messages = [];

set_global('message_list', {
    all: {
        all_messages: function () {
            return messages;
        },
    },
});
set_global('message_store', {
    get: (msg_id) => {
        return messages[msg_id - 1];
    },
});

let id = 0;

messages[0] = {
    stream_id: stream1,
    stream: 'stream1',
    id: id += 1,
    topic: topic1,
    sender_id: sender1,
    type: 'stream',
};

messages[1] = {
    stream_id: stream1,
    stream: 'stream1',
    id: id += 1,
    topic: topic2,
    sender_id: sender1,
    type: 'stream',
};

messages[2] = {
    stream_id: stream1,
    stream: 'stream1',
    id: id += 1,
    topic: topic2,
    sender_id: sender2,
    type: 'stream',
};

messages[3] = {
    stream_id: stream1,
    stream: 'stream1',
    id: id += 1,
    topic: topic3,
    sender_id: sender2,
    type: 'stream',
};

messages[4] = {
    stream_id: stream1,
    stream: 'stream1',
    id: id += 1,
    topic: topic4,
    sender_id: sender2,
    type: 'stream',
};

messages[5] = {
    stream_id: stream1,
    stream: 'stream1',
    id: id += 1,
    topic: topic5,
    sender_id: sender1,
    type: 'stream',
};

messages[6] = {
    stream_id: stream1,
    stream: 'stream1',
    id: id += 1,
    topic: topic5,
    sender_id: sender2,
    type: 'stream',
};

messages[7] = {
    stream_id: stream1,
    stream: 'stream1',
    id: id += 1,
    topic: topic6,
    sender_id: sender1,
    type: 'stream',
};

messages[8] = {
    stream_id: stream1,
    stream: 'stream1',
    id: id += 1,
    topic: topic6,
    sender_id: sender2,
    type: 'stream',
};

messages[9] = {
    stream_id: stream1,
    stream: 'stream1',
    id: id += 1,
    topic: topic7,
    sender_id: sender1,
    type: 'stream',
};

// a message of stream4
messages[10] = {
    stream_id: stream4,
    stream: 'stream4',
    id: id += 1,
    topic: topic10,
    sender_id: sender1,
    type: 'stream',
};

function generate_topic_data(topic_info_array) {
    // Since most of the fields are common, this function helps generate fixtures
    // with non common fields.
    $.clear_all_elements();
    const data = [];
    const selectors = [];

    for (const [stream_id, topic, unread_count, muted, participated] of topic_info_array) {
        const topic_selector = $.create('#recent_topic:' + stream_id + ":" + topic);
        topic_selector.data = function () {
            return {
                participated: participated,
                muted: muted,
                unreadCount: unread_count,
            };
        };

        selectors.push(topic_selector);
        data.push({
            count_senders: 0,
            invite_only: false,
            is_web_public: true,
            last_msg_time: 'Just now',
            senders: [
                1,
                2,
            ],
            stream: 'stream' + stream_id,
            stream_color: '',
            stream_id: stream_id,
            stream_url: 'https://www.example.com',
            topic: topic,
            topic_url: 'https://www.example.com',
            unread_count: unread_count,
            muted: muted,
            topic_muted: muted,
            participated: participated,
        });
    }
    return data;
}

function verify_topic_data(all_topics, stream, topic, last_msg_id,
                           participated) {
    const topic_data = all_topics.get(stream + ':' + topic);
    assert.equal(topic_data.last_msg_id, last_msg_id);
    assert.equal(topic_data.participated, participated);
}

run_test("test_recent_topics_launch", () => {
    // Note: unread count and urls are fake,
    // since they are generated in external libraries
    // and are not to be tested here.
    const expected = {
        filter_participated: true,
        filter_unread: true,
        filter_muted: false,
        search_val: '',
    };

    global.stub_templates(function (template_name, data) {
        if (template_name === 'recent_topics_table') {
            assert.deepEqual(data, expected);
        } else if (template_name === 'recent_topics_filters') {
            assert.equal(data.filter_unread, expected.filter_unread);
            assert.equal(data.filter_participated, expected.filter_participated);
        }
        return '<recent_topics table stub>';
    });

    const rt = zrequire('recent_topics');
    rt.process_messages(messages);

    rt.launch();
    assert.equal($("#recent_topics_search").is(":focus"), true);
    overlays.close_callback();

    // incorrect topic_key
    assert.equal(rt.inplace_rerender('stream_unknown:topic_unknown'), false);
});

run_test('test_filter_all', () => {
    // Just tests inplace rerender of a message
    // in All topics filter.
    const expected = {
        filter_participated: false,
        filter_unread: false,
        filter_muted: false,
        search_val: "",
    };
    let row_data;
    let i;
    global.stub_templates(function (template_name, data) {
        if (template_name === 'recent_topic_row') {
            // All the row will be processed.
            i -= 1;
            assert.deepEqual(data, row_data[i]);
        } else if (template_name === 'recent_topics_table') {
            assert.deepEqual(data, expected);
        }
        return '<recent_topics row stub>';
    });

    // topic is not muted
    row_data = generate_topic_data([[1, 'topic-1', 0, false, true]]);
    i = row_data.length;
    const rt = zrequire('recent_topics');
    rt.set_filter('all');
    rt.process_messages([messages[0]]);

    row_data = row_data.concat(generate_topic_data([[1, 'topic-7', 1, true, true]]));
    i = row_data.length;
    // topic is muted (=== hidden)
    rt.process_messages([messages[9]]);

    // Test search
    expected.search_val = "topic-1";
    row_data = generate_topic_data([[1, 'topic-1', 0, false, true]]);
    const search_element = $.create("#recent_topics_search");
    search_element.val('topic-3');
    i = row_data.length;
    assert.equal(rt.inplace_rerender('1:topic-1'), true);
});

run_test('test_filter_unread', () => {
    // Tests rerender of all topics when filter changes to "unread".
    const expected = {
        filter_participated: false,
        filter_unread: true,
        filter_muted: false,
        search_val: '',
    };

    const row_data = generate_topic_data([
        // stream_id, topic, unread_count,  muted, participated
        [4, 'topic-10', 1, false, true],
        [1, 'topic-7', 1, true, true],
        [1, 'topic-6', 1, false, true],
        [1, 'topic-5', 1, false, true],
        [1, 'topic-4', 1, false, false],
        [1, 'topic-3', 1, false, false],
        [1, 'topic-2', 1, false, true],
        [1, 'topic-1', 0, false, true],
    ]);
    let i = 0;

    const rt = zrequire('recent_topics');

    global.stub_templates(function () {
        return '<recent_topics table stub>';
    });
    rt.process_messages(messages);
    assert.equal(rt.inplace_rerender('1:topic-1'), true);

    global.stub_templates(function (template_name, data) {
        assert.equal(template_name, 'recent_topics_filters');
        assert.equal(data.filter_unread, expected.filter_unread);
        assert.equal(data.filter_participated, expected.filter_participated);
        return '<recent_topics table stub>';
    });

    // This will deselect participated and leave only unread selected.
    rt.set_filter('participated');
    rt.update_filters_view();

    global.stub_templates(function (template_name, data) {
        if (template_name === 'recent_topic_row') {
            // All the row will be processed.
            assert.deepEqual(data, row_data[i]);
            i += 1;
        } else if (template_name === 'recent_topics_table') {
            assert.deepEqual(data, expected);
        }
        return '<recent_topics row stub>';
    });
    rt.process_messages([messages[0]]);

    // Unselect "unread" filter by clicking twice.
    expected.filter_unread = false;
    $('#recent_topics_filter_buttons').addClass('btn-recent-selected');
    rt.set_filter('unread');

    $('#recent_topics_filter_buttons').removeClass('btn-recent-selected');
    // reselect "unread" filter
    rt.set_filter('unread');

    // Now clicking "all" filter should have no change to expected data.
    rt.set_filter('all');
});

run_test('test_filter_participated', () => {
    // Tests rerender of all topics when filter changes to "unread".
    const expected = {
        filter_participated: true,
        filter_unread: false,
        filter_muted: false,
        search_val: '',
    };

    const row_data = generate_topic_data([
        // stream_id, topic, unread_count,  muted, participated
        [4, 'topic-10', 1, false, true],
        [1, 'topic-7', 1, true, true],
        [1, 'topic-6', 1, false, true],
        [1, 'topic-5', 1, false, true],
        [1, 'topic-4', 1, false, false],
        [1, 'topic-3', 1, false, false],
        [1, 'topic-2', 1, false, true],
        [1, 'topic-1', 0, false, true],
    ]);
    let i = 0;

    const rt = zrequire('recent_topics');

    global.stub_templates(function () {
        return '<recent_topics table stub>';
    });
    rt.process_messages(messages);
    assert.equal(rt.inplace_rerender('1:topic-4'), true);

    // Set muted filter
    rt.set_filter('muted');
    assert.equal(rt.inplace_rerender('1:topic-7'), true);

    // remove muted filter
    rt.set_filter('muted');

    global.stub_templates(function (template_name, data) {
        assert.equal(template_name, 'recent_topics_filters');
        assert.equal(data.filter_unread, expected.filter_unread);
        assert.equal(data.filter_participated, expected.filter_participated);
        return '<recent_topics table stub>';
    });
    rt.set_filter('unread');
    rt.update_filters_view();


    global.stub_templates(function (template_name, data) {
        if (template_name === 'recent_topic_row') {
            // All the row will be processed.
            assert.deepEqual(data, row_data[i]);
            i += 1;
        } else if (template_name === 'recent_topics_table') {
            assert.deepEqual(data, expected);
        }
        return '<recent_topics row stub>';
    });
    rt.process_messages([messages[4]]);

    expected.filter_participated = false;
    rt.set_filter('all');
});

run_test('test_update_unread_count', () => {
    const rt = zrequire('recent_topics');
    rt.set_filter('all');
    global.stub_templates(function () {
        return '<recent_topics table stub>';
    });
    rt.process_messages(messages);

    // update a message
    generate_topic_data([[1, 'topic-7', 1, false, true]]);
    rt.update_topic_unread_count([messages[9]]);
});

// template rendering is tested in test_recent_topics_launch.
global.stub_templates(function () {
    return '<recent_topics table stub>';
});

run_test('basic assertions', () => {
    const rt = zrequire('recent_topics');
    rt.set_filter('all');
    rt.process_messages(messages);
    let all_topics = rt.get();

    // update a message
    generate_topic_data([[1, 'topic-7', 1, false, true]]);
    rt.process_messages([messages[9]]);
    // Check for expected lengths.
    // total 8 topics, 1 muted
    assert.equal(all_topics.size, 8);
    assert.equal(Array.from(all_topics.keys()).toString(),
                 '4:topic-10,1:topic-7,1:topic-6,1:topic-5,1:topic-4,1:topic-3,1:topic-2,1:topic-1');

    rt.process_message({
        type: 'private',
    });

    // Private msgs are not processed.
    assert.equal(all_topics.size, 8);
    assert.equal(Array.from(all_topics.keys()).toString(),
                 '4:topic-10,1:topic-7,1:topic-6,1:topic-5,1:topic-4,1:topic-3,1:topic-2,1:topic-1');

    // participated
    verify_topic_data(all_topics, stream1, topic1, messages[0].id, true);

    // No message was sent by us.
    verify_topic_data(all_topics, stream1, topic3, messages[3].id, false);

    // Not participated
    verify_topic_data(all_topics, stream1, topic4, messages[4].id, false);

    // topic3 now participated
    rt.process_message({
        stream_id: stream1,
        id: id += 1,
        topic: topic3,
        sender_id: sender1,
        type: 'stream',
    });

    all_topics = rt.get();
    assert.equal(Array.from(all_topics.keys()).toString(),
                 '1:topic-3,4:topic-10,1:topic-7,1:topic-6,1:topic-5,1:topic-4,1:topic-2,1:topic-1');
    verify_topic_data(all_topics, stream1, topic3, id, true);

    // Send new message to topic7 (muted)
    // The topic will be hidden when displayed
    rt.process_message({
        stream_id: stream1,
        id: id += 1,
        topic: topic7,
        sender_id: sender1,
        type: 'stream',
    });

    all_topics = rt.get();
    assert.equal(Array.from(all_topics.keys()).toString(),
                 '1:topic-7,1:topic-3,4:topic-10,1:topic-6,1:topic-5,1:topic-4,1:topic-2,1:topic-1');

    // update_topic_is_muted now relies on external libraries completely
    // so we don't need to check anythere here.
    generate_topic_data([[1, topic1, 0, false, true]]);
    assert.equal(rt.update_topic_is_muted(stream1, topic1), true);
    // a topic gets muted which we are not tracking
    assert.equal(rt.update_topic_is_muted(stream1, "topic-10"), false);
});

run_test('test_reify_local_echo_message', () => {
    const rt = zrequire('recent_topics');
    rt.set_filter('all');
    rt.process_messages(messages);

    rt.process_message({
        stream_id: stream1,
        id: 1000.01,
        topic: topic7,
        sender_id: sender1,
        type: 'stream',
    }, false);

    assert.equal(rt.reify_message_id_if_available({
        old_id: 1000.01,
        new_id: 1001,
    }), true);

    rt.process_message({
        stream_id: stream1,
        id: 1001.01,
        topic: topic7,
        sender_id: sender1,
        type: 'stream',
    }, false);

    // A new message arrived in the same topic before we could reify the message_id
    rt.process_message({
        stream_id: stream1,
        id: 1003,
        topic: topic7,
        sender_id: sender1,
        type: 'stream',
    }, false);

    assert.equal(rt.reify_message_id_if_available({
        old_id: 1000.01,
        new_id: 1001,
    }), false);
});

run_test('test_topic_edit', () => {
    // NOTE: This test should always run in the end as it modified the messages data.
    const rt = zrequire('recent_topics');
    rt.set_filter('all');
    rt.process_messages(messages);

    let all_topics = rt.get();
    assert.equal(Array.from(all_topics.keys()).toString(),
                 '4:topic-10,1:topic-7,1:topic-6,1:topic-5,1:topic-4,1:topic-3,1:topic-2,1:topic-1');

    ////////////////// test change topic //////////////////
    verify_topic_data(all_topics, stream1, topic6, messages[8].id, true);
    assert.equal(all_topics.get(stream1 + ":" + topic8), undefined);

    let topic_selector = $.create('#recent_topic:' + stream1 + ":" + topic8);
    topic_selector.data = function () {
        return {
            participated: true,
            muted: false,
            unreadCount: 1,
        };
    };
    // change topic of topic6 to topic8
    messages[7].topic = topic8;
    messages[8].topic = topic8;
    rt.process_topic_edit(stream1, topic6, topic8);
    all_topics = rt.get();

    verify_topic_data(all_topics, stream1, topic8, messages[8].id, true);
    assert.equal(all_topics.get(stream1 + ":" + topic6), undefined);

    ////////////////// test stream change //////////////////
    verify_topic_data(all_topics, stream1, topic1, messages[0].id, true);
    assert.equal(all_topics.get(stream2 + ":" + topic1), undefined);

    topic_selector = $.create('#recent_topic:' + stream2 + ":" + topic1);
    topic_selector.data = function () {
        return {
            participated: true,
            muted: false,
            unreadCount: 0,
        };
    };
    messages[0].stream_id = stream2;
    rt.process_topic_edit(stream1, topic1, topic1, stream2);
    all_topics = rt.get();

    assert.equal(all_topics.get(stream1 + ":" + topic1), undefined);
    verify_topic_data(all_topics, stream2, topic1, messages[0].id, true);

    ////////////////// test stream & topic change //////////////////
    verify_topic_data(all_topics, stream2, topic1, messages[0].id, true);
    assert.equal(all_topics.get(stream3 + ":" + topic9), undefined);

    topic_selector = $.create('#recent_topic:' + stream3 + ":" + topic9);
    topic_selector.data = function () {
        return {
            participated: false,
            muted: false,
            unreadCount: 1,
        };
    };
    messages[0].stream_id = stream3;
    messages[0].topic = topic9;
    rt.process_topic_edit(stream2, topic1, topic9, stream3);
    all_topics = rt.get();

    assert.equal(all_topics.get(stream2 + ":" + topic1), undefined);
    verify_topic_data(all_topics, stream3, topic9, messages[0].id, true);
});
