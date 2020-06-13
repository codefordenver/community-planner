# Update User Group

{generate_api_description(/user_groups/{group_id}:patch)}

## Usage examples

{start_tabs}
{tab|python}

{generate_code_example(python)|/user_groups/{group_id}:patch|example}

{tab|curl}

{generate_code_example(curl)|/user_groups/{group_id}:patch|example}

{end_tabs}

## Arguments

{generate_api_arguments_table|zulip.yaml|/user_groups/{group_id}:patch}

## Response

#### Example response

A typical successful JSON response may look like:

{generate_code_example|/user_groups/{group_id}:patch|fixture(200)}

An example JSON response when the user group ID is invalid:

{generate_code_example|/user_groups/{group_id}:patch|fixture(400)}
