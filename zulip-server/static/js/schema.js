/*

These runtime schema validators are defensive and
should always succeed, so we don't necessarily want
to translate these.  These are very similar to server
side validators in zerver/lib/validator.py.

*/

exports.check_string = function (var_name, val) {
    if (typeof val !== "string") {
        return var_name + ' is not a string';
    }
};

exports.check_record = function (var_name, val, fields) {
    if (typeof val !== "object") {
        return var_name + ' is not a record';
    }

    const field_results = Object.entries(fields).map(([field_name, f]) => {
        if (val[field_name] === undefined) {
            return field_name + ' is missing';
        }
        return f(field_name, val[field_name]);
    });

    const msg = field_results.filter(Boolean).sort().join(', ');

    if (msg) {
        return 'in ' + var_name + ' ' + msg;
    }
};

exports.check_array = function (var_name, val, checker) {
    if (!Array.isArray(val)) {
        return var_name + ' is not an array';
    }

    for (const item of val) {
        const msg = checker('item', item);

        if (msg) {
            return 'in ' + var_name + ' we found an item where ' + msg;
        }
    }
};

window.schema = exports;
