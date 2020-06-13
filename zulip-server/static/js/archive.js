const render_archive_message_group = require('../templates/archive_message_group.hbs');

function should_separate_into_groups(current_msg_time, next_msg_time) {
    const current_time = new XDate(current_msg_time * 1000);
    const next_time = new XDate(next_msg_time * 1000);
    return current_time.toDateString() !== next_time.toDateString();
}

function all_message_timestamps_to_human_readable() {
    $('.message_time').each(function () {
        const time = new XDate(parseInt($(this).text(), 10) * 1000);
        $(this).text(time.toString('h:mm TT'));
    });
}


exports.initialize = function () {
    const all_message_groups = [];
    let current_message_group = {};
    const today = new XDate();
    const recipient_and_topic = $('#display_recipient').html();
    const stream_name = recipient_and_topic.split('-')[0];
    const topic = recipient_and_topic.split('-')[1];
    const recipient_color = color_data.pick_color();
    current_message_group.message_containers = [];
    current_message_group.show_group_date_divider = false;
    current_message_group.display_recipient = stream_name;
    current_message_group.topic = topic;
    current_message_group.background_color = recipient_color;

    function separate_into_groups(current_message_row, cur_msg_time, next_msg_time) {
        const time = new XDate(next_msg_time * 1000);
        const prev_time = new XDate(cur_msg_time * 1000);
        current_message_group.message_containers.push(current_message_row[0].outerHTML);
        const date_element = timerender.render_date(prev_time, undefined, today)[0];
        current_message_group.date = date_element.outerHTML;
        all_message_groups.push(current_message_group);
        current_message_group = {};
        current_message_group.message_containers = [];
        current_message_group.group_date_divider_html =
            timerender.render_date(time, prev_time, today)[0].outerHTML;
        current_message_group.show_group_date_divider = true;
        current_message_group.display_recipient = stream_name;
        current_message_group.topic = topic;
        current_message_group.background_color = recipient_color;
    }

    $('.message_row').each(function () {
        const current_message_row = $(this);
        const cur_msg_time = parseInt(current_message_row.find('.message_time').first().html(), 10);
        const next_msg_time = parseInt(current_message_row.next().find('.message_time').first().html(), 10);

        if (current_message_row.next().length === 0) {
            separate_into_groups(current_message_row, cur_msg_time);
            return;
        }

        if (should_separate_into_groups(cur_msg_time, next_msg_time)) {
            separate_into_groups(current_message_row, cur_msg_time, next_msg_time);
            return;
        }
        current_message_group.message_containers.push(current_message_row[0].outerHTML);
        const time = new XDate(cur_msg_time * 1000);
        const date_element = timerender.render_date(time, undefined, today)[0];
        current_message_group.date = date_element.outerHTML;
    });

    const context = {
        message_groups: all_message_groups,
    };
    const message_groups_html = render_archive_message_group(context);
    $('.message_row').each(function () {
        $(this).detach();
    });
    $('.message_table').prepend(message_groups_html);
    $('.messagebox').css('box-shadow', 'inset 2px 0px 0px 0px ' + recipient_color);
    $('#display_recipient').remove();

    // Fixing include_sender after rendering groups.
    let prev_sender;
    $('.recipient_row').each(function () {
        if (prev_sender !== undefined) {
            const first_group_msg = $(this).find('.message_row').first();
            const message_sender = first_group_msg.find('.message_sender');
            if (!message_sender.find('.inline_profile_picture').length) {
                message_sender.replaceWith(prev_sender.clone());
            }
        }
        const all_senders = $(this).find('.message_sender').has('.inline_profile_picture');
        prev_sender = all_senders.last();
    });

    $('.app').scrollTop($('.app').height());
    all_message_timestamps_to_human_readable();
};

exports.current_msg_list = {
    selected_row: function () {
        return $('.message_row').last();
    },
};
exports.rows = {
    get_message_recipient_row: function (message_row) {
        return $(message_row).parent('.recipient_row');
    },
    first_message_in_group: function (message_group) {
        return $('div.message_row', message_group).first();
    },
    id: function (message_row) {
        return parseFloat(message_row.attr('zid'));
    },
};

let scroll_timer;
function scroll_finish() {
    clearTimeout(scroll_timer);
    scroll_timer = setTimeout(floating_recipient_bar.update, 100);
}

$(function () {
    $.fn.safeOuterHeight = function (...args) {
        return this.outerHeight(...args) || 0;
    };
    $.fn.safeOuterWidth = function (...args) {
        return this.outerWidth(...args) || 0;
    };
    $('.app').scroll(_.throttle(function () {
        scroll_finish();
    }, 50));
    exports.initialize();
});
