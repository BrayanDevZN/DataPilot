# Functional tests

These tests exercise the locally running DataPilot API over real HTTP using
`requests.Session`, including HttpOnly cookie authentication.

## Docker

Start the backend:

```bash
docker compose up --build -d
```

Run the functional suite:

```bash
docker compose --profile test run --rm functional-tests
```

Or run the suite directly from the host:

```bash
python tests/functional/routes.py
```

Environment overrides:

```bash
FUNCTIONAL_BASE_URL=http://localhost:8000 \
FUNCTIONAL_REDIS_HOST=localhost \
FUNCTIONAL_REDIS_PORT=6379 \
python tests/functional/routes.py
```

The suite is intended for `ENVIROIMENT=test`. It seeds only the temporary
account-verification code directly in Redis; all application behavior after
that is exercised through HTTP routes.
