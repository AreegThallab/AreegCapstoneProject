# DAWRAH Security Configuration

DAWRAH reads local configuration from environment variables. For local
development on Windows or VS Code, copy `.env.example` to `.env` in the project
root and replace the placeholder secret key with a local development value.

Required variable:

- `DJANGO_SECRET_KEY`: Django secret key. Do not commit real values.

Optional variables:

- `DJANGO_DEBUG`: `True` for local development, `False` outside development.
- `DJANGO_ALLOWED_HOSTS`: comma-separated hosts, such as `localhost,127.0.0.1`.

The `.env` file is ignored by Git. The project also supports variables already
set in the operating system environment; OS values take precedence over `.env`.

Example local setup:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and set a local-only `DJANGO_SECRET_KEY`.
