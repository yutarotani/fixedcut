#!/usr/bin/env python3
"""
自己署名証明書を生成するスクリプト
ローカル開発用に使用してください。
"""

import ssl
import os
import ipaddress

# 証明書ファイル名
CERT_FILE = 'cert.pem'
KEY_FILE = 'key.pem'

# 証明書情報
CERT_INFO = {
    'country_name': 'JP',
    'state_or_province_name': 'Tokyo',
    'locality_name': 'Tokyo',
    'organization_name': 'Local Development',
    'organizational_unit_name': 'Development',
    'common_name': 'localhost',
    'email_address': 'dev@localhost'
}

def create_self_signed_cert():
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
    import datetime

    # 秘密鍵生成
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # 証明書情報
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, CERT_INFO['country_name']),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, CERT_INFO['state_or_province_name']),
        x509.NameAttribute(NameOID.LOCALITY_NAME, CERT_INFO['locality_name']),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, CERT_INFO['organization_name']),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, CERT_INFO['organizational_unit_name']),
        x509.NameAttribute(NameOID.COMMON_NAME, CERT_INFO['common_name']),
        x509.NameAttribute(NameOID.EMAIL_ADDRESS, CERT_INFO['email_address']),
    ])

    # 証明書生成
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName('localhost'),
            x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256(), default_backend())

    # PEM形式で保存
    with open(CERT_FILE, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    with open(KEY_FILE, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    print(f"証明書を生成しました: {CERT_FILE}, {KEY_FILE}")

if __name__ == '__main__':
    try:
        create_self_signed_cert()
    except ImportError:
        print("cryptography ライブラリが必要です。インストールしてください: pip install cryptography")
    except Exception as e:
        print(f"エラーが発生しました: {e}")