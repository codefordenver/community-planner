import * as google_analytics from './google-analytics.js';
import blueslip from './../blueslip';

import { path_parts } from './landing-page';


// these constants are populated immediately with data from the DOM on page load
// name -> display name
const INTEGRATIONS = new Map();
const CATEGORIES = new Map();

function load_data() {
    $('.integration-lozenge').toArray().forEach(function (integration) {
        const name = $(integration).data('name');
        const display_name = $(integration).find('.integration-name').text().trim();

        if (display_name && name) {
            INTEGRATIONS.set(name, display_name);
        }
    });

    $('.integration-category').toArray().forEach(function (category) {
        const name = $(category).data('category');
        const display_name = $(category).text().trim();

        if (display_name && name) {
            CATEGORIES.set(name, display_name);
        }
    });
}

const INITIAL_STATE = {
    category: 'all',
    integration: null,
    query: '',
};

let state = Object.assign({}, INITIAL_STATE);


function adjust_font_sizing() {
    $('.integration-lozenge').toArray().forEach(function (integration) {
        const $integration_name = $(integration).find('.integration-name');
        const $integration_category = $(integration).find('.integration-category');

        // if the text has wrapped to two lines, decrease font-size
        if ($integration_name.height() > 30) {
            $integration_name.css('font-size', '1em');
            if ($integration_name.height() > 30) {
                $integration_name.css('font-size', '.95em');
            }
        }

        if ($integration_category.height() > 30) {
            $integration_category.css('font-size', '.8em');
            if ($integration_category.height() > 30) {
                $integration_category.css('font-size', '.75em');
            }
        }
    });
}

function update_path() {
    let next_path;
    if (state.integration) {
        next_path = $('.integration-lozenge[data-name="' + state.integration + '"]')
            .closest('a').attr('href');
    } else if (state.category) {
        next_path = $('.integration-category[data-category="' + state.category + '"]')
            .closest('a').attr('href');
    } else {
        next_path = '/';
    }

    window.history.pushState(state, '', next_path);
    google_analytics.config({page_path: next_path});
}

function update_categories() {
    $('.integration-lozenges').css('opacity', 0);

    $('.integration-category').removeClass('selected');
    $('[data-category="' + state.category + '"]').addClass('selected');

    const $dropdown_label = $('.integration-categories-dropdown .dropdown-category-label');
    if (state.category === INITIAL_STATE.category) {
        $dropdown_label.text(i18n.t('Filter by category'));
    } else {
        $dropdown_label.text(CATEGORIES.get(state.category));
    }

    $('.integration-lozenges').animate(
        { opacity: 1 },
        { duration: 400 }
    );

    adjust_font_sizing();
}

const update_integrations = _.debounce(function () {
    const max_scrollY = window.scrollY;

    const integrations = $('.integration-lozenges').children().toArray();
    integrations.forEach(function (integration) {
        const $integration = $(integration).find('.integration-lozenge');
        const $integration_category = $integration.find('.integration-category');

        if (state.category !== 'all') {
            $integration_category.css('display', 'none');
            $integration.addClass('without-category');
        } else {
            $integration_category.css('display', '');
            $integration.removeClass('without-category');
        }

        if (!$integration.hasClass('integration-create-your-own')) {
            const display_name = INTEGRATIONS.get($integration.data('name'));
            const display =
                common.phrase_match(state.query, display_name) &&
                ($integration.data('categories').includes(CATEGORIES.get(state.category)) ||
                 state.category === 'all');

            if (display) {
                $integration.css('display', 'inline-block');
            } else {
                $integration.css('display', 'none');
            }
        }

        document.body.scrollTop = Math.min(window.scrollY, max_scrollY);
    });

    adjust_font_sizing();
}, 50);

function hide_catalog_show_integration() {
    const $lozenge_icon = $(".integration-lozenge.integration-" + state.integration).clone(false);
    $lozenge_icon.removeClass('legacy');

    const categories = $('.integration-' + state.integration).data('categories')
        .slice(1, -1)
        .split(',')
        .map(function (category) {
            return category.trim().slice(1, -1);
        });

    function show_integration(doc) {
        $('#integration-instructions-group .name').text(INTEGRATIONS.get(state.integration));
        $('#integration-instructions-group .categories .integration-category').remove();
        categories.forEach(function (category) {
            let link;
            for (const [name, display_name] of CATEGORIES) {
                if (display_name === category) {
                    link = name;
                }
            }
            const category_el = $('<a></a>')
                .attr('href', '/integrations/' + link)
                .append('<h3 class="integration-category"></h3>');
            category_el.find('.integration-category')
                .attr('data-category', link)
                .text(category);
            $('#integration-instructions-group .categories').append(category_el);
        });
        $('#integration-instructions-group').css({
            opacity: 0,
            display: 'flex',
        });
        $('.integration-instructions').css('display', 'none');
        $('#' + state.integration + '.integration-instructions .help-content').html(doc);
        $('#integration-instruction-block .integration-lozenge').remove();
        $("#integration-instruction-block")
            .append($lozenge_icon)
            .css('display', 'flex');
        $('.integration-instructions#' + state.integration).css('display', 'block');

        $("html, body").animate(
            { scrollTop: 0 },
            { duration: 200 }
        );
        $('#integration-instructions-group').animate(
            { opacity: 1 },
            { duration: 300 }
        );

        adjust_font_sizing();
    }

    function hide_catalog(doc) {
        $(".integration-categories-dropdown").css('display', 'none');
        $(".integrations .catalog").addClass('hide');
        $(".extra, #integration-main-text, #integration-search").css("display", "none");

        show_integration(doc);
        $(".main").css("visibility", "visible");
    }

    $.get({
        url: '/integrations/doc-html/' + state.integration,
        dataType: 'html',
        success: hide_catalog,
        error: function (err) {
            blueslip.error("Integration documentation for '" + state.integration + "' not found.", err);
        },
    });
}

