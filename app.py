"""Inkan backend: a small JSON API over the mini-PKI, plus the static frontend."""
import datetime as dt, os, re, tempfile
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
import flask
from flask import Flask, jsonify, request
import pki, lab

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
HOST_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")

class Bad(Exception): pass

@app.errorhandler(Bad)
def _bad(e): return jsonify(error=str(e)), 400

@app.errorhandler(413)
def _big(e): return jsonify(error="Request too large."), 413

@app.after_request
def _headers(r):
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["Content-Security-Policy"] = ("default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; script-src 'self'; frame-ancestors 'none'")
    return r

def body():
    d = request.get_json(silent=True)
    if not isinstance(d, dict): raise Bad("Send a JSON body.")
    return d

def cert_from(pem, label="certificate"):
    try: return x509.load_pem_x509_certificate(str(pem).encode())
    except Exception: raise Bad(f"The {label} is not a valid PEM certificate.")

def key_from(pem):
    try: return serialization.load_pem_private_key(str(pem).encode(), password=None)
    except Exception: raise Bad("The CA private key is not a valid PEM key.")

def cn(name):
    a = name.get_attributes_for_oid(NameOID.COMMON_NAME)
    return a[0].value if a else name.rfc4514_string()

def sans(c):
    try: return c.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound: return []

def is_ca(c):
    try: return c.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
    except x509.ExtensionNotFound: return False

def describe(c):
    return dict(subject=cn(c.subject), issuer=cn(c.issuer), self_signed=c.subject == c.issuer,
        serial=format(c.serial_number, "x")[:16], not_before=c.not_valid_before_utc.isoformat(),
        not_after=c.not_valid_after_utc.isoformat(), is_ca=is_ca(c), san=sans(c),
        sig_alg=c.signature_algorithm_oid._name, key=f"{c.public_key().curve.name}" if hasattr(c.public_key(), "curve") else type(c.public_key()).__name__,
        fingerprint=c.fingerprint(hashes.SHA256()).hex())

def host_matches(pattern, host):
    p, h = pattern.lower(), host.lower()
    if p.startswith("*."): return h.count(".") == p.count(".") and h.endswith(p[1:])
    return p == h

def pem_of(path): return Path(path).read_text()

@app.get("/healthz")
def healthz(): return jsonify(ok=True)

@app.post("/api/ca")
def api_ca():
    name = str(body().get("name") or "Inkan Root CA")[:60]
    with tempfile.TemporaryDirectory() as d:
        pki.create_ca(d, name=name)
        return jsonify(cert=pem_of(Path(d) / "ca.crt"), key=pem_of(Path(d) / "ca.key"),
                       info=describe(cert_from(pem_of(Path(d) / "ca.crt"))))

@app.post("/api/issue")
def api_issue():
    d = body(); host = str(d.get("hostname", "")).strip()
    if not HOST_RE.match(host): raise Bad("Enter a valid hostname, for example shop.example.com.")
    try: days = int(d.get("days", 30))
    except (TypeError, ValueError): raise Bad("Days must be a number.")
    if not 1 <= days <= 365: raise Bad("Days must be between 1 and 365.")
    ca_c, ca_k = cert_from(d.get("ca_cert"), "CA certificate"), key_from(d.get("ca_key"))
    if not is_ca(ca_c): raise Bad("That certificate is not a CA.")
    with tempfile.TemporaryDirectory() as t:
        crt, key = pki.issue_cert(t, ca_k, ca_c, host, valid_days=days, expired=bool(d.get("expired")), prefix="leaf")
        c = pem_of(crt)
        return jsonify(cert=c, key=pem_of(key), info=describe(cert_from(c)))

@app.post("/api/inspect")
def api_inspect():
    return jsonify(info=describe(cert_from(body().get("cert"))))

@app.post("/api/verify")
def api_verify():
    d = body(); leaf, ca = cert_from(d.get("cert"), "server certificate"), cert_from(d.get("ca_cert"), "CA certificate")
    host = str(d.get("hostname", "")).strip()
    now = dt.datetime.now(dt.timezone.utc); checks = []
    def add(name, ok, detail): checks.append(dict(name=name, ok=bool(ok), detail=detail))
    try: leaf.verify_directly_issued_by(ca); add("Signature", True, f"Signed by {cn(ca.subject)}.")
    except Exception: add("Signature", False, f"Not signed by {cn(ca.subject)}; the chain of trust breaks here.")
    add("CA authority", is_ca(ca), "The signer is allowed to issue certificates." if is_ca(ca) else "The signer is not marked as a CA.")
    ok = leaf.not_valid_before_utc <= now <= leaf.not_valid_after_utc
    add("Validity period", ok, "Within its dates." if ok else ("Expired on " if now > leaf.not_valid_after_utc else "Not valid until ") +
        (leaf.not_valid_after_utc if now > leaf.not_valid_after_utc else leaf.not_valid_before_utc).strftime("%Y-%m-%d") + ".")
    if host:
        m = any(host_matches(s, host) for s in sans(leaf))
        add("Hostname", m, f"{host} is listed on the certificate." if m else f"{host} is not listed. Names on the certificate: {', '.join(sans(leaf)) or 'none'}.")
    return jsonify(valid=all(c["ok"] for c in checks), checks=checks, info=describe(leaf))

@app.post("/api/lab")
def api_lab(): return jsonify(results=lab.run_cases())

@app.get("/")
def index(): return app.send_static_file("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
