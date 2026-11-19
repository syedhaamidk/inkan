"""Module 3 - TLS client: verifies the server certificate chain, dates and hostname."""
import socket, ssl

def connect(host, port, ca_file, server_hostname, message=b"hello tls",
            max_version=None):
    ctx = ssl.create_default_context(cafile=ca_file)   # verify + check_hostname ON
    ctx.verify_flags |= ssl.VERIFY_X509_STRICT          # strict X.509 rules (default on Python 3.13+)
    if max_version is not None:
        ctx.maximum_version = max_version
    with socket.create_connection((host, port), timeout=5) as raw:
        with ctx.wrap_socket(raw, server_hostname=server_hostname) as tls:
            tls.sendall(message)
            reply = tls.recv(4096)
            return {"version": tls.version(), "cipher": tls.cipher()[0],
                    "peer_subject": dict(x[0] for x in tls.getpeercert()["subject"]),
                    "reply": reply.decode()}

if __name__ == "__main__":
    import sys
    print(connect("127.0.0.1", int(sys.argv[3]), sys.argv[1], sys.argv[2]))
