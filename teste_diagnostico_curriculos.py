import requests
from requests.auth import HTTPBasicAuth
import warnings
warnings.filterwarnings('ignore')

BASE_URL = "https://unifoa.lyceum.com.br:443/api"
USERNAME = "unifoa_integracao_crm_educa"
PASSWORD = "L]~=0Hy-%XMy_EU"

print("="*70)
print("DIAGNÓSTICO DETALHADO: API DE CURRÍCULOS")
print("="*70)

def testar_endpoint_curriculos_sem_filtro():
    """Testa o endpoint de currículos sem filtro"""
    print("\n🔍 1. TESTANDO ENDPOINT SEM FILTRO...")
    
    endpoint = "/v2/tabela/curriculos"
    
    # Testar diferentes tamanhos de página
    for size in [10, 50, 100]:
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                params={"page": 1, "size": size},
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                timeout=30,
                verify=False
            )
            
            print(f"\n📄 Tamanho {size}: Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'data' in data:
                    print(f"   ✅ Encontrados: {len(data['data'])} currículos")
                    
                    if len(data['data']) > 0:
                        # Agrupar por curso
                        cursos_dict = {}
                        for curriculo in data['data']:
                            curso = curriculo.get('curso')
                            curriculo_cod = curriculo.get('curriculo')
                            if curso not in cursos_dict:
                                cursos_dict[curso] = []
                            cursos_dict[curso].append(curriculo_cod)
                        
                        print(f"   📊 Cursos encontrados: {len(cursos_dict)}")
                        print(f"   📋 Primeiros 5 cursos com currículos:")
                        for i, (curso, curriculos) in enumerate(list(cursos_dict.items())[:5]):
                            print(f"      {i+1}. Curso {curso}: {len(curriculos)} currículos: {curriculos}")
                else:
                    print(f"   ⚠️  Estrutura inesperada")
            else:
                print(f"   ❌ Erro: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def testar_filtro_curso_especifico(codigo_curso):
    """Testa filtro para um curso específico"""
    print(f"\n🔍 2. TESTANDO FILTRO PARA CURSO {codigo_curso}...")
    
    endpoint = "/v2/tabela/curriculos"
    
    # Testar diferentes formatos de parâmetros de filtro
    parametros_testar = [
        {"curso": codigo_curso},
        {"filter[curso]": codigo_curso},
        {"pk[curso]": codigo_curso},
        {"curso_id": codigo_curso},
        {"codigo_curso": codigo_curso},
        {"search": codigo_curso},
        {"q": codigo_curso}
    ]
    
    for params in parametros_testar:
        try:
            print(f"\n📋 Parâmetros: {params}")
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                params={**params, "page": 1, "size": 20},
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                timeout=30,
                verify=False
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'data' in data:
                    print(f"   ✅ Resultados: {len(data['data'])}")
                    
                    if len(data['data']) > 0:
                        print(f"   📋 Currículos encontrados:")
                        for curriculo in data['data'][:5]:
                            print(f"      - Currículo: {curriculo.get('curriculo')}, Turno: {curriculo.get('turno')}, Prazo Ideal: {curriculo.get('prazo_ideal')}")
                else:
                    print(f"   📄 Resposta: {str(data)[:200]}")
            elif response.status_code == 404:
                print(f"   ❌ 404 Not Found")
            else:
                print(f"   ❌ Status inesperado")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def testar_estrutura_curriculo_detalhada():
    """Testa estrutura detalhada de um currículo específico"""
    print("\n🔍 3. TESTANDO ESTRUTURA DETALHADA DE UM CURRÍCULO...")
    
    # Primeiro, buscar alguns currículos sem filtro
    endpoint = "/v2/tabela/curriculos"
    
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            params={"page": 1, "size": 5},
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'data' in data and len(data['data']) > 0:
                curriculo = data['data'][0]
                print(f"\n📋 Estrutura do primeiro currículo encontrado:")
                print(f"   Curso: {curriculo.get('curso')}")
                print(f"   Currículo: {curriculo.get('curriculo')}")
                print(f"   Turno: {curriculo.get('turno')}")
                print(f"   Prazo Ideal: {curriculo.get('prazo_ideal')}")
                print(f"   Ano Início: {curriculo.get('ano_ini')}")
                print(f"   Semestre Início: {curriculo.get('sem_ini')}")
                
                # Mostrar outros campos importantes
                campos_importantes = ['regime', 'aulas_previstas', 'creditos', 'prazo_max']
                for campo in campos_importantes:
                    if campo in curriculo:
                        print(f"   {campo}: {curriculo.get(campo)}")
            else:
                print("❌ Nenhum currículo encontrado")
        else:
            print(f"❌ Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def testar_metadados_api():
    """Testa metadados da API"""
    print("\n🔍 4. TESTANDO METADADOS DA API...")
    
    # Tentar acessar documentação/swagger
    endpoints_doc = [
        "/swagger-ui.html",
        "/v2/api-docs",
        "/api-docs",
        "/docs"
    ]
    
    for doc in endpoints_doc:
        try:
            response = requests.get(
                f"{BASE_URL}{doc}",
                timeout=10,
                verify=False
            )
            if response.status_code == 200:
                print(f"✅ Documentação encontrada em: {doc}")
                if "swagger" in response.text.lower():
                    print(f"   ✅ É Swagger/OpenAPI")
                    # Procurar por endpoint de currículos na documentação
                    if "curricul" in response.text.lower():
                        print(f"   ✅ Endpoint de currículos mencionado")
        except:
            pass

def main():
    # 1. Testar endpoint sem filtro
    testar_endpoint_curriculos_sem_filtro()
    
    # 2. Testar com cursos específicos
    cursos_para_testar = ["404", "401", "127", "128", "129", "400"]
    for curso in cursos_para_testar:
        testar_filtro_curso_especifico(curso)
    
    # 3. Testar estrutura detalhada
    testar_estrutura_curriculo_detalhada()
    
    # 4. Testar metadados
    testar_metadados_api()
    
    print("\n" + "="*70)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("="*70)

if __name__ == "__main__":
    main()