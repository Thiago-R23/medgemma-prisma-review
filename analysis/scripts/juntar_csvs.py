"""
Script para unir todos os arquivos .csv de uma pasta em um único arquivo CSV.

Uso:
    python juntar_csvs.py
"""

import pandas as pd
from pathlib import Path

# ---- Configurações (ajuste se necessário) ----
PASTA_ENTRADA = Path("/home/thcaballicare/medgemma-prisma-review/search_results")
ARQUIVO_SAIDA = Path("/home/thcaballicare/medgemma-prisma-review/analysis/combined_search_results.csv")


def ler_csv_robusto(caminho: Path) -> pd.DataFrame:
    """Tenta ler um CSV testando diferentes codificações comuns."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(caminho, encoding=encoding)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise RuntimeError(f"Falha ao ler {caminho.name}: {e}")
    raise RuntimeError(f"Não foi possível decodificar {caminho.name}.")


def main():
    arquivos_csv = sorted(PASTA_ENTRADA.glob("*.csv"))

    if not arquivos_csv:
        print(f"Nenhum arquivo .csv encontrado em: {PASTA_ENTRADA}")
        return

    print(f"Encontrados {len(arquivos_csv)} arquivos .csv:")
    for f in arquivos_csv:
        print(f"  - {f.name}")

    dataframes = []
    for arquivo in arquivos_csv:
        try:
            df = ler_csv_robusto(arquivo)
            df["arquivo_origem"] = arquivo.name  # marca de qual arquivo veio cada linha
            dataframes.append(df)
            print(f"OK: {arquivo.name} ({len(df)} linhas, {len(df.columns) - 1} colunas)")
        except Exception as e:
            print(f"ERRO ao ler {arquivo.name}: {e}")

    if not dataframes:
        print("Nenhum arquivo pôde ser lido com sucesso.")
        return

    # Junta todos os dataframes, mesmo que tenham colunas diferentes entre si
    df_final = pd.concat(dataframes, ignore_index=True, sort=False)

    # Garante que a pasta de saída existe
    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(ARQUIVO_SAIDA, index=False)

    print(f"\nArquivo final salvo em: {ARQUIVO_SAIDA}")
    print(f"Total de linhas: {len(df_final)}")
    print(f"Total de colunas: {len(df_final.columns)}")


if __name__ == "__main__":
    main()
