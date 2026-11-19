# Inkan: a pocket certificate authority (Cryptography CA3)

Flask backend plus a themed frontend. Create a CA, issue a certificate, check it the way a browser does,
and run real TLS handshakes that succeed or fail for five reasons.

## Run locally
    pip install -r requirements.txt
    python app.py                      # http://localhost:8000
    python -c "import test_app as t; t.test_flow(); t.test_bad_input(); t.test_lab_and_static()"

## Deploy
Any of these work with the files already here.
- **Render:** push this folder to GitHub, then New > Blueprint. `render.yaml` and the `Dockerfile` do the rest.
- **Railway / Heroku:** push the repo. The `Procfile` runs gunicorn on `$PORT`.
- **Docker anywhere:** `docker build -t inkan .` then `docker run -p 8000:8000 inkan`

## API
| Route | Purpose |
|---|---|
| POST /api/ca | create a root CA (returns PEM cert, key, details) |
| POST /api/issue | issue a server certificate from a CA |
| POST /api/inspect | read the fields of a PEM certificate |
| POST /api/verify | check signature, CA flag, validity dates and hostname |
| POST /api/lab | run five real TLS handshakes on loopback |
| GET /healthz | health check |

## Files
app.py (API) · pki.py (CA and issuing) · server.py / client.py (TLS) · lab.py (handshake scenarios)
· static/ (frontend) · test_app.py

## Limits
Stateless by design: nothing is stored on the server, and keys are returned to the browser for practice use only.
No login, rate limiting or revocation (CRL/OCSP). Add rate limiting (for example Flask-Limiter) before public use.
