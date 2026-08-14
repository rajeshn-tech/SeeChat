import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import DNSName, IPAddress
import ipaddress

def generate_self_signed_cert(cert_file='cert.pem', key_file='key.pem'):
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"[SECURITY] Existing TLS SSL certificates found ('{cert_file}', '{key_file}'). Overwrite skipped to preserve certificate stability.")
        return cert_file, key_file

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "MH"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Mumbai"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SeeChat Studio"),
        x509.NameAttribute(NameOID.COMMON_NAME, "seechat"),
    ])

    alt_names = [
        DNSName("seechat"),
        DNSName("localhost"),
        IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ]

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
        .sign(key, hashes.SHA256())
    )

    with open(key_file, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"Generated SSL certificate '{cert_file}' and private key '{key_file}' successfully!")
    return cert_file, key_file

if __name__ == "__main__":
    generate_self_signed_cert()
