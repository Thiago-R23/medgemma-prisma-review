#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pubmed_search_export.py

Executa 3 buscas no PubMed (via API E-utilities do NCBI) e exporta o
resultado COMPLETO de cada uma para um arquivo CSV separado.

Requisitos
----------
    pip install biopython

Antes de executar
------------------
1. Preencha ENTREZ_EMAIL com um e-mail válido (exigência do NCBI para
   identificar quem está fazendo as requisições).
2. (Opcional, mas recomendado) Gere uma API Key gratuita em
   https://www.ncbi.nlm.nih.gov/account/settings/  e preencha
   ENTREZ_API_KEY. Isso aumenta o limite de 3 para 10 requisições/segundo,
   o que acelera bastante buscas com muitos resultados.

Filtro de data
--------------
Todas as 3 buscas incluem automaticamente um filtro de data de publicação
a partir de MIN_YEAR (definido mais abaixo, padrão: 2023) até hoje.
Para mudar o ano inicial, basta editar a constante MIN_YEAR.

Limite de 10.000 registros por busca (NCBI)
--------------------------------------------
O PubMed/NCBI não permite paginar (retstart) além de ~10.000 registros
dentro de uma mesma busca, mesmo usando API key — isso é uma limitação da
própria API, não do script. Para contornar isso, o script verifica o total
de resultados de cada busca e, se ultrapassar MAX_RECORDS_PER_SEARCH,
divide automaticamente o período em sub-intervalos de data cada vez
menores (busca binária por data) até que cada sub-intervalo fique abaixo
do limite. No fim, os resultados de todos os sub-intervalos são
combinados em um único CSV por busca.

Uso
---
    python pubmed_search_export.py

Saída
-----
    pubmed_1_IA_Multimodal.csv
    pubmed_2_IA_Radiologia.csv
    pubmed_3_MedGemma.csv
