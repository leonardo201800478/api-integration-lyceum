from core.api_client import get_pessoa_client
client = get_pessoa_client()

# Substitua por um ID que você tem certeza que existe (ex: 4000238433)
id_teste = 4000238433

print("🔍 Testando parâmetros para buscar pessoa", id_teste)

# Teste 1: pk[pessoa] (padrão da API Lyceum)
r1 = client.get("/v2/tabela/pessoas", params={"pk[pessoa]": id_teste})
print("1. pk[pessoa]:", r1)

# Teste 2: pessoa
r2 = client.get("/v2/tabela/pessoas", params={"pessoa": id_teste})
print("2. pessoa:", r2)

# Teste 3: pk[codPessoa]
r3 = client.get("/v2/tabela/pessoas", params={"pk[codPessoa]": id_teste})
print("3. pk[codPessoa]:", r3)

# Teste 4: codPessoa
r4 = client.get("/v2/tabela/pessoas", params={"codPessoa": id_teste})
print("4. codPessoa:", r4)

# Teste 5: filtro com 'filter' (algumas APIs usam)
r5 = client.get("/v2/tabela/pessoas", params={"filter": f"pessoa eq {id_teste}"})
print("5. filter:", r5)

# Teste 6: sem filtro, só para ver a estrutura
r6 = client.get("/v2/tabela/pessoas", params={"page": 0, "size": 1})
print("6. Primeiro registro (sem filtro):", r6)

client.close()