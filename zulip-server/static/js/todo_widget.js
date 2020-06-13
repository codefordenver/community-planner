const render_widgets_todo_widget = require('../templates/widgets/todo_widget.hbs');
const render_widgets_todo_widget_tasks = require('../templates/widgets/todo_widget_tasks.hbs');

exports.task_data_holder = function () {
    const self = {};

    const task_map = new Map();

    function get_new_index() {
        let idx = 0;

        for (const item of task_map.values()) {
            idx = Math.max(idx, item.idx);
        }

        return idx + 1;
    }

    self.get_widget_data = function () {
        const all_tasks = Array.from(task_map.values());
        all_tasks.sort((a, b) => a.task.localeCompare(b.task));

        const pending_tasks = [];
        const completed_tasks = [];

        for (const item of all_tasks) {
            if (item.completed) {
                completed_tasks.push(item);
            } else {
                pending_tasks.push(item);
            }
        }

        const widget_data = {
            pending_tasks: pending_tasks,
            completed_tasks: completed_tasks,
        };

        return widget_data;
    };

    self.name_in_use = function (name) {
        for (const item of task_map.values()) {
            if (item.task === name) {
                return true;
            }
        }

        return false;
    };

    self.handle = {
        new_task: {
            outbound: function (task, desc) {
                const event = {
                    type: 'new_task',
                    key: get_new_index(),
                    task: task,
                    desc: desc,
                    completed: false,
                };

                if (!self.name_in_use(task)) {
                    return event;
                }
                return;
            },

            inbound: function (sender_id, data) {
                // for legacy reasons, the inbound idx is
                // called key in the event
                const idx = data.key;
                const key = idx + "," + sender_id;
                const task = data.task;
                const desc = data.desc;
                const completed = data.completed;

                const task_data = {
                    task: task,
                    desc: desc,
                    idx: idx,
                    key: key,
                    completed: completed,
                };

                if (!self.name_in_use(task)) {
                    task_map.set(key, task_data);
                }
            },
        },

        strike: {
            outbound: function (key) {
                const event = {
                    type: 'strike',
                    key: key,
                };

                return event;
            },

            inbound: function (sender_id, data) {
                const key = data.key;
                const item = task_map.get(key);

                if (item === undefined) {
                    blueslip.warn('Do we have legacy data? unknown key for tasks: ' + key);
                    return;
                }

                item.completed = !item.completed;
            },
        },
    };

    self.handle_event = function (sender_id, data) {
        const type = data.type;
        if (self.handle[type]) {
            self.handle[type].inbound(sender_id, data);
        }
    };

    return self;
};

exports.activate = function (opts) {
    const elem = opts.elem;
    const callback = opts.callback;

    const task_data = exports.task_data_holder();

    function render() {
        const html = render_widgets_todo_widget();
        elem.html(html);

        elem.find("button.add-task").on('click', function (e) {
            e.stopPropagation();
            elem.find(".widget-error").text('');
            const task = elem.find("input.add-task").val().trim();
            const desc = elem.find("input.add-desc").val().trim();

            if (task === '') {
                return;
            }

            elem.find(".add-task").val('').focus();
            elem.find(".add-desc").val('').focus();

            const task_exists = task_data.name_in_use(task);
            if (task_exists) {
                elem.find(".widget-error").text(i18n.t('Task already exists'));
                return;
            }

            const data = task_data.handle.new_task.outbound(task, desc);
            callback(data);
        });
    }

    function render_results() {
        const widget_data = task_data.get_widget_data();
        const html = render_widgets_todo_widget_tasks(widget_data);
        elem.find('ul.todo-widget').html(html);
        elem.find(".widget-error").text('');

        elem.find("button.task").on('click', function (e) {
            e.stopPropagation();
            const key = $(e.target).attr('data-key');

            const data = task_data.handle.strike.outbound(key);
            callback(data);
        });
    }

    elem.handle_events = function (events) {
        for (const event of events) {
            task_data.handle_event(event.sender_id, event.data);
        }

        render_results();
    };

    render();
    render_results();
};

window.todo_widget = exports;
