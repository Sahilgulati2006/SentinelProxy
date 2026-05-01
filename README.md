# SentinelProxy

SentinelProxy is a local-first LLM security proxy that protects sensitive prompts before they reach a model provider.

It provides an OpenAI-compatible chat endpoint with local PII redaction, Redis-backed placeholder mapping, response re-identification, API key authentication, user budgets, rate limits, PII-safe audit logs, an admin dashboard, and a protected chat web UI.

---

## Why SentinelProxy Exists

Modern AI apps often send raw user prompts directly to external or local model providers. Those prompts may contain sensitive data such as:

- Emails
- Phone numbers
- SSNs
- Credit cards
- IP addresses
- API keys or secrets

SentinelProxy sits between the client and the model provider.

Instead of sending raw sensitive values to the model, it replaces them with protected placeholders like:

```text
<<SP_EMAIL_1>>
<<SP_PHONE_1>>
<<SP_SSN_1>>
<<SP_CREDIT_CARD_1>>