"""Adaptador de compatibilidade da V2 para os sincronizadores existentes.

Objetivo desta primeira fase: criar uma superfície V2 uniforme sem alterar o
comportamento validado da implementação legada. A implementação específica de
cada endpoint será migrada gradualmente para V2 depois dos testes de contrato.
"""

from __future__ import annotations

import importlib
from typing import Any, Callable


FUNCTION_CANDIDATES = ("run", "sincronizar", "sincronizar_dados", "sincronizar_cursos",
                       "sincronizar_disciplinas", "sincronizar_coordenacoes",
                       "sincronizar_matriculas", "sincronizar_grades",
                       "sincronizar_turmas", "sincronizar_docentes",
                       "sincronizar_pessoas")


def resolve_entrypoint(module_name: str) -> Callable[..., Any]:
    """Localiza a função pública de execução do sincronizador legado."""
    module = importlib.import_module(module_name)
    for name in FUNCTION_CANDIDATES:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    raise AttributeError(f"Nenhum entry-point conhecido em {module_name}")


def run_legacy(module_name: str, **kwargs: Any) -> Any:
    """Executa um endpoint legado através da interface uniforme V2."""
    fn = resolve_entrypoint(module_name)
    if kwargs:
        try:
            return fn(**kwargs)
        except TypeError:
            if "modo" in kwargs:
                return fn(kwargs["modo"])
            raise
    return fn()
