# Instruction Templating specifics, this part is separated
INSTRUCTION_TEMPLATING_GUIDELINES = """
- For short fields (ex: user name, user email, etc.) you can 'inline' the variable directly in the instructions sentences:
{% raw %}
- The user name is {{ user.name }}
{% endraw %}

- For longer fields (ex: email content), you can use the following syntax (preferably at the end of the instructions):
{% raw %}
- The email content to process is:
{{ user.email_content }}
{% endraw %}

- For deeply nested fields, you do not need to specify the path to every single field, you can just inject the parent object where it makes sense:
{% raw %}
The issues to generate the release note from are:
{{ issues }}
{% endraw %}

In this case, the 'issues' object is an array of objects, each with the following keys: name, description, priority, type, status, sub_issues, etc.
"""
