# Security Policy

## Supported Scope

Security reports for the open-source tools in this repository are welcome,
especially for:

- `mythology-dictionary/`
- `.tools/github-utility-starters/`

The static GitHub Pages site and bundled game/export assets are maintained
separately from the OSS tooling.

## Reporting

Please open a private report through GitHub's security advisory flow if it is
available for this repository. If not, open a minimal public issue that says a
security report is available and avoid posting exploit details.

## Notes

The mythology dictionary is local-first and binds Streamlit to `127.0.0.1` by
default. Do not expose the app directly to the public internet without adding
authentication, backups, and an explicit deployment review.

