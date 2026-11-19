"""Module 1 - Mini PKI: create a root CA and issue server certificates."""
import datetime as dt
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

def _name(cn):
    return x509.Name([x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CA3 Mini PKI"),
                      x509.NameAttribute(NameOID.COMMON_NAME, cn)])

def _save(path, key=None, cert=None):
    if key is not None:
        Path(path).write_bytes(key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()))
    if cert is not None:
        Path(path).write_bytes(cert.public_bytes(serialization.Encoding.PEM))

def create_ca(outdir, name="CA3 Root CA"):
    """Self-signed root CA (ECDSA P-256). Returns (key, cert)."""
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    key = ec.generate_private_key(ec.SECP256R1())
    now = dt.datetime.now(dt.timezone.utc)
    cert = (x509.CertificateBuilder()
            .subject_name(_name(name)).issuer_name(_name(name))
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - dt.timedelta(minutes=1))
            .not_valid_after(now + dt.timedelta(days=365))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(key.public_key()), critical=False)
            .add_extension(x509.KeyUsage(digital_signature=True, key_cert_sign=True,
                crl_sign=True, content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False, encipher_only=False,
                decipher_only=False), critical=True)
            .sign(key, hashes.SHA256()))
    _save(out / "ca.key", key=key); _save(out / "ca.crt", cert=cert)
    return key, cert

def issue_cert(outdir, ca_key, ca_cert, hostname, valid_days=30, expired=False, prefix=None):
    """Server certificate signed by the CA, with a SAN for `hostname`."""
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    key = ec.generate_private_key(ec.SECP256R1())
    now = dt.datetime.now(dt.timezone.utc)
    start, end = ((now - dt.timedelta(days=60), now - dt.timedelta(days=1)) if expired
                  else (now - dt.timedelta(minutes=1), now + dt.timedelta(days=valid_days)))
    cert = (x509.CertificateBuilder()
            .subject_name(_name(hostname)).issuer_name(ca_cert.subject)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(start).not_valid_after(end)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName(hostname)]), critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=False, crl_sign=False,
                encipher_only=False, decipher_only=False), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_cert.public_key()), critical=False)
            .sign(ca_key, hashes.SHA256()))
    prefix = prefix or hostname
    _save(out / f"{prefix}.key", key=key); _save(out / f"{prefix}.crt", cert=cert)
    return out / f"{prefix}.crt", out / f"{prefix}.key"
