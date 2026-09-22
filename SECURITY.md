# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x alpha | Best-effort |

## Reporting

Email **will@tygartmedia.com** with subject `PageReady security`. Do not file public issues for secrets or RCE.

## Hosted API (when enabled)

- Scheme allowlist: `http` / `https` only  
- Block link-local / metadata IP ranges (SSRF)  
- Rate limits + concurrency caps on Playwright  
- No full HTML retention by default  

## Secrets

Never commit API keys, WP application passwords, wallet keys, or Stripe secrets to this repository.
