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

The API and Redis are exposed by Compose on localhost, which is also how the
GitHub Actions functional workflow executes the suite.

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
