# Security Policy

## ⚠️ NEVER commit secrets

This repository uses environment variables for sensitive data:

- LLM API keys (e.g. `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) — set in `architect-agent/.env`
- Any future production credentials

The `.gitignore` excludes `.env` files, but **always double-check** before pushing:

```bash
git status
# Look for .env, *.key, *.pem, secrets.* — none of these should appear
```

## Reporting a vulnerability

If you discover a security issue, please email the maintainers directly rather
than opening a public GitHub issue.

## Verified safe to push

✅ `.env.example` (template only, no real secrets)
✅ `.gitignore` (excludes all sensitive files)
✅ No hardcoded API keys in source code
