import requests
import sys
from core.config import config

def test_api_connection():
    print("🧪 Testando conexão com a API...")
    
    # Verifica configurações
    print(f"Base URL: {config.LYCEUM_BASE_URL}")
    print(f"Username: {config.LYCEUM_USERNAME}")
    print(f"Password: {'*' * len(config.LYCEUM_PASSWORD) if config.LYCEUM_PASSWORD else 'Não configurado'}")
    
    if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
        print("❌ Configurações incompletas no .env")
        return False
    
    # Testa conexão básica
    url = f"{config.LYCEUM_BASE_URL.rstrip('/')}/v2/tabela/alunos"
    auth = (config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD)
    
    print(f"\n🔗 URL da API: {url}")
    
    try:
        # Teste sem parâmetros de paginação primeiro
        print("\n📡 Testando endpoint sem parâmetros...")
        response = requests.get(
            url,
            auth=auth,
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Resposta JSON: {data}")
                if isinstance(data, list):
                    print(f"Total de alunos na primeira página: {len(data)}")
                else:
                    print(f"Tipo de resposta: {type(data)}")
                    print(f"Conteúdo: {data}")
            except Exception as e:
                print(f"Conteúdo da resposta (não JSON): {response.text[:500]}")
        else:
            print(f"Resposta: {response.text[:500]}")
            
        # Teste com parâmetros de paginação
        print("\n📡 Testando endpoint com paginação...")
        response = requests.get(
            url,
            auth=auth,
            headers={"Accept": "application/json"},
            params={"page": 0, "size": 10},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list):
                    print(f"Total de alunos na página 0 (size=10): {len(data)}")
                    if len(data) > 0:
                        print(f"\n📋 Exemplo do primeiro aluno:")
                        for key, value in data[0].items():
                            print(f"  {key}: {value}")
                else:
                    print(f"Resposta: {data}")
            except Exception as e:
                print(f"Erro ao parsear JSON: {e}")
                print(f"Conteúdo: {response.text[:500]}")
        else:
            print(f"Resposta: {response.text[:500]}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

if __name__ == "__main__":
    success = test_api_connection()
    sys.exit(0 if success else 1)