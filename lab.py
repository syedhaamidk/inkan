"""Handshake Lab: runs real TLS handshakes on loopback against five certificate situations."""
import ssl, tempfile, threading, time
from pathlib import Path
import pki, server, client

_lock = threading.Lock()
CASES = [  # name, use rogue CA, cert hostname, expired, client max TLS, expect accept, why
    ("Valid certificate", False, "localhost", False, None, True, "Signed by the trusted CA, in date, name matches."),
    ("Unknown CA", True, "localhost", False, None, False, "The signer is not in the client's trust store, so the chain cannot be built."),
    ("Expired certificate", False, "localhost", True, None, False, "The validity period ended yesterday."),
    ("Wrong hostname", False, "other.local", False, None, False, "The certificate names other.local, not the host the client asked for."),
    ("Legacy TLS 1.1 client", False, "localhost", False, ssl.TLSVersion.TLSv1_1, False, "The server requires TLS 1.2 or newer; old versions are refused."),
]

def run_cases():
    with _lock, tempfile.TemporaryDirectory(prefix="inkan_") as d:
        w = Path(d)
        ca_k, ca_c = pki.create_ca(w / "ca")
        rg_k, rg_c = pki.create_ca(w / "rg", name="Rogue CA")
        out = []
        for i, (name, rogue, host, exp, maxv, want, why) in enumerate(CASES):
            k, c = (rg_k, rg_c) if rogue else (ca_k, ca_c)
            crt, key = pki.issue_cert(w / "c", k, c, host, expired=exp, prefix=f"s{i}")
            stop, ready = threading.Event(), []
            t = threading.Thread(target=server.serve, args=(str(crt), str(key)),
                                 kwargs={"ready": ready, "stop": stop}, daemon=True)
            t.start()
            while not ready: time.sleep(0.01)
            try:
                r = client.connect("127.0.0.1", ready[0], str(w / "ca" / "ca.crt"), "localhost", max_version=maxv)
                acc, detail = True, f"{r['version']} · {r['cipher']}"
            except (ssl.SSLError, OSError) as e:
                acc, detail = False, getattr(e, "verify_message", None) or str(e).split("] ")[-1][:80]
            stop.set(); t.join(timeout=2)
            out.append(dict(name=name, accepted=acc, expected=want, ok=acc == want, detail=detail, why=why))
        return out
