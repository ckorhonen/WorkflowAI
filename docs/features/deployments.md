## Deployments

Deploy specific versions of an agent with ease, allowing for updates to prompts and models **without any code changes**.

### Why use deployments?

- ✅ update to a new model or prompt without asking your engineering team.
- ✅ save cost by updating to a more recent, cheaper model, without changing your code.
- ✅ improve the quality of your tasks outputs by adjusting the prompt, in real-time, based on users' feedback.
- ✅ use different versions of a task in different environments (development, staging, production).

### How to deploy a version?

1. Go to **Deployments** section from the menu.
2. Pick the environment you want to deploy to, either: production, staging, or development.
3. Tap **Deploy Version**
4. Select the version you want to deploy.
5. Tap **Deploy**

{% embed url="https://customer-turax1sz4f7wbpuv.cloudflarestream.com/58dfabcb7b91f2a57d99602876dc98f1/watch" %}

{% hint style="warning" %}
To avoid any breaking changes: deployments are **schema specific**, not AI feature specific. This means that if you want to deploy a new version of your AI feature that is on a different schema, you will need to update the schema number in your code.

This also means that you can deploy a (development, staging, production) version for each schema of an agent without the version deployed to production being affected.
{% endhint %}

### Using your own AI Provider Keys

Your own API provider keys can be added by going to: [workflowai.com/organization/settings/providers](https://workflowai.com/organization/settings/providers). 

**Important: If you are using WorkflowAI Cloud, credits will still deducted by default. There is a required manual operation on our side to mark the keys as a customer provided key.** If you would like to use your own keys via workflowai.com, please reach out to us via [email](mailto:team@workflowai.support) or on [GitHub](https://github.com/workflowai/workflowai/discussions) so we can help you out.

If you are self-hosting, adding your own API provider keys does not require any additional steps beyond adding them at: [workflowai.com/organization/settings/providers](https://workflowai.com/organization/settings/providers). 
