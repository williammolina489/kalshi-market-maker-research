# Security and Trading Safety

## Non-negotiable project restrictions

- Real-money trading is prohibited.
- No live orders may be placed.
- No funded execution path may be created.
- No API secrets, private keys, passwords, cookies, or tokens may be committed to Git.
- Future API credentials, if research ever requires authenticated read-only connectivity, must use the least privilege available and must not have withdrawal permissions.
- Trading capability must remain disabled until explicitly approved by a future project decision. Under the current charter, it is not approved.

## Current code boundary

`ReadOnlyKalshiClient` implements `GET` requests only. There is no generic request method exposed to callers, no order endpoint, no cancel endpoint, and no credential loader.

## Secret handling if later needed

- Keep secrets outside the repository and outside logs.
- Use environment injection or an OS/secret-manager facility.
- Never put a private RSA key in `.env`, fixtures, CI variables visible to forks, or issue/PR text.
- Prefer public REST for E001 so no credential is needed.

## Future execution safeguards (design requirements, not implemented)

If a later explicitly approved project phase ever designs execution, it must fail closed and include a global kill switch, stale-data and clock-skew checks, market-status validation, hard position/exposure limits, duplicate-order prevention, API-error handling, cancel-all behavior on integrity failure, no quoting after close, and no quoting when settlement rules cannot be resolved.
