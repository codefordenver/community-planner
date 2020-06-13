import * as google_analytics from './google-analytics.js';
import SimpleBar from 'simplebar';
import {activate_correct_tab} from './tabbed-instructions.js';

function registerCodeSection($codeSection) {
    const $li = $codeSection.find("ul.nav li");
    const $blocks = $codeSection.find(".blocks div");

    $li.click(function () {
        const language = this.dataset.language;

        $li.removeClass("active");
        $li.filter("[data-language=" + language + "]").addClass("active");

        $blocks.removeClass("active");
        $blocks.filter("[data-language=" + language + "]").addClass("active");
    });
}

function highlight_current_article() {
    $('.help .sidebar a').removeClass('highlighted');
    const path = window.location.pathname;

    if (!path) {
        return;
    }

    const hash = window.location.hash;
    let article = $('.help .sidebar a[href="' + path + hash + '"]');
    if (!article.length) {
        // If there isn't an entry in the left sidebar that matches
        // the full url+hash pair, instead highlight an entry in the
        // left sidebar that just matches the url part.
        article = $('.help .sidebar a[href="' + path + '"]');
    }
    // Highlight current article link and the heading of the same
    article.closest('ul').css('display', 'block');
    article.addClass('highlighted');
}

function render_code_sections() {
    $(".code-section").each(function () {
        activate_correct_tab($(this));
        registerCodeSection($(this));
    });

    highlight_current_article();

    common.adjust_mac_shortcuts(".markdown .content code", true);

    $("table").each(function () {
        $(this).addClass("table table-striped");
    });
}

function scrollToHash(simplebar) {
    const hash = window.location.hash;
    const scrollbar = simplebar.getScrollElement();
    if (hash !== '') {
        const position = $(hash).position().top - $(scrollbar.firstChild).position().top;
        scrollbar.scrollTop = position;
    } else {
        scrollbar.scrollTop = 0;
    }
}

const html_map = new Map();
const loading = {
    name: null,
};

const markdownSB = new SimpleBar($(".markdown")[0]);

const fetch_page = function (path, callback) {
    $.get(path, function (res) {
        const $html = $(res).find(".markdown .content");

        callback($html.html().trim());
        render_code_sections();
    });
};

const update_page = function (html_map, path) {
    if (html_map.has(path)) {
        $(".markdown .content").html(html_map.get(path));
        render_code_sections();
        scrollToHash(markdownSB);
    } else {
        loading.name = path;
        fetch_page(path, function (res) {
            html_map.set(path, res);
            $(".markdown .content").html(res);
            loading.name = null;
            scrollToHash(markdownSB);
        });
    }
    google_analytics.config({page_path: path});
};

new SimpleBar($(".sidebar")[0]);

$(".sidebar.slide h2").click(function (e) {
    const $next = $(e.target).next();

    if ($next.is("ul")) {
        // Close other article's headings first
        $('.sidebar ul').not($next).hide();
        // Toggle the heading
        $next.slideToggle("fast", "swing");
    }
});

$(".sidebar a").click(function (e) {
    const path = $(this).attr("href");
    const path_dir = path.split('/')[1];
    const current_dir = window.location.pathname.split('/')[1];

    // Do not block redirecting to external URLs
    if (path_dir !== current_dir) {
        return;
    }

    if (loading.name === path) {
        return;
    }

    history.pushState({}, "", path);

    update_page(html_map, path);

    $(".sidebar").removeClass("show");

    e.preventDefault();
});

if (window.location.pathname === '/help/') {
    // Expand the Guides user docs section in sidebar in the /help/ homepage.
    $('.help .sidebar h2#guides + ul').show();
}
// Remove ID attributes from sidebar links so they don't conflict with index page anchor links
$('.help .sidebar h1, .help .sidebar h2, .help .sidebar h3').removeAttr('id');

// Scroll to anchor link when clicked
$(document).on('click', '.markdown .content h1, .markdown .content h2, .markdown .content h3', function () {
    window.location.hash = $(this).attr("id");
    scrollToHash(markdownSB);
});

$(".hamburger").click(function () {
    $(".sidebar").toggleClass("show");
});

$(".markdown").click(function () {
    if ($(".sidebar.show").length) {
        $(".sidebar.show").toggleClass("show");
    }
});

render_code_sections();

// Finally, make sure if we loaded a window with a hash, we scroll
// to the right place.
scrollToHash(markdownSB);

window.addEventListener("popstate", function () {
    const path = window.location.pathname;
    update_page(html_map, path);
});

$('body').addClass('noscroll');