"""

import csv
import time
from datetime import date, timedelta
from Bio import Entrez, Medline

# ----------------------------------------------------------------------
# CONFIGURAÇÕES — AJUSTE AQUI
# ----------------------------------------------------------------------
ENTREZ_EMAIL = "thiagorc2312@gmail.com"   # <<< OBRIGATÓRIO: troque pelo seu e-mail
ENTREZ_API_KEY = None                     # <<< opcional: "sua_api_key_aqui"

BATCH_SIZE = 200            # nº de registros buscados por requisição (efetch)
SLEEP_BETWEEN_CALLS = 0.34  # ~3 req/s (limite sem api_key)

Entrez.email = ENTREZ_EMAIL
if ENTREZ_API_KEY:
    Entrez.api_key = ENTREZ_API_KEY
    SLEEP_BETWEEN_CALLS = 0.11  # ~10 req/s (limite com api_key)

# ----------------------------------------------------------------------
# FILTRO DE DATA (aplicado a todas as buscas)
# ----------------------------------------------------------------------
MIN_YEAR = 2023  # inclui tudo publicado a partir de 01/01 deste ano até hoje
MIN_DATE = f"{MIN_YEAR}/01/01"
MAX_DATE = date.today().strftime("%Y/%m/%d")

# Limite prático de registros por busca imposto pelo PubMed/NCBI (retstart
# não pode passar de ~10.000). Deixamos uma margem de segurança abaixo disso.
MAX_RECORDS_PER_SEARCH = 9500

# ----------------------------------------------------------------------
# STRINGS DE BUSCA (bases, sem o filtro de data — a data é aplicada à parte)
# ----------------------------------------------------------------------
BASE_SEARCHES = {
    "1_IA_Multimodal": (
        '(multimodal[Title/Abstract] OR "foundation model*"[Title/Abstract] '
        'OR "large language model*"[Title/Abstract] OR "generative AI"[Title/Abstract]) '
        'AND '
        '(radiology[Title/Abstract] OR "medical imaging"[Title/Abstract] '
        'OR "diagnostic imaging"[Title/Abstract] OR "chest radiograph*"[Title/Abstract] '
        'OR "chest x-ray*"[Title/Abstract] OR CXR[Title/Abstract])'
    ),
    "2_IA_Radiologia": (
        '("artificial intelligence"[MeSH Terms] OR "deep learning"[Title/Abstract] '
        'OR "large language model"[Title/Abstract]) '
        'AND '
        '(radiology[MeSH Terms] OR "diagnostic imaging"[MeSH Terms])'
    ),
    "3_MedGemma": 'MedGemma',
}

# ----------------------------------------------------------------------
# FUNÇÕES
# ----------------------------------------------------------------------

def search_pubmed(query, mindate=None, maxdate=None):
    """Executa o ESearch com histórico no servidor e retorna metadados.
    Se mindate/maxdate forem informados, filtra por data de publicação."""
    kwargs = dict(db="pubmed", term=query, retmax=0, usehistory="y")
    if mindate and maxdate:
        kwargs.update(mindate=mindate, maxdate=maxdate, datetype="pdat")
    handle = Entrez.esearch(**kwargs)
    record = Entrez.read(handle)
    handle.close()
    return {
        "count": int(record["Count"]),
        "webenv": record["WebEnv"],
        "query_key": record["QueryKey"],
    }


def get_date_windows(query, mindate, maxdate):
    """Divide recursivamente o intervalo [mindate, maxdate] em sub-janelas
    até que cada uma tenha no máximo MAX_RECORDS_PER_SEARCH resultados,
    contornando o limite de ~10.000 registros por busca do PubMed."""
    meta = search_pubmed(query, mindate=mindate, maxdate=maxdate)
    count = meta["count"]
    time.sleep(SLEEP_BETWEEN_CALLS)

    if count == 0:
        return []

    if count <= MAX_RECORDS_PER_SEARCH or mindate == maxdate:
        if count > MAX_RECORDS_PER_SEARCH:
            print(
                f"  Aviso: {mindate} sozinho já tem {count} registros "
                f"(acima do limite). Só os {MAX_RECORDS_PER_SEARCH} primeiros "
                f"dessa data serão baixados."
            )
        return [{"mindate": mindate, "maxdate": maxdate, **meta}]

    d1 = date(*(int(x) for x in mindate.split("/")))
    d2 = date(*(int(x) for x in maxdate.split("/")))
    meio = d1 + (d2 - d1) // 2
    meio_str = meio.strftime("%Y/%m/%d")
    proximo_str = (meio + timedelta(days=1)).strftime("%Y/%m/%d")

    print(f"  {mindate} a {maxdate}: {count} registros (> {MAX_RECORDS_PER_SEARCH}); dividindo por data...")
    esquerda = get_date_windows(query, mindate, meio_str)
    direita = get_date_windows(query, proximo_str, maxdate)
    return esquerda + direita


def fetch_records(webenv, query_key, count):
    """Baixa todos os registros em lotes (formato MEDLINE) usando o
    histórico criado pelo ESearch, com retentativas em caso de falha."""
    records = []
    for start in range(0, count, BATCH_SIZE):
        for attempt in range(3):
            try:
                handle = Entrez.efetch(
                    db="pubmed",
                    rettype="medline",
                    retmode="text",
                    retstart=start,
                    retmax=BATCH_SIZE,
                    webenv=webenv,
                    query_key=query_key,
                )
                batch = list(Medline.parse(handle))
                handle.close()
                records.extend(batch)
                print(f"  ... {min(start + BATCH_SIZE, count)}/{count} registros baixados")
                break
            except Exception as exc:
                print(f"  Aviso: erro no lote {start} (tentativa {attempt + 1}/3): {exc}")
                time.sleep(2)
        else:
            print(f"  ERRO: não foi possível baixar o lote a partir de {start}. Pulando.")
        time.sleep(SLEEP_BETWEEN_CALLS)
    return records


def extract_doi(aid_field):
    """Extrai o DOI da lista AID (Article ID), se existir."""
    if not aid_field:
        return ""
    for aid in aid_field:
        if aid.strip().endswith("[doi]"):
            return aid.replace("[doi]", "").strip()
    return ""


def medline_to_row(rec):
    """Converte um registro MEDLINE (dict) em uma linha de CSV."""
    pmid = rec.get("PMID", "")
    return {
        "PMID": pmid,
        "Titulo": rec.get("TI", ""),
        "Autores": "; ".join(rec.get("FAU", rec.get("AU", []))),
        "Periodico": rec.get("JT", rec.get("TA", "")),
        "Data_Publicacao": rec.get("DP", ""),
        "DOI": extract_doi(rec.get("AID", [])),
        "Tipo_Publicacao": "; ".join(rec.get("PT", [])),
        "MeSH_Terms": "; ".join(rec.get("MH", [])),
        "Resumo": rec.get("AB", ""),
        "URL": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
    }


def save_csv(rows, filename):
    fieldnames = [
        "PMID", "Titulo", "Autores", "Periodico", "Data_Publicacao",
        "DOI", "Tipo_Publicacao", "MeSH_Terms", "Resumo", "URL",
    ]
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ----------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ----------------------------------------------------------------------

def main():
    if ENTREZ_EMAIL == "seu_email@exemplo.com":
        print("!! Configure ENTREZ_EMAIL com um e-mail válido antes de rodar o script.")
        return

    for nome, query in BASE_SEARCHES.items():
        print(f"\n=== Busca: {nome} ===")
        print(f"Query base: {query}")
        print(f"Periodo: {MIN_DATE} a {MAX_DATE}")

        janelas = get_date_windows(query, MIN_DATE, MAX_DATE)
        total = sum(min(w["count"], MAX_RECORDS_PER_SEARCH) for w in janelas)
        print(f"Total de artigos encontrados: {total} (em {len(janelas)} sub-busca(s) por data)")

        if total == 0:
            print("Nenhum resultado. CSV não será gerado.")
            continue

        todos_registros = []
        for w in janelas:
            n = min(w["count"], MAX_RECORDS_PER_SEARCH)
            print(f"  Baixando {w['mindate']} a {w['maxdate']} ({n} registros)...")
            todos_registros.extend(fetch_records(w["webenv"], w["query_key"], n))

        # remove eventuais duplicatas (precaução; não deveria ocorrer com
        # janelas de data disjuntas, mas é uma rede de segurança barata)
        vistos = set()
        linhas = []
        for rec in todos_registros:
            pmid = rec.get("PMID", "")
            if pmid and pmid in vistos:
                continue
            if pmid:
                vistos.add(pmid)
            linhas.append(medline_to_row(rec))

        filename = f"pubmed_{nome}.csv"
        save_csv(linhas, filename)
        print(f"Arquivo salvo: {filename} ({len(linhas)} registros)")

    print("\nConcluído!")


if __name__ == "__main__":
    main()
