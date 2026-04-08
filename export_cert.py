# export_cert.py
# Rode na raiz do projeto:
#   python export_cert.py

import ssl
import socket

HOST = "unifoa.lyceum.com.br"
PORT = 443
OUTPUT = "lyceum_ca_bundle.crt"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

pems = []

with socket.create_connection((HOST, PORT), timeout=10) as sock:
    with ctx.wrap_socket(sock, server_hostname=HOST) as ssock:
        # Captura toda a cadeia de certificados (proxy incluso)
        chain = ssock.get_verified_chain() if hasattr(ssock, "get_verified_chain") else None

        if chain:
            for cert_bin in chain:
                pems.append(ssl.DER_cert_to_PEM_cert(cert_bin))
        else:
            # Fallback: apenas o certificado do servidor
            cert_bin = ssock.getpeercert(binary_form=True)
            pems.append(ssl.DER_cert_to_PEM_cert(cert_bin))

with open(OUTPUT, "w") as f:
    f.writelines(pems)

print(f"✅ {len(pems)} certificado(s) salvo(s) em: {OUTPUT}")
print("➡️  Atualize o .env: LYCEUM_SSL_VERIFY=lyceum_ca_bundle.crt")