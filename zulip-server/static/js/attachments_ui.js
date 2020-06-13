const render_settings_upload_space_stats = require("../templates/settings/upload_space_stats.hbs");
const render_uploaded_files_list = require("../templates/uploaded_files_list.hbs");

let attachments;
let upload_space_used;

exports.bytes_to_size = function (bytes, kb_with_1024_bytes) {
    if (kb_with_1024_bytes === undefined) {
        kb_with_1024_bytes = false;
    }
    const kb_size = kb_with_1024_bytes ? 1024 : 1000;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) {
        return '0 B';
    }
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(kb_size)), 10);
    let size = Math.round(bytes / Math.pow(kb_size, i));
    if (i > 0 && size < 10) {
        size = Math.round(bytes / Math.pow(kb_size, i) * 10) / 10;
    }
    return size + ' ' + sizes[i];
};

exports.percentage_used_space = function (uploads_size) {
    if (page_params.realm_upload_quota === null) {
        return null;
    }
    return (100 * uploads_size / page_params.realm_upload_quota).toFixed(1);
};

function set_upload_space_stats() {
    if (page_params.realm_upload_quota === null) {
        return;
    }
    const args = {
        show_upgrade_message: page_params.realm_plan_type === 2,
        percent_used: exports.percentage_used_space(upload_space_used),
        upload_quota: exports.bytes_to_size(page_params.realm_upload_quota, true),
    };
    const rendered_upload_stats_html = render_settings_upload_space_stats(args);
    $("#attachment-stats-holder").html(rendered_upload_stats_html);
}

function delete_attachments(attachment) {
    const status = $('#delete-upload-status');
    channel.del({
        url: '/json/attachments/' + attachment,
        idempotent: true,
        error: function (xhr) {
            ui_report.error(i18n.t("Failed"), xhr, status);
        },
        success: function () {
            ui_report.success(i18n.t("Attachment deleted"), status);
        },
    });
}

function sort_mentioned_in(a, b) {
    const a_m = a.messages[0];
    const b_m = b.messages[0];

    if (!a_m) { return 1; }
    if (!b_m) { return -1; }

    if (a_m.id > b_m.id) {
        return 1;
    } else if (a_m.id === b_m.id) {
        return 0;
    }

    return -1;
}

function render_attachments_ui() {
    set_upload_space_stats();

    const uploaded_files_table = $("#uploaded_files_table").expectOne();
    const $search_input = $("#upload_file_search");

    list_render.create(uploaded_files_table, attachments, {
        name: "uploaded-files-list",
        modifier: function (attachment) {
            return render_uploaded_files_list({ attachment: attachment });
        },
        filter: {
            element: $search_input,
            predicate: function (item, value) {
                return item.name.toLocaleLowerCase().includes(value);
            },
            onupdate: function () {
                ui.reset_scrollbar(uploaded_files_table.closest(".progressive-table-wrapper"));
            },
        },
        parent_container: $('#attachments-settings').expectOne(),
        init_sort: ['numeric', 'create_time'],
        sort_fields: {
            mentioned_in: sort_mentioned_in,
        },
    });

    ui.reset_scrollbar(uploaded_files_table.closest(".progressive-table-wrapper"));
}

function format_attachment_data(new_attachments) {
    for (const attachment of new_attachments) {
        const time = new XDate(attachment.create_time);
        attachment.create_time_str = timerender.render_now(time).time_str;
        attachment.size_str = exports.bytes_to_size(attachment.size);
    }
}

exports.update_attachments = function (event) {
    if (attachments === undefined) {
        // If we haven't fetched attachment data yet, there's nothing to do.
        return;
    }
    if (event.op === 'remove' || event.op === 'update') {
        attachments = attachments.filter(function (a) {
            return a.id !== event.attachment.id;
        });
    }
    if (event.op === 'add' || event.op === 'update') {
        format_attachment_data([event.attachment]);
        attachments.push(event.attachment);
    }
    upload_space_used = event.upload_space_used;
    // TODO: This is inefficient and we should be able to do some sort
    // of incremental list_render update instead.
    render_attachments_ui();
};

exports.set_up_attachments = function () {
    // The settings page must be rendered before this function gets called.

    const status = $('#delete-upload-status');
    loading.make_indicator($('#attachments_loading_indicator'), {text: 'Loading...'});

    $('#uploaded_files_table').on('click', '.remove-attachment', function (e) {
        delete_attachments($(e.target).closest(".uploaded_file_row").attr('data-attachment-id'));
    });

    channel.get({
        url: "/json/attachments",
        idempotent: true,
        success: function (data) {
            loading.destroy_indicator($('#attachments_loading_indicator'));
            format_attachment_data(data.attachments);
            attachments = data.attachments;
            upload_space_used = data.upload_space_used;
            render_attachments_ui();
        },
        error: function (xhr) {
            loading.destroy_indicator($('#attachments_loading_indicator'));
            ui_report.error(i18n.t("Failed"), xhr, status);
        },
    });
};

window.attachments_ui = exports;