function hide_integration_show_catalog() {
    function show_catalog() {
        $("html, body").animate(
            { scrollTop: 0 },
            { duration: 200 }
        );

        $(".integration-categories-dropdown").css('display', '');
        $(".integrations .catalog").removeClass('hide');
        $(".extra, #integration-main-text, #integration-search").css("display", "block");
        adjust_font_sizing();
    }

    function hide_integration() {
        $('#integration-instruction-block').css('display', 'none');
        $('#integration-instructions-group').css('display', 'none');
        $('.inner-content').css({ padding: '' });
        $("#integration-instruction-block .integration-lozenge").remove();
        show_catalog();
    }

    hide_integration();
}

function get_state_from_path() {
    const result = Object.assign({}, INITIAL_STATE);
    result.query = state.query;

    const parts = path_parts();
    if (parts[1] === 'doc' && INTEGRATIONS.get(parts[2])) {
        result.integration = parts[2];
    } else if (CATEGORIES.has(parts[1])) {
        result.category = parts[1];
    }

    return result;
}

function render(next_state) {
    const previous_state = Object.assign({}, state);
    state = next_state;

    if (previous_state.integration !== next_state.integration &&
        next_state.integration !== null) {
        hide_catalog_show_integration();
    } else {
        if (previous_state.integration !== next_state.integration) {
            hide_integration_show_catalog();
        }

        if (previous_state.category !== next_state.category) {
            update_categories();
            update_integrations();
        }

        if (previous_state.query !== next_state.query) {
            update_integrations();
        }

        $(".main").css("visibility", "visible");
    }

}

function dispatch(action, payload) {
    switch (action) {
    case 'CHANGE_CATEGORY':
        render(Object.assign({}, state, {
            category: payload.category,
        }));
        update_path();
        break;

    case 'SHOW_INTEGRATION':
        render(Object.assign({}, state, {
            integration: payload.integration,
        }));
        update_path();
        break;

    case 'HIDE_INTEGRATION':
        render(Object.assign({}, state, {
            integration: null,
        }));
        update_path();
        break;

    case 'SHOW_CATEGORY':
        render(Object.assign({}, state, {
            integration: null,
            category: payload.category,
        }));
        update_path();
        break;

    case 'UPDATE_QUERY':
        render(Object.assign({}, state, {
            query: payload.query,
        }));
        break;

    case 'LOAD_PATH':
        render(get_state_from_path());
        google_analytics.config({page_path: window.location.pathname});
        break;

    default:
        blueslip.error('Invalid action dispatched on /integrations.');
        break;
    }
}

function toggle_categories_dropdown() {
    const $dropdown_list = $('.integration-categories-dropdown .dropdown-list');
    $dropdown_list.slideToggle(250);
}

function integration_events() {
    $('#integration-search input[type="text"]').keypress(function (e) {
        const integrations = $('.integration-lozenges').children().toArray();
        if (e.which === 13 && e.target.value !== '') {
            for (let i = 0; i < integrations.length; i += 1) {
                const integration = $(integrations[i]).find('.integration-lozenge');

                if ($(integration).css('display') !== 'none') {
                    $(integration).closest('a')[0].click();
                    break;
                }
            }
        }
    });

    $('.integration-categories-dropdown .dropdown-toggle').click(function () {
        toggle_categories_dropdown();
    });

    $('.integration-instruction-block').on('click', 'a .integration-category', function (e) {
        const category = $(e.target).data('category');
        dispatch('SHOW_CATEGORY', { category: category });
        return false;
    });

    $('.integrations a .integration-category').on('click', function (e) {
        const category = $(e.target).data('category');
        dispatch('CHANGE_CATEGORY', { category: category });
        toggle_categories_dropdown();
        return false;
    });

    $('.integrations a .integration-lozenge').on('click', function (e) {
        if (!$(e.target).closest('.integration-lozenge').hasClass('integration-create-your-own')) {
            const integration = $(e.target).closest('.integration-lozenge').data('name');
            dispatch('SHOW_INTEGRATION', { integration: integration });
            return false;
        }
    });

    $('a#integration-list-link span, a#integration-list-link i').on('click', function () {
        dispatch('HIDE_INTEGRATION');
        return false;
    });

    // combine selector use for both focusing the integrations searchbar and adding
    // the input event.
    $(".integrations .searchbar input[type='text']")
        .focus()
        .on('input', function (e) {
            dispatch('UPDATE_QUERY', { query: e.target.value.toLowerCase() });
        });

    $(window).scroll(function () {
        if (document.body.scrollTop > 330) {
            $('.integration-categories-sidebar').addClass('sticky');
        } else {
            $('.integration-categories-sidebar').removeClass('sticky');
        }
    });

    $(window).on('resize', function () {
        adjust_font_sizing();
    });

    $(window).on('popstate', function () {
        if (window.location.pathname.startsWith('/integrations')) {
            dispatch('LOAD_PATH');
        } else {
            window.location = window.location.href;
        }
    });
}

// init
$(function () {
    integration_events();
    load_data();
    dispatch('LOAD_PATH');
});
