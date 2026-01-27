import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd
from datetime import datetime
import time

def test_conexao_api():
    """Testa conexão básica com a API"""
    
    print("="*60)
    print("TESTE DE CONEXÃO COM API LY_ALUNO")
    print("="*60)
    
    # Configurações
    BASE_URL = "https://unifoa.lyceum.com.br:443/api"
    ENDPOINT = "/v2/tabela/alunos"

    # https://unifoa.lyceum.com.br:443/api/v2/tabela/matriculas?page=1&size=100
    # https://unifoa.lyceum.com.br/api/v2/tabela/alunos?pk%5Baluno%5D=201400582%22
    
    USERNAME = "unifoa_integracao_crm_educa"
    PASSWORD = "L]~=0Hy-%XMy_EU"
    
    # Lista para armazenar resultados
    alunos = []
    
    try:
        print(f"\n🔗 Conectando em: {BASE_URL}{ENDPOINT}")
        print(f"👤 Usuário: {USERNAME}")
        print(f"⏳ Aguarde...")
        
        # Testar primeiro um aluno específico
        aluno_teste = "201400582"  # Substitua por um código válido
        print(f"\n📋 Testando aluno específico: {aluno_teste}")
        
        response = requests.get(
            f"{BASE_URL}{ENDPOINT}",
            params={"pk[aluno]": aluno_teste},
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            timeout=30,
            verify=True  # Verificar SSL
        )
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Formato JSON válido")
                print(f"📊 Estrutura do dado: {type(data)}")
                
                # Mostrar estrutura do primeiro registro
                if isinstance(data, dict):
                    print("\n📋 Campos disponíveis:")
                    for key in data.keys():
                        print(f"   - {key}: {type(data[key]).__name__}")
                elif isinstance(data, list):
                    print(f"\n📊 Total de registros: {len(data)}")
                    if len(data) > 0:
                        print("\n📋 Primeiro registro:")
                        for key, value in data[0].items():
                            print(f"   - {key}: {value}")
                
                return data
                
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao decodificar JSON: {e}")
                print(f"📄 Resposta bruta (primeiros 500 chars):")
                print(response.text[:500])
                return None
                
        elif response.status_code == 401:
            print("❌ ERRO 401: Não autorizado")
            print("Verifique usuário e senha")
            
        elif response.status_code == 404:
            print("❌ ERRO 404: Endpoint não encontrado")
            print(f"URL tentada: {BASE_URL}{ENDPOINT}")
            print("\n💡 Dica: Verifique se o endpoint está correto")
            print("O endpoint pode ser: /api/v2/tabela/alunos")
            print("Ou apenas: /v2/tabela/alunos")
            
        elif response.status_code == 403:
            print("❌ ERRO 403: Acesso proibido")
            print("Você pode não ter permissão para este recurso")
            
        else:
            print(f"❌ Status inesperado: {response.status_code}")
            print(f"Resposta: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: A API demorou muito para responder")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão: Verifique URL e internet")
        
    except requests.exceptions.SSLError:
        print("❌ Erro SSL: Tentando sem verificação...")
        # Tentar sem verificar SSL (apenas para teste)
        try:
            response = requests.get(
                f"{BASE_URL}{ENDPOINT}",
                params={"pk[aluno]": aluno_teste},
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                timeout=30,
                verify=False  # Não verificar SSL
            )
            print(f"✅ Conexão sem SSL: Status {response.status_code}")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"❌ Falha mesmo sem SSL: {e}")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {type(e).__name__}: {e}")
        
    return None

