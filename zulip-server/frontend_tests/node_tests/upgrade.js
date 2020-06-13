const noop = () => {};
const { JSDOM } = require("jsdom");
const fs = require("fs");

const template = fs.readFileSync("templates/corporate/upgrade.html", "utf-8");
const dom = new JSDOM(template, { pretendToBeVisual: true });
const document = dom.window.document;
let jquery_init;

global.$ = (f) => {jquery_init = f;};

set_global('helpers', {
    set_tab: noop,
});

set_global('StripeCheckout', {
    configure: noop,
});

set_global('page_params', {
    annual_price: 8000,
    monthly_price: 800,
    seat_count: 8,
    percent_off: 20,
});

zrequire('helpers', "js/billing/helpers");
zrequire('upgrade', "js/billing/upgrade");
set_global('$', global.make_zjquery());

run_test("initialize", () => {
    let token_func;
    helpers.set_tab = (page_name) => {
        assert.equal(page_name, "upgrade");
    };

    helpers.create_ajax_request = (url, form_name, stripe_token) => {
        assert.equal(url, "/json/billing/upgrade");
        if (form_name === "autopay") {
            assert.equal(stripe_token, "stripe_add_card_token");
        } else if (form_name === "invoice") {
            assert.equal(stripe_token, undefined);
        } else {
            throw Error("Unhandled case");
        }
    };

    const open_func = (config_opts) => {
        assert.equal(config_opts.name, "Zulip");
        assert.equal(config_opts.zipCode, true);
        assert.equal(config_opts.billingAddress, true);
        assert.equal(config_opts.panelLabel, "Make payment");
        assert.equal(config_opts.label, "Add card");
        assert.equal(config_opts.allowRememberMe, false);
        assert.equal(config_opts.email, "{{ email }}");
        assert.equal(config_opts.description, "Zulip Cloud Standard");
        token_func("stripe_add_card_token");
    };

    StripeCheckout.configure = (config_opts) => {
        assert.equal(config_opts.image, '/static/images/logo/zulip-icon-128x128.png');
        assert.equal(config_opts.locale, 'auto');
        assert.equal(config_opts.key, '{{ publishable_key }}');
        token_func = config_opts.token;

        return {
            open: open_func,
        };
    };

    helpers.show_license_section = (section) => {
        assert.equal(section, "automatic");
    };

    helpers.update_charged_amount = (prices, schedule) => {
        assert.equal(prices.annual, 6400);
        assert.equal(prices.monthly, 640);
        assert.equal(schedule, "monthly");
    };

    $('input[type=radio][name=license_management]:checked').val = () => {
        return document.querySelector("input[type=radio][name=license_management]:checked").value;
    };

    $('input[type=radio][name=schedule]:checked').val = () => {
        return document.querySelector("input[type=radio][name=schedule]:checked").value;
    };

    $("#autopay-form").data = (key) => {
        return document.querySelector("#autopay-form").getAttribute("data-" + key);
    };

    jquery_init();

    const e = {
        preventDefault: noop,
    };

    const add_card_click_handler = $('#add-card-button').get_on_handler('click');
    const invoice_click_handler = $('#invoice-button').get_on_handler('click');

    helpers.is_valid_input = () => {
        return true;
    };

    add_card_click_handler(e);
    invoice_click_handler(e);

    helpers.is_valid_input = () => {
        return false;
    };
    add_card_click_handler(e);
    invoice_click_handler(e);

    helpers.show_license_section = (section) => {
        assert.equal(section, "manual");
    };
    const license_change_handler = $('input[type=radio][name=license_management]').get_on_handler('change');
    license_change_handler.call({value: "manual"});

    helpers.update_charged_amount = (prices, schedule) => {
        assert.equal(prices.annual, 6400);
        assert.equal(prices.monthly, 640);
        assert.equal(schedule, "monthly");
    };
    const schedule_change_handler = $('input[type=radio][name=schedule]').get_on_handler('change');
    schedule_change_handler.call({value: "monthly"});

    assert.equal($("#autopay_annual_price").text(), "64");
    assert.equal($("#autopay_annual_price_per_month").text(), "5.34");
    assert.equal($("#autopay_monthly_price").text(), "6.40");
    assert.equal($("#invoice_annual_price").text(), "64");
    assert.equal($("#invoice_annual_price_per_month").text(), "5.34");
});

run_test("autopay_form_fields", () => {
    assert.equal(document.querySelector("#autopay-form").dataset.key, "{{ publishable_key }}");
    assert.equal(document.querySelector("#autopay-form").dataset.email, "{{ email }}");
    assert.equal(document.querySelector("#autopay-form [name=seat_count]").value, "{{ seat_count }}");
    assert.equal(document.querySelector("#autopay-form [name=signed_seat_count]").value, "{{ signed_seat_count }}");
    assert.equal(document.querySelector("#autopay-form [name=salt]").value, "{{ salt }}");
    assert.equal(document.querySelector("#autopay-form [name=billing_modality]").value, "charge_automatically");
    assert.equal(document.querySelector("#autopay-form #automatic_license_count").value, "{{ seat_count }}");
    assert.equal(document.querySelector("#autopay-form #manual_license_count").min, "{{ seat_count }}");

    const license_options = document.querySelectorAll("#autopay-form input[type=radio][name=license_management]");
    assert.equal(license_options.length, 2);
    assert.equal(license_options[0].value, "automatic");
    assert.equal(license_options[1].value, "manual");

    const schedule_options = document.querySelectorAll("#autopay-form input[type=radio][name=schedule]");
    assert.equal(schedule_options.length, 2);
    assert.equal(schedule_options[0].value, "monthly");
    assert.equal(schedule_options[1].value, "annual");

    assert(document.querySelector("#autopay-error"));
    assert(document.querySelector("#autopay-loading"));
    assert(document.querySelector("#autopay"));
    assert(document.querySelector("#autopay-success"));
    assert(document.querySelector("#autopay_loading_indicator"));

    assert(document.querySelector("input[name=csrfmiddlewaretoken]"));

    assert(document.querySelector("#free-trial-alert-message"));
});

run_test("invoice_form_fields", () => {
    assert.equal(document.querySelector("#invoice-form [name=signed_seat_count]").value, "{{ signed_seat_count }}");
    assert.equal(document.querySelector("#invoice-form [name=salt]").value, "{{ salt }}");
    assert.equal(document.querySelector("#invoice-form [name=billing_modality]").value, "send_invoice");
    assert.equal(document.querySelector("#invoice-form [name=licenses]").min, "{{ min_invoiced_licenses }}");

    const schedule_options = document.querySelectorAll("#invoice-form input[type=radio][name=schedule]");
    assert.equal(schedule_options.length, 1);
    assert.equal(schedule_options[0].value, "annual");

    assert(document.querySelector("#invoice-error"));
    assert(document.querySelector("#invoice-loading"));
    assert(document.querySelector("#invoice"));
    assert(document.querySelector("#invoice-success"));
    assert(document.querySelector("#invoice_loading_indicator"));

    assert(document.querySelector("input[name=csrfmiddlewaretoken]"));

    assert(document.querySelector("#free-trial-alert-message"));
});
