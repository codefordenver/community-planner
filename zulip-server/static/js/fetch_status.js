const FetchStatus = function () {

    const self = {};

    let loading_older = false;
    let loading_newer = false;
    let found_oldest = false;
    let found_newest = false;
    let history_limited = false;

    self.start_older_batch = function () {
        loading_older = true;
    };

    self.finish_older_batch = function (opts) {
        loading_older = false;
        found_oldest = opts.found_oldest;
        history_limited = opts.history_limited;
    };

    self.can_load_older_messages = function () {
        return !loading_older && !found_oldest;
    };

    self.history_limited = function () {
        return history_limited;
    };

    self.start_newer_batch = function () {
        loading_newer = true;
    };

    self.finish_newer_batch = function (opts) {
        loading_newer = false;
        found_newest = opts.found_newest;
    };

    self.can_load_newer_messages = function () {
        return !loading_newer && !found_newest;
    };

    self.has_found_newest = function () {
        return found_newest;
    };

    return self;

};
module.exports = FetchStatus;
window.FetchStatus = FetchStatus;
