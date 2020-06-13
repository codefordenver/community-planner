# Add subscriptions

{generate_api_description(/users/me/subscriptions:post)}

## Usage examples

{start_tabs}
{tab|python}

{generate_code_example(python)|/users/me/subscriptions:post|example}

{tab|js}

More examples and documentation can be found [here](https://github.com/zulip/zulip-js).

```js
const zulip = require('zulip-js');

// Pass the path to your zuliprc file here.
const config = {
    zuliprc: 'zuliprc',
};

zulip(config).then((client) => {
    // Subscribe to the streams "Verona" and "Denmark"
    const meParams = {
        subscriptions: JSON.stringify([
            {'name': 'Verona'},
            {'name': 'Denmark'}
        ]),
    };
    client.users.me.subscriptions.add(meParams).then(console.log);

    // To subscribe another user to a stream, you may pass in
    // the `principals` argument, like so:
    const anotherUserParams = {
        subscriptions: JSON.stringify([
            {'name': 'Verona'},
            {'name': 'Denmark'}
        ]),
        principals: JSON.stringify(['ZOE@zulip.org']),
    };
    client.users.me.subscriptions.add(anotherUserParams).then(console.log);
});
```

{tab|curl}

{generate_code_example(curl, include=["subscriptions"])|/users/me/subscriptions:post|example}

To subscribe another user to a stream, you may pass in
the `principals` argument, like so:

{generate_code_example(curl, include=["subscriptions", "principals"])|/users/me/subscriptions:post|example}

{end_tabs}

## Arguments

{generate_api_arguments_table|zulip.yaml|/users/me/subscriptions:post}

## Response

#### Return values

{generate_return_values_table|zulip.yaml|/users/me/subscriptions:post}

#### Example response

A typical successful JSON response may look like:

{generate_code_example|/users/me/subscriptions:post|fixture(200_0)}

A typical successful JSON response when the user is already subscribed to
the streams specified:

{generate_code_example|/users/me/subscriptions:post|fixture(200_1)}

A typical response for when the requesting user does not have access to
a private stream and `authorization_errors_fatal` is `True`:

{generate_code_example|/users/me/subscriptions:post|fixture(400_0)}


A typical response for when the requesting user does not have access to
a private stream and `authorization_errors_fatal` is `False`:

{generate_code_example|/users/me/subscriptions:post|fixture(400_1)}
