import requests
from requests.auth import HTTPBasicAuth
import warnings
warnings.filterwarnings('ignore')

BASE_URL = "https://unifoa.lyceum.com.br:443/api"
USERNAME = "unifoa_integracao_crm_educa"
PASSWORD = "L]~=0Hy-%XMy_EU"

print("="*60)
print("TESTE: API DE CURSOS")
print("="*60)

def testar_endpoint(endpoint):
    """Testa um endpoint da API"""
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            params={"page": 1, "size": 10},
            timeout=30,
            verify=False
        )
        
        print(f"\n🔍 Endpoint: {endpoint}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'data' in data:
                print(f"   ✅ Estrutura: dict com 'data' (lista)")
                print(f"   📊 Total de itens: {len(data['data'])}")
                
                if len(data['data']) > 0:
                    primeiro = data['data'][0]
                    print(f"   📋 Campos disponíveis: {list(primeiro.keys())}")
                    print(f"   📋 Primeiro registro:")
                    for key, value in list(primeiro.items())[:5]:
                        print(f"      {key}: {value}")
            else:
                print(f"   ⚠️  Estrutura inesperada: {type(data)}")
                print(f"   📄 Amostra: {str(data)[:200]}")
        else:
            print(f"   ❌ Resposta: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

# Testar diferentes endpoints de cursos
endpoints_cursos = [
    "/v2/tabela/cursos",
    "/v2/cursos",
    "/cursos",
    "/v2/tabela/curso",
    "/tabela/cursos"
]

for endpoint in endpoints_cursos:
    testar_endpoint(endpoint)

# Testar endpoint de currículos
print("\n" + "="*60)
print("TESTE: API DE CURRÍCULOS")
print("="*60)

endpoints_curriculos = [
    "/v2/tabela/curriculos",
    "/v2/curriculos",
    "/curriculos",
    "/v2/tabela/curriculo",
    "/tabela/curriculos"
]

for endpoint in endpoints_curriculos:
    testar_endpoint(endpoint)