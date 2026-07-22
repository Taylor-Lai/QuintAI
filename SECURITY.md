# Security policy

Do not report credentials, production data, or exploitable details in public
issue content. Share security findings privately with the repository owner and
include the affected revision, reproduction steps, impact, and a suggested
mitigation when available.

Production deployments must provide a random `SECRET_KEY` of at least 32
characters, restrict `CORS_ORIGINS`, inject model-provider credentials through
a secret manager, and use a managed database for horizontally scaled services.

Never commit `.env`, database files, uploaded documents, generated reports,
private keys, or provider responses containing user data.
