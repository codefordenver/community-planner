# Set "typing" status

{generate_api_description(/typing:post)}

## Usage examples

{start_tabs}
{tab|python}

{generate_code_example(python)|/typing:post|example}

{tab|js}

More examples and documentation can be found [here](https://github.com/zulip/zulip-js).
```js
const zulip = require('zulip-js');

// Pass the path to your zuliprc file here.
const config = {
    zuliprc: 'zuliprc',
};

const user_id1 = 9;
const user_id2 = 10;

const typingParams = {
    op: 'start',
    to: [user_id1, user_id2],
};

zulip(config).then((client) => {
    // The user has started to type in the group PM with Iago and Polonius
    return client.typing.send(typingParams);
}).then(console.log);
```

{tab|curl}

{generate_code_example(curl)|/typing:post|example}

{end_tabs}

## Arguments

{generate_api_arguments_table|zulip.yaml|/typing:post}

## Response

#### Example response

A typical successful JSON response may look like:

{generate_code_example|/typing:post|fixture(200)}
