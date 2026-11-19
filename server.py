"""Module 2 - TLS server: presents a certificate, requires TLS 1.2+, echoes upper-case."""
import socket, ssl, threading

def make_context(certfile, keyfile):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2      # refuse SSLv3/TLS1.0/1.1
    ctx.load_cert_chain(certfile, keyfile)
    return ctx

def _handle(conn):
    try:
        with conn:
            data = conn.recv(4096)
            if data:
                conn.sendall(data.upper())
    except (ssl.SSLError, OSError):
        pass          # failed handshakes (bad client) are simply dropped

def serve(certfile, keyfile, host="127.0.0.1", port=0, ready=None, stop=None):
    """Run until `stop` (threading.Event) is set. Reports its port via `ready` list."""
    ctx = make_context(certfile, keyfile)
    with socket.socket() as sock:
        sock.bind((host, port)); sock.listen(5); sock.settimeout(0.2)
        if ready is not None:
            ready.append(sock.getsockname()[1])
        while not (stop and stop.is_set()):
            try:
                raw, _ = sock.accept()
            except socket.timeout:
                continue
            try:
                conn = ctx.wrap_socket(raw, server_side=True)
            except (ssl.SSLError, OSError):
                raw.close(); continue
            threading.Thread(target=_handle, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    import sys
    cert, key, port = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 8443
    print(f"TLS server on 127.0.0.1:{port}"); serve(cert, key, port=port)
