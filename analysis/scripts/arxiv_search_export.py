#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arxiv_search_export.py

Executa as 6 buscas no arXiv (API oficial, gratuita, sem necessidade de
chave) e exporta o resultado completo de cada uma para um CSV separado.

Requisitos
----------
    pip install requests

Não é preciso se cadastrar nem gerar chave -- a API do arXiv
(export.arxiv.org/api/query) é totalmente aberta.

Como as strings de busca foram convertidas
--------------------------------------------
A API do arXiv exige que cada termo pesquisado tenha um prefixo de campo
(ex.: `all:`, `ti:`, `abs:`) e usa os operadores AND / OR / ANDNOT (não
"NOT" sozinho). Como você escreveu as buscas em formato "simples" (sem
prefixo de campo, algumas com AND/OR explícitos e outras não), o script
converte cada linha automaticamente:
  - Cada termo ou "frase entre aspas" recebe o prefixo all: (busca em
    título + resumo + autores + comentários + categoria, tudo ao mesmo
    tempo -- é o que mais se aproxima de uma busca "livre").
  - Quando não há operador explícito entre dois termos na mesma linha
    (ex.: "edge radiology"), o script insere um AND implícito entre eles.
  - Quando a linha já tem AND/OR/parênteses explícitos (buscas 5 e 6),
    a estrutura é preservada, só adicionando o prefixo all: em cada termo.
Você pode conferir a query final de cada busca no log impresso ao rodar.

Buscas com várias linhas (ex.: busca 1, que tem duas linhas)
---------------------------------------------------------------
Cada linha é executada como uma sub-busca independente (é assim que o
arXiv também é normalmente pesquisado manualmente, uma linha de cada
vez). Os resultados de todas as sub-buscas de um mesmo grupo são somados
e deduplicados por ID do arXiv antes de salvar o CSV daquele grupo.

Filtro de data
--------------
Todas as buscas incluem automaticamente submittedDate a partir de
MIN_YEAR (padrão: 2023) até hoje, para manter consistência com o filtro
usado nas buscas do PubMed e do IEEE Xplore.

Uso
---
    python arxiv_search_export.py

Saída
-----
    arxiv_1_VLMs.csv
    arxiv_2_MedGemma.csv
    arxiv_3_Edge.csv
    arxiv_4_Hardware.csv
    arxiv_5_Quantizacao.csv
    arxiv_6_MotorInferencia.csv
