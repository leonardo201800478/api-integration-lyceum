# reports/exporters/base.py
from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path

class Exporter(ABC):
    """Classe base para todos os exportadores de relatórios."""

    @abstractmethod
    def export(self, data: pd.DataFrame, output_path: Path, **kwargs) -> bool:
        """
        Exporta os dados para o formato desejado.
        :param data: DataFrame com os dados a exportar.
        :param output_path: Caminho completo do arquivo de saída.
        :param kwargs: Parâmetros adicionais específicos do formato.
        :return: True se sucesso, False caso contrário.
        """
        pass