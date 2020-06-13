exports.do_unread_count_updates = function do_unread_count_updates(messages) {
    unread.process_loaded_messages(messages);
    unread_ui.update_unread_counts();
    resize.resize_page_components();
};

function add_messages(messages, msg_list, opts) {
    if (!messages) {
        return;
    }

    loading.destroy_indicator($('#page_loading_indicator'));

    const render_info = msg_list.add_messages(messages, opts);

    return render_info;
}

exports.add_old_messages = function (messages, msg_list) {
    return add_messages(messages, msg_list, {messages_are_new: false});
};
exports.add_new_messages = function (messages, msg_list) {
    return add_messages(messages, msg_list, {messages_are_new: true});
};

exports.get_messages_in_topic = function (stream_id, topic) {
    // This function is very expensive since it searches
    // all the messages. Please only use it in case of
    // very rare events like topic edits. Its primary
    // use case is the new experimental Recent Topics UI.
    return message_list.all.all_messages().filter(x => {
        return x.type === 'stream' &&
               x.stream_id === stream_id &&
               x.topic.toLowerCase() === topic.toLowerCase();
    });
};

window.message_util = exports;