"""

import csv
import re
import time
import xml.etree.ElementTree as ET

import requests

# ----------------------------------------------------------------------
# CONFIGURAÇÕES
# ----------------------------------------------------------------------
ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
MIN_YEAR = 2023

MAX_RECORDS_PER_CALL = 200   # a API aceita até 2000, mas fatias menores são mais rápidas/gentis
SLEEP_BETWEEN_CALLS = 3.0    # o arXiv pede explicitamente um intervalo de 3s entre chamadas

MIN_DATE_ARXIV = f"{MIN_YEAR}01010000"   # AAAAMMDDHHHH (GMT)
MAX_DATE_ARXIV = "209912312359"          # data bem no futuro = "sem limite superior / até hoje"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}

# ----------------------------------------------------------------------
# STRINGS DE BUSCA (cada item da lista = uma sub-busca independente)
# ----------------------------------------------------------------------
SEARCHES = {
    "1_VLMs": [
        '"vision-language model" radiology',
        '"medical imaging" multimodal',
    ],
    "2_MedGemma": [
        'MedGemma',
    ],
    "3_Edge": [
        'edge radiology',
    ],
    "4_Hardware": [
        'NVIDIA Jetson Nano',
    ],
    "5_Quantizacao": [
        '(quantization OR GGUF OR GGML OR INT4 OR INT8 OR QLoRA) AND (MedGemma OR Gemma OR multimodal)',
    ],
    "6_MotorInferencia": [
        'llama.cpp OR GGUF',
    ],
}

# ----------------------------------------------------------------------
# CONVERSOR: busca "simples" -> sintaxe search_query do arXiv
# ----------------------------------------------------------------------
FIELD_PREFIXES = {"ti", "au", "abs", "co", "jr", "cat", "rn", "id", "all"}
TOKEN_RE = re.compile(r'"[^"]+"|\(|\)|[^\s()]+')


def to_arxiv_query(raw):
    """Converte uma linha de busca simples (com ou sem AND/OR/parênteses
    explícitos) para a sintaxe search_query da API do arXiv, prefixando
    cada termo com all: e inserindo AND implícito entre termos consecutivos
    que não tenham operador entre eles."""
    tokens = TOKEN_RE.findall(raw)
    out = []
    prev_was_term = False
    for tok in tokens:
        if tok == "(":
            out.append(tok)
            prev_was_term = False
            continue
        if tok == ")":
            out.append(tok)
            prev_was_term = True
            continue
        upper = tok.upper()
        if upper == "NOT":
            out.append("ANDNOT")
            prev_was_term = False
            continue
        if upper in ("AND", "OR", "ANDNOT"):
            out.append(upper)
            prev_was_term = False
            continue
        if prev_was_term:
            out.append("AND")
        if ":" in tok and tok.split(":", 1)[0].lower() in FIELD_PREFIXES:
            out.append(tok)
        else:
            out.append(f"all:{tok}")
        prev_was_term = True
    return " ".join(out)


# ----------------------------------------------------------------------
# FUNÇÕES DE BUSCA
# ----------------------------------------------------------------------

def arxiv_search(query, start=0, max_results=MAX_RECORDS_PER_CALL):
    """Faz uma chamada à API do arXiv e retorna a árvore XML (Atom) já parseada."""
    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    for attempt in range(3):
        try:
            resp = requests.get(ARXIV_BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            return ET.fromstring(resp.content)
        except requests.exceptions.RequestException as exc:
            print(f"    Aviso: erro na chamada (tentativa {attempt + 1}/3): {exc}")
            time.sleep(5)
        except ET.ParseError as exc:
            print(f"    Aviso: resposta XML inválida (tentativa {attempt + 1}/3): {exc}")
            time.sleep(5)
    raise RuntimeError("Não foi possível completar a chamada à API do arXiv após 3 tentativas.")


def parse_entries(root):
    """Extrai os artigos (<entry>) de uma árvore Atom já parseada."""
    entradas = []
    for entry in root.findall("atom:entry", NS):
        id_el = entry.find("atom:id", NS)
        if id_el is None or not id_el.text:
            continue
        arxiv_id = id_el.text.strip()
        if "arxiv.org/abs/" not in arxiv_id:
            continue  # provavelmente uma entrada de erro da API

        title = (entry.findtext("atom:title", default="", namespaces=NS) or "").strip()
        title = " ".join(title.split())
        summary = (entry.findtext("atom:summary", default="", namespaces=NS) or "").strip()
        summary = " ".join(summary.split())
        published = entry.findtext("atom:published", default="", namespaces=NS) or ""
        updated = entry.findtext("atom:updated", default="", namespaces=NS) or ""

        autores = "; ".join(
            (a.findtext("atom:name", default="", namespaces=NS) or "").strip()
            for a in entry.findall("atom:author", NS)
        )
        categorias = "; ".join(c.get("term", "") for c in entry.findall("atom:category", NS))
        cat_principal_el = entry.find("arxiv:primary_category", NS)
        cat_principal = cat_principal_el.get("term", "") if cat_principal_el is not None else ""

        doi = entry.findtext("arxiv:doi", default="", namespaces=NS) or ""
        journal_ref = entry.findtext("arxiv:journal_ref", default="", namespaces=NS) or ""
        comentario = entry.findtext("arxiv:comment", default="", namespaces=NS) or ""

        pdf_url = ""
        for link in entry.findall("atom:link", NS):
            if link.get("title") == "pdf":
                pdf_url = link.get("href", "")

        entradas.append({
            "arxiv_id": arxiv_id,
            "titulo": title,
            "autores": autores,
            "categoria_principal": cat_principal,
            "categorias": categorias,
            "data_publicacao": published,
            "data_atualizacao": updated,
            "doi": doi,
            "journal_ref": journal_ref,
            "comentario": comentario,
            "resumo": summary,
            "pdf_url": pdf_url,
        })
    return entradas


def fetch_arxiv_subquery(raw_query):
    """Executa uma sub-busca (uma linha) já paginando até trazer tudo."""
    query = to_arxiv_query(raw_query)
    full_query = f"({query}) AND submittedDate:[{MIN_DATE_ARXIV} TO {MAX_DATE_ARXIV}]"
    print(f"  Sub-busca: {raw_query}")
    print(f"    search_query: {full_query}")

    registros = []
    start = 0
    total = None
    while True:
        root = arxiv_search(full_query, start=start, max_results=MAX_RECORDS_PER_CALL)
        if total is None:
            total_txt = root.findtext("opensearch:totalResults", default="0", namespaces=NS)
            total = int(total_txt) if total_txt and total_txt.strip().isdigit() else 0
            print(f"    Total encontrado: {total}")
            if total > 1000:
                print("    Aviso: mais de 1000 resultados; considere refinar esta sub-busca.")
            if total == 0:
                break
        entradas = parse_entries(root)
        if not entradas:
            break
        registros.extend(entradas)
        print(f"    ... {min(len(registros), total)}/{total} registros baixados")
        start += MAX_RECORDS_PER_CALL
        time.sleep(SLEEP_BETWEEN_CALLS)
        if start >= total:
            break

    return registros


def dedupe_by_id(registros):
    """Remove duplicatas (mesmo artigo em versões/sub-buscas diferentes),
    ignorando o sufixo de versão (vN) do ID do arXiv."""
    vistos = set()
    saida = []
    for r in registros:
        base_id = re.sub(r"v\d+$", "", r["arxiv_id"])
        if base_id in vistos:
            continue
        vistos.add(base_id)
        saida.append(r)
    return saida


def save_csv(rows, filename):
    fieldnames = [
        "arxiv_id", "titulo", "autores", "categoria_principal", "categorias",
        "data_publicacao", "data_atualizacao", "doi", "journal_ref",
        "comentario", "resumo", "pdf_url",
    ]
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ----------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ----------------------------------------------------------------------

def main():
    for nome, subqueries in SEARCHES.items():
        print(f"\n=== Busca: {nome} ===")
        todos = []
        for sub in subqueries:
            todos.extend(fetch_arxiv_subquery(sub))

        todos = dedupe_by_id(todos)
        filename = f"arxiv_{nome}.csv"
        save_csv(todos, filename)
        print(f"Arquivo salvo: {filename} ({len(todos)} registros únicos)")

    print("\nConcluído!")


if __name__ == "__main__":
    main()
