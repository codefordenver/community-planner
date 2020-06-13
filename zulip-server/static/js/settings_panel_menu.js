exports.make_menu = function (opts) {
    const main_elem = opts.main_elem;
    const hash_prefix = opts.hash_prefix;
    let curr_li = main_elem.children('li').eq(0);

    const self = {};

    self.show = function () {
        main_elem.show();
        const section = self.current_tab();
        self.activate_section(section);
        curr_li.focus();
    };

    self.hide = function () {
        main_elem.hide();
    };

    self.current_tab = function () {
        return curr_li.data('section');
    };

    self.li_for_section = function (section) {
        const li = $("#settings_overlay_container li[data-section='" + section + "']");
        return li;
    };

    self.set_key_handlers = function (toggler) {
        keydown_util.handle({
            elem: main_elem,
            handlers: {
                left_arrow: toggler.maybe_go_left,
                right_arrow: toggler.maybe_go_right,
                enter_key: self.enter_panel,
                up_arrow: self.prev,
                down_arrow: self.next,
            },
        });
    };

    self.prev = function () {
        curr_li.prevAll(":visible:first").focus().click();
        return true;
    };

    self.next = function () {
        curr_li.nextAll(":visible:first").focus().click();
        return true;
    };

    self.enter_panel = function () {
        const panel = self.get_panel();
        const sel = 'input:visible,button:visible,select:visible';
        const panel_elem = panel.find(sel).first();

        panel_elem.focus();
        return true;
    };

    self.activate_section = function (section) {
        curr_li = self.li_for_section(section);

        main_elem.children("li").removeClass("active no-border");
        curr_li.addClass("active");
        curr_li.prev().addClass("no-border");

        const settings_section_hash = '#' + hash_prefix + section;
        hashchange.update_browser_history(settings_section_hash);

        $(".settings-section, .settings-wrapper").removeClass("show");

        settings_sections.load_settings_section(section);

        self.get_panel().addClass('show');

        ui.reset_scrollbar($("#settings_content"));

        const $settings_overlay_container = $("#settings_overlay_container");
        $settings_overlay_container.find(".right").addClass("show");
        $settings_overlay_container.find(".settings-header.mobile").addClass("slide-left");

        settings.set_settings_header(section);
    };

    self.get_panel = function () {
        const section = curr_li.data('section');
        const sel = "[data-name='" + section + "']";
        const panel = $(".settings-section" + sel + ", .settings-wrapper" + sel);
        return panel;
    };

    main_elem.on("click", "li[data-section]", function (e) {
        const section = $(this).attr('data-section');

        self.activate_section(section);

        // You generally want to add logic to activate_section,
        // not to this click handler.

        e.stopPropagation();
    });

    return self;
};

exports.initialize = function () {
    exports.normal_settings = exports.make_menu({
        main_elem: $('.normal-settings-list'),
        hash_prefix: "settings/",
    });
    exports.org_settings = exports.make_menu({
        main_elem: $('.org-settings-list'),
        hash_prefix: "organization/",
    });
};

exports.show_normal_settings = function () {
    exports.org_settings.hide();
    exports.normal_settings.show();
};

exports.show_org_settings = function () {
    exports.normal_settings.hide();
    exports.org_settings.show();
};

exports.set_key_handlers = function (toggler) {
    exports.normal_settings.set_key_handlers(toggler);
    exports.org_settings.set_key_handlers(toggler);
};

window.settings_panel_menu = exports;
