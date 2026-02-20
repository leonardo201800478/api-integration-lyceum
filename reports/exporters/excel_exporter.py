import pandas as pd
from pathlib import Path
from core.logger import logger

class ExcelExporter:
    """Exporta DataFrame para Excel com formatação básica."""

    def export(self, data: pd.DataFrame, output_path: Path, sheet_name="Relatório") -> bool:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                data.to_excel(writer, sheet_name=sheet_name, index=False)
                # Ajustar largura das colunas automaticamente
                worksheet = writer.sheets[sheet_name]
                for column in data:
                    column_length = max(data[column].astype(str).map(len).max(), len(column))
                    col_idx = data.columns.get_loc(column)
                    worksheet.column_dimensions[chr(65 + col_idx)].width = column_length + 2
            logger.info(f"Excel gerado: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao gerar Excel: {e}", exc_info=True)
            return False