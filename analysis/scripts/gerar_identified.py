"""
Gera o arquivo 'identified.csv' — primeira etapa do fluxo PRISMA
(Identification: registros identificados nas bases de dados).

Lê o combined_search_results.csv (saída do juntar_csvs.py) e padroniza as
colunas das diferentes bases (arXiv, PubMed, Semantic Scholar, Crossref/ACM)
em um esquema único, adicionando um ID de rastreio para cada registro.

Uso:
    python gerar_identified.py
"""

import re
import pandas as pd
from pathlib import Path

# ---- Configurações (ajuste se necessário) ----
ARQUIVO_ENTRADA = Path("/home/thcaballicare/medgemma-prisma-review/analysis/combined_search_results.csv")
ARQUIVO_SAIDA = Path("/home/thcaballicare/medgemma-prisma-review/screening/identified.csv")

# Prefixos de base de dados esperados no nome do arquivo de origem
BASES_CONHECIDAS = ("arxiv", "pubmed", "semanticscholar", "crossref_acm")


def extrair_base_topico(nome_arquivo: str) -> tuple[str, str]:
    """Extrai o nome da base e o tópico de busca a partir do nome do arquivo.
    Ex.: 'pubmed_2_IA_Radiologia.csv' -> ('pubmed', 'IA_Radiologia')
    """
    padrao = r'^(' + '|'.join(BASES_CONHECIDAS) + r')_\d+_(.+)\.csv$'
    m = re.match(padrao, nome_arquivo)
    if m:
        return m.group(1), m.group(2)
    return "desconhecido", nome_arquivo


def extrair_ano(row: pd.Series):
    """Extrai o ano de publicação, tentando várias colunas possíveis."""
    if pd.notna(row.get("Ano")):
        try:
            return int(row["Ano"])
        except (ValueError, TypeError):
            pass
    for col in ("Data_Publicacao", "data_publicacao"):
        val = row.get(col)
        if pd.notna(val):
            match = re.search(r"(19|20)\d{2}", str(val))
            if match:
                return int(match.group(0))
    return pd.NA


def primeiro_nao_nulo(row: pd.Series, *colunas):
    """Retorna o primeiro valor não nulo entre as colunas informadas."""
    for col in colunas:
        val = row.get(col)
        if pd.notna(val):
            return val
    return pd.NA


def padronizar(df: pd.DataFrame) -> pd.DataFrame:
    registros = []
    for _, row in df.iterrows():
        base, topico = extrair_base_topico(row["arquivo_origem"])
        registros.append({
            "title": primeiro_nao_nulo(row, "Titulo", "titulo"),
            "authors": primeiro_nao_nulo(row, "Autores", "autores"),
            "abstract": primeiro_nao_nulo(row, "Resumo", "resumo"),
            "year": extrair_ano(row),
            "doi": primeiro_nao_nulo(row, "DOI", "doi"),
            "pmid": row.get("PMID"),
            "venue": primeiro_nao_nulo(row, "Publicacao", "Periodico", "Veiculo", "journal_ref"),
            "url": primeiro_nao_nulo(row, "URL", "pdf_url"),
            "publication_type": primeiro_nao_nulo(row, "Tipo", "Tipo_Publicacao"),
            "source_database": base,
            "search_topic": topico,
            "source_file": row["arquivo_origem"],
        })

    identified = pd.DataFrame(registros)
    identified.insert(0, "record_id", [f"REC{i + 1:05d}" for i in range(len(identified))])
    return identified


def main():
    if not ARQUIVO_ENTRADA.exists():
        print(f"Arquivo não encontrado: {ARQUIVO_ENTRADA}")
        return

    df = pd.read_csv(ARQUIVO_ENTRADA, low_memory=False)
    identified = padronizar(df)

    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    identified.to_csv(ARQUIVO_SAIDA, index=False)

    print(f"Arquivo salvo em: {ARQUIVO_SAIDA}")
    print(f"\nTotal de registros identificados: {len(identified)}")
    print("\n--- Registros por base de dados (para o diagrama PRISMA) ---")
    print(identified["source_database"].value_counts().to_string())
    print(f"\nTítulos ausentes: {identified['title'].isna().sum()}")
    print(f"DOIs ausentes: {identified['doi'].isna().sum()}")
    print(f"Anos ausentes: {identified['year'].isna().sum()}")


if __name__ == "__main__":
    main()
