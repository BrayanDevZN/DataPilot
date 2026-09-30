# Functional tests

These tests exercise the locally running DataPilot API over real HTTP using
`requests.Session`, including HttpOnly cookie authentication.

## Docker

Start the backend:

```bash
docker compose up --build -d
```

Run the functional suite from the host:

```bash
python tests/functional/routes.py
```

The GitHub Actions workflow starts the stack and lets the Python runner wait
for the API through HTTP.

Environment override:

```bash
FUNCTIONAL_BASE_URL=http://localhost:8000 \
python tests/functional/routes.py
```

The suite is intended for `ENVIROIMENT=test`. Verification-code endpoints
return the generated code only in test mode, so the functional runner exercises
the complete flow exclusively through HTTP without reading Redis directly.
