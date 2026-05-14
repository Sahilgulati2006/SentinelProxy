# SentinelProxy Deployment Guide

This guide explains how to deploy SentinelProxy with:

- Frontend on Vercel
- Backend on Render
- Postgres as the production database
- Redis as the production cache/mapping/rate-limit store
- OpenAI-compatible provider for deployed inference

Local development can still use Ollama.

---

## Production Architecture

```text
Browser
  ↓
Vercel Frontend
  ↓
Render FastAPI Backend
  ↓
Postgres Database
  ↓
Redis
  ↓
OpenAI-compatible Model Provider

alembic upgrade head