exports.build_realm_logo_widget = function (upload_function, is_night) {
    let logo_section_id = '#day-logo-section';
    let logo_source = page_params.realm_logo_source;

    if (is_night) {
        logo_section_id = '#night-logo-section';
        logo_source = page_params.realm_night_logo_source;
    }

    const delete_button_elem = $(logo_section_id + " .realm-logo-delete-button");
    const file_input_elem = $(logo_section_id + " .realm-logo-file-input");
    const file_input_error_elem = $(logo_section_id + " .realm-logo-file-input-error");
    const upload_button_elem = $(logo_section_id + " .realm-logo-upload-button");

    const get_file_input = function () {
        return file_input_elem.expectOne();
    };

    if (!page_params.is_admin) {
        return;
    }

    if (logo_source === 'D') {
        delete_button_elem.hide();
    } else {
        delete_button_elem.show();
    }

    const data = {night: JSON.stringify(is_night)};
    delete_button_elem.on('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        channel.del({
            url: '/json/realm/logo',
            data: data,
        });
    });

    return upload_widget.build_direct_upload_widget(
        get_file_input,
        file_input_error_elem.expectOne(),
        upload_button_elem.expectOne(),
        upload_function,
        page_params.max_logo_file_size
    );
};

function change_logo_delete_button(logo_source, logo_delete_button, file_input) {
    if (logo_source === 'U') {
        logo_delete_button.show();
    } else {
        logo_delete_button.hide();
        // Need to clear input because of a small edge case
        // where you try to upload the same image you just deleted.
        file_input.val('');
    }
}

exports.rerender = function () {
    const file_input = $("#day-logo-section .realm-logo-file-input");
    const night_file_input = $("#night-logo-section .realm-logo-file-input");
    $("#day-logo-section .realm-logo-img").attr("src", page_params.realm_logo_url);

    if (page_params.realm_night_logo_source === 'D' &&
            page_params.realm_logo_source !== 'D') {
        // If no night mode logo is uploaded but a day mode one
        // is, use the day mode one; this handles the common case
        // of transparent background logos that look good on both
        // night and day themes.  See also similar code in admin.js.

        $("#night-logo-section .realm-logo-img").attr("src", page_params.realm_logo_url);
    } else {
        $("#night-logo-section .realm-logo-img").attr("src", page_params.realm_night_logo_url);
    }

    if (page_params.night_mode && page_params.realm_night_logo_source !== 'D') {
        $("#realm-logo").attr("src", page_params.realm_night_logo_url);
    } else {
        $("#realm-logo").attr("src", page_params.realm_logo_url);
    }

    change_logo_delete_button(page_params.realm_logo_source,
                              $("#day-logo-section .realm-logo-delete-button"),
                              file_input);
    change_logo_delete_button(page_params.realm_night_logo_source,
                              $("#night-logo-section .realm-logo-delete-button"),
                              night_file_input);
};

window.realm_logo = exports;
