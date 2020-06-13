export function detect_user_os() {
    if (/Android/i.test(navigator.userAgent)) {
        return "android";
    }
    if (/iPhone|iPad|iPod/i.test(navigator.userAgent)) {
        return "ios";
    }
    if (common.has_mac_keyboard()) {
        return "mac";
    }
    if (/Win/i.test(navigator.userAgent)) {
        return "windows";
    }
    if (/Linux/i.test(navigator.userAgent)) {
        return "linux";
    }
    return "mac"; // if unable to determine OS return Mac by default
}

export function activate_correct_tab($codeSection) {
    const user_os = detect_user_os();
    const desktop_os = ["mac", "linux", "windows"];
    const $li = $codeSection.find("ul.nav li");
    const $blocks = $codeSection.find(".blocks div");

    $li.each(function () {
        const language = this.dataset.language;
        $(this).removeClass("active");
        if (language === user_os) {
            $(this).addClass("active");
        }

        if (desktop_os.includes(user_os) && language === "desktop-web") {
            $(this).addClass("active");
        }
    });

    $blocks.each(function () {
        const language = this.dataset.language;
        $(this).removeClass("active");
        if (language === user_os) {
            $(this).addClass("active");
        }

        if (desktop_os.includes(user_os) && language === "desktop-web") {
            $(this).addClass("active");
        }
    });

    // if no tab was activated, just activate the first one
    const active_list_items = $li.filter(".active");
    if (!active_list_items.length) {
        $li.first().addClass("active");
        const language = $li.first()[0].dataset.language;
        $blocks.filter("[data-language=" + language + "]").addClass("active");
    }
}

$(".code-section").each(function () {
    activate_correct_tab($(this));
});
