from typing import Dict, List, Optional

class CursoProcessor:
    """Processador de dados para cursos IMP-001"""
    
    @staticmethod
    def filter_cursos(cursos_data: List[Dict]) -> List[Dict]:
        """Filtra cursos: ativo='S' e faculdade em ['001', '002']"""
        filtered = []
        for curso in cursos_data:
            ativo = curso.get("ativo", "")
            faculdade = curso.get("faculdade", "")
            
            if ativo == "S" and faculdade in ["001", "002"]:
                filtered.append(curso)
        
        print(f"📊 Cursos após filtro (ativo='S' e faculdade em ['001','002']): {len(filtered)}/{len(cursos_data)}")
        return filtered
    
    @staticmethod
    def process_curso(curso_data: Dict) -> Optional[Dict]:
        """Processa dados de um curso para formato IMP-001"""
        try:
            codigo = curso_data.get("curso", "")
            nome = curso_data.get("nome", "")
            
            if not all([codigo, nome]):
                return None
            
            return {
                "codigoCurso": str(codigo)[:30],
                "nomeCurso": str(nome)[:64],
                "codigoUnidadeOrganizacional": "4000000001",  # Valor fixo
                "quantPeriodos": None,  # Será preenchido depois com os currículos
                "ativo": True
            }
        except Exception as e:
            print(f"❌ Erro ao processar curso {curso_data.get('curso', 'N/A')}: {e}")
            return None
    
    @staticmethod
    def process_batch(cursos_data: List[Dict]) -> List[Dict]:
        """Processa um lote de cursos"""
        # Primeiro filtra
        filtered = CursoProcessor.filter_cursos(cursos_data)
        
        # Depois processa
        processed = []
        for curso in filtered:
            processed_curso = CursoProcessor.process_curso(curso)
            if processed_curso:
                processed.append(processed_curso)
        
        print(f"📦 Cursos processados: {len(processed)}/{len(cursos_data)}")
        return processed


class CurriculoProcessor:
    """Processador para dados de currículos"""
    
    @staticmethod
    def get_maior_curriculo_por_curso(curriculos_data: List[Dict]) -> Dict[str, Dict]:
        """
        Para cada curso, encontra o currículo com o maior código de currículo.
        Retorna um dicionário: {codigo_curso: {dados_do_curriculo}}
        """
        # Agrupar por curso
        curriculos_por_curso = {}
        
        for curriculo in curriculos_data:
            curso = curriculo.get("curso", "")
            if not curso:
                continue
            
            curriculo_codigo = curriculo.get("curriculo", "")
            if not curriculo_codigo:
                continue
            
            # Se não tem currículo para este curso ou se o atual é maior
            if curso not in curriculos_por_curso:
                curriculos_por_curso[curso] = curriculo
            else:
                # Comparar os códigos de currículo (como string, mas pode ser numérico)
                # Assumindo que o maior código é o mais recente
                if curriculo_codigo > curriculos_por_curso[curso].get("curriculo", ""):
                    curriculos_por_curso[curso] = curriculo
        
        print(f"📊 Currículos encontrados para {len(curriculos_por_curso)} cursos")
        return curriculos_por_curso
    
    @staticmethod
    def extrair_prazo_ideal(curriculo_data: Dict) -> Optional[int]:
        """Extrai o prazo_ideal do currículo, convertendo para inteiro se possível"""
        prazo_ideal = curriculo_data.get("prazo_ideal")
        
        if prazo_ideal is None:
            return None
        
        try:
            return int(prazo_ideal)
        except (ValueError, TypeError):
            return None