def buscar_primeiros_alunos(quantidade=100):
    """Busca os primeiros N alunos"""
    
    print("\n" + "="*60)
    print(f"BUSCANDO PRIMEIROS {quantidade} ALUNOS")
    print("="*60)
    
    BASE_URL = "https://unifoa.lyceum.com.br/api"
    ENDPOINT = "/v2/tabela/alunos"
    
    USERNAME = "unifoa_integracao_crm_educa"
    PASSWORD = "L]~=0Hy-%XMy_EU"
    
    todos_alunos = []
    
    # Se a API não suportar paginação, precisamos buscar um por um
    # Primeiro, vamos descobrir como funciona
    
    print("🔍 Descobrindo como buscar múltiplos alunos...")
    
    # Tentativa 1: Sem parâmetro específico (pode trazer todos)
    try:
        print("📤 Tentando buscar sem parâmetro...")
        response = requests.get(
            f"{BASE_URL}{ENDPOINT}",
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            timeout=60,
            verify=False  # Temporariamente para testes
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                print(f"🎉 Sucesso! Encontrados {len(data)} alunos")
                return data[:quantidade]
            elif isinstance(data, dict):
                print(f"⚠️  Retornou objeto único, não lista")
                return [data]
                
    except Exception as e:
        print(f"❌ Tentativa 1 falhou: {e}")
    
    # Tentativa 2: Com paginação
    print("\n📤 Tentando com paginação...")
    for i in range(1, quantidade + 1):
        try:
            aluno_id = str(i).zfill(5)  # Formato 00001, 00002...
            
            response = requests.get(
                f"{BASE_URL}{ENDPOINT}",
                params={"pk[aluno]": aluno_id},
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                aluno_data = response.json()
                todos_alunos.append(aluno_data)
                print(f"✅ Aluno {aluno_id} encontrado")
            else:
                print(f"⚠️  Aluno {aluno_id} não encontrado")
            
            # Delay para não sobrecarregar API
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Erro no aluno {aluno_id}: {e}")
            continue
    
    return todos_alunos

def salvar_resultados(alunos, formato='json'):
    """Salva os resultados em arquivo"""
    
    if not alunos:
        print("⚠️  Nenhum dado para salvar")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if formato == 'json':
        filename = f"alunos_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(alunos, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 Dados salvos em: {filename}")
        
    elif formato == 'csv' and alunos:
        # Converter para DataFrame do pandas
        df = pd.json_normalize(alunos)
        filename = f"alunos_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 Dados salvos em CSV: {filename}")
        print(f"📊 Colunas: {', '.join(df.columns)}")
        
    return filename

def main():
    """Função principal"""
    
    print("\n" + "="*60)
    print("SISTEMA DE SINCRONIZAÇÃO DE ALUNOS - UNIFOA")
    print("="*60)
    
    # 1. Testar conexão
    resultado_teste = test_conexao_api()
    
    if resultado_teste:
        print("\n" + "="*60)
        print("✅ CONEXÃO BEM SUCEDIDA!")
        print("="*60)
        
        # Perguntar se quer buscar mais alunos
        resposta = input("\n📝 Buscar primeiros 100 alunos? (s/n): ").lower()
        
        if resposta == 's':
            alunos = buscar_primeiros_alunos(100)
            
            if alunos:
                print(f"\n📊 Total de alunos obtidos: {len(alunos)}")
                
                # Mostrar resumo
                print("\n📋 RESUMO DOS DADOS:")
                for i, aluno in enumerate(alunos[:3]):  # Primeiros 3 como exemplo
                    print(f"\nAluno {i+1}:")
                    for key, value in list(aluno.items())[:5]:  # Primeiros 5 campos
                        print(f"  {key}: {value}")
                
                # Salvar resultados
                resposta_salvar = input("\n💾 Salvar resultados? (json/csv/n): ").lower()
                if resposta_salvar in ['json', 'csv']:
                    salvar_resultados(alunos, resposta_salvar)
                elif resposta_salvar != 'n':
                    salvar_resultados(alunos, 'json')
                    
            else:
                print("❌ Nenhum aluno encontrado")
    else:
        print("\n❌ Não foi possível conectar à API")
        print("\n💡 SOLUÇÕES:")
        print("1. Verifique usuário e senha")
        print("2. Verifique se a URL está correta")
        print("3. Verifique conexão com internet")
        print("4. Verifique se tem acesso à API externamente")
        print("5. Tente usar VPN se estiver na rede da faculdade")

if __name__ == "__main__":
    main()