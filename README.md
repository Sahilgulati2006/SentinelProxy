# SentinelProxy

SentinelProxy is a production-style LLM security gateway that protects sensitive user data before it reaches a model provider.

It works as an OpenAI-compatible proxy: users and applications send chat requests to SentinelProxy, SentinelProxy redacts sensitive information locally, forwards only protected placeholders to the model, then safely restores the final response.

**Live Demo**

- Frontend: https://sentinel-proxy-phi.vercel.app
- Backend: https://sentinelproxy-api.onrender.com

---

## Why I Built This

LLM apps often send raw user prompts directly to model providers. Those prompts can contain sensitive information such as emails, phone numbers, SSNs, credit card numbers, API keys, or customer records.

SentinelProxy reduces this risk by sitting between the client and the model provider.

```text
Raw prompt:
My email is sahil@example.com and my phone is 413-555-0199.

Provider receives:
My email is <<SP_EMAIL_1>> and my phone is <<SP_PHONE_1>>.
