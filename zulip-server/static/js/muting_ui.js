const render_muted_topic_ui_row = require('../templates/muted_topic_ui_row.hbs');
const render_topic_muted = require('../templates/topic_muted.hbs');

function timestamp_ms() {
    return new Date().getTime();
}

let last_topic_update = 0;

exports.rerender = function () {
    // Note: We tend to optimistically rerender muting preferences before
    // the back end actually acknowledges the mute.  This gives a more
    // immediate feel to the user, and if the back end fails temporarily,
    // re-doing a mute or unmute is a pretty recoverable thing.

    stream_list.update_streams_sidebar();
    if (current_msg_list.muting_enabled) {
        current_msg_list.update_muting_and_rerender();
    }
    if (current_msg_list !== home_msg_list) {
        home_msg_list.update_muting_and_rerender();
    }
    exports.set_up_muted_topics_ui();
};

exports.persist_mute = function (stream_id, topic_name) {
    const data = {
        stream_id: stream_id,
        topic: topic_name,
        op: 'add',
    };
    last_topic_update = timestamp_ms();
    channel.patch({
        url: '/json/users/me/subscriptions/muted_topics',
        idempotent: true,
        data: data,
    });
};

exports.persist_unmute = function (stream_id, topic_name) {
    const data = {
        stream_id: stream_id,
        topic: topic_name,
        op: 'remove',
    };
    last_topic_update = timestamp_ms();
    channel.patch({
        url: '/json/users/me/subscriptions/muted_topics',
        idempotent: true,
        data: data,
    });
};

exports.handle_updates = function (muted_topics) {
    if (timestamp_ms() < last_topic_update + 1000) {
        // This topic update is either the one that we just rendered, or,
        // much less likely, it's coming from another device and would probably
        // be overwriting this device's preferences with stale data.
        return;
    }

    exports.update_muted_topics(muted_topics);
    exports.rerender();
};

exports.update_muted_topics = function (muted_topics) {
    muting.set_muted_topics(muted_topics);
    unread_ui.update_unread_counts();
};

exports.set_up_muted_topics_ui = function () {
    const muted_topics = muting.get_muted_topics();
    const muted_topics_table = $("#muted_topics_table");
    const $search_input = $("#muted_topics_search");

    list_render.create(muted_topics_table, muted_topics, {
        name: "muted-topics-list",
        modifier: function (muted_topics) {
            return render_muted_topic_ui_row({ muted_topics: muted_topics });
        },
        filter: {
            element: $search_input,
            predicate: function (item, value) {
                return item.topic.toLocaleLowerCase().indexOf(value) >= 0;
            },
            onupdate: function () {
                ui.reset_scrollbar(muted_topics_table.closest(".progressive-table-wrapper"));
            },
        },
        parent_container: $('#muted-topic-settings'),
    });
};

exports.mute = function (stream_id, topic) {
    const stream_name = stream_data.maybe_get_stream_name(stream_id);

    stream_popover.hide_topic_popover();
    muting.add_muted_topic(stream_id, topic);
    unread_ui.update_unread_counts();
    exports.rerender();
    exports.persist_mute(stream_id, topic);
    feedback_widget.show({
        populate: function (container) {
            const rendered_html = render_topic_muted();
            container.html(rendered_html);
            container.find(".stream").text(stream_name);
            container.find(".topic").text(topic);
        },
        on_undo: function () {
            exports.unmute(stream_id, topic);
        },
        title_text: i18n.t("Topic muted"),
        undo_button_text: i18n.t("Unmute"),
    });
    recent_topics.update_topic_is_muted(stream_id, topic);
};

exports.unmute = function (stream_id, topic) {
    // we don't run a unmute_notify function because it isn't an issue as much
    // if someone accidentally unmutes a stream rather than if they mute it
    // and miss out on info.
    stream_popover.hide_topic_popover();
    muting.remove_muted_topic(stream_id, topic);
    unread_ui.update_unread_counts();
    exports.rerender();
    exports.persist_unmute(stream_id, topic);
    feedback_widget.dismiss();
    recent_topics.update_topic_is_muted(stream_id, topic);
};

exports.toggle_mute = function (message) {
    const stream_id = message.stream_id;
    const topic = message.topic;

    if (muting.is_topic_muted(stream_id, topic)) {
        exports.unmute(stream_id, topic);
    } else if (message.type === 'stream') {
        exports.mute(stream_id, topic);
    }
};

window.muting_ui = exports;
