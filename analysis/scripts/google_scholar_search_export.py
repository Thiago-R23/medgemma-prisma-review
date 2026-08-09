#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
semantic_scholar_search_export.py

IMPORTANTE -- leia antes de usar
-----------------------------------
O Google Scholar NÃO tem API pública, e fazer scraping automatizado dele
viola os Termos de Serviço do Google (e o Google ativamente bloqueia/usa
CAPTCHA contra esse tipo de acesso). Por isso este script NÃO busca no
Google Scholar -- ele usa o Semantic Scholar, uma base acadêmica gratuita
e de acesso aberto (Allen Institute for AI) com cobertura ampla e
sobreposta à do Google Scholar, e que tem uma API oficial, gratuita e sem
necessidade de chave.

Isso é uma SUBSTITUIÇÃO, não uma cópia do Google Scholar -- os resultados
não serão idênticos. Veja a mensagem que te mandei no chat para outras
opções (busca manual no Scholar, o que é aliás prática padrão e bem
documentada em revisões PRISMA justamente pela falta de API/exportação
em massa do Scholar).

Requisitos
----------
    pip install requests

Não é preciso se cadastrar nem gerar chave. Se quiser um limite de taxa
maior, dá pra gerar uma chave gratuita em
https://www.semanticscholar.org/product/api e preencher API_KEY abaixo
(opcional).

Como as strings foram adaptadas
-----------------------------------
A busca "bulk" do Semantic Scholar pesquisa título + resumo e é, por
padrão, uma busca "e" (AND) entre os termos/frases da mesma linha -- ou
seja, bem parecido com o comportamento do Google Scholar. Frases entre
aspas continuam funcionando como busca exata. Por isso as linhas que você
escreveu praticamente não precisaram de tradução, foram só agrupadas por
busca numerada (cada linha roda como uma sub-busca separada, e os
resultados são somados e deduplicados por paperId).

Filtro de data
--------------
Todas as buscas usam year=MIN_YEAR- (a partir de MIN_YEAR, padrão 2023),
para manter consistência com as outras bases.

Uso
---
    python semantic_scholar_search_export.py

Saída
-----
    semanticscholar_1_VLMs.csv
    semanticscholar_2_ModelosMedicos.csv
    semanticscholar_4_RadiografiaTorax.csv
    semanticscholar_5_Jetson.csv
    semanticscholar_6_Quantizacao.csv
    semanticscholar_7_Llama.csv
    semanticscholar_8_Datasets.csv
    semanticscholar_9_Eficiencia.csv
    semanticscholar_10_Integradora.csv
(numeração preservada igual à do seu documento original, que pula o "3")
"""

import csv
import time
import requests

# ----------------------------------------------------------------------
# CONFIGURAÇÕES
# ----------------------------------------------------------------------
API_KEY = ""   # opcional -- deixe em branco para usar sem chave (mais lento)
BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
MIN_YEAR = 2023

FIELDS = "title,authors,year,venue,abstract,externalIds,url,publicationDate"
SLEEP_BETWEEN_CALLS = 3.0   # conservador: fica bem abaixo do limite sem chave

# ----------------------------------------------------------------------
# STRINGS DE BUSCA (cada item da lista = uma sub-busca independente)
# ----------------------------------------------------------------------
SEARCHES = {
    "1_VLMs": [
        '"vision-language model" radiology',
        'multimodal radiology',
    ],
    "2_ModelosMedicos": [
        'MedGemma radiology',
        'CheXagent radiology',
        '"LLaVA-Med"',
    ],
    "4_RadiografiaTorax": [
        '"chest X-ray" multimodal AI',
        'CXR multimodal',
    ],
    "5_Jetson": [
        '"NVIDIA Jetson" radiology',
        '"NVIDIA Jetson" "medical imaging"',
        'Jetson AI healthcare',
    ],
    "6_Quantizacao": [
        'quantization multimodal model',
        'GGUF MedGemma',
        'GGML multimodal',
        'QLoRA MedGemma',
    ],
    "7_Llama": [
        'llama.cpp MedGemma',
        'llama.cpp multimodal',
        'llama.cpp radiology',
    ],
    "8_Datasets": [
        'MIMIC-CXR multimodal',
        'CheXpert multimodal',
        'BRAX radiology AI',
    ],
    "9_Eficiencia": [
        'multimodal latency inference',
        'vision-language model benchmark',
        'medical multimodal benchmark',
    ],
    "10_Integradora": [
        'MedGemma radiology Jetson',
        'multimodal radiology edge computing',
        '"vision-language model" "medical imaging" Jetson',
    ],
}

# ----------------------------------------------------------------------
# FUNÇÕES
# ----------------------------------------------------------------------


def s2_search(query, token=None):
    """Faz uma chamada à busca bulk do Semantic Scholar e retorna o JSON."""
    params = {
        "query": query,
        "fields": FIELDS,
        "year": f"{MIN_YEAR}-",
    }
    if token:
        params["token"] = token
    headers = {"x-api-key": API_KEY} if API_KEY else {}

    for attempt in range(3):
        try:
            resp = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
            if resp.status_code == 429:
                print("    Aviso: limite de taxa atingido (429). Aguardando 15s...")
                time.sleep(15)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as exc:
            print(f"    Aviso: erro na chamada (tentativa {attempt + 1}/3): {exc}")
            time.sleep(5)
    raise RuntimeError("Não foi possível completar a chamada à API do Semantic Scholar após 3 tentativas.")


def fetch_subquery(raw_query):
    print(f"  Sub-busca: {raw_query}")
    registros = []
    token = None
    total = None

    while True:
        data = s2_search(raw_query, token=token)
        if total is None:
            total = data.get("total", 0)
            print(f"    Total encontrado: {total}")
            if total == 0:
                break

        pagina = data.get("data", []) or []
        registros.extend(pagina)
        print(f"    ... {len(registros)}/{total} registros baixados")

        token = data.get("token")
        if not token or not pagina:
            break
        time.sleep(SLEEP_BETWEEN_CALLS)

    return registros


def dedupe_by_id(registros):
    vistos = set()
    saida = []
    for r in registros:
        pid = r.get("paperId", "")
        if pid and pid in vistos:
            continue
        if pid:
            vistos.add(pid)
        saida.append(r)
    return saida


def join_authors(paper):
    autores = paper.get("authors") or []
    return "; ".join(a.get("name", "") for a in autores if isinstance(a, dict) and a.get("name"))


def paper_to_row(paper):
    external_ids = paper.get("externalIds") or {}
    return {
        "PaperId": paper.get("paperId", ""),
        "Titulo": paper.get("title", "") or "",
        "Autores": join_authors(paper),
        "Ano": paper.get("year", ""),
        "Data_Publicacao": paper.get("publicationDate", ""),
        "Veiculo": paper.get("venue", "") or "",
        "DOI": external_ids.get("DOI", ""),
        "ArXiv_ID": external_ids.get("ArXiv", ""),
        "Resumo": paper.get("abstract", "") or "",
        "URL": paper.get("url", "") or "",
    }


def save_csv(rows, filename):
    fieldnames = [
        "PaperId", "Titulo", "Autores", "Ano", "Data_Publicacao",
        "Veiculo", "DOI", "ArXiv_ID", "Resumo", "URL",
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
            todos.extend(fetch_subquery(sub))
            time.sleep(SLEEP_BETWEEN_CALLS)

        todos = dedupe_by_id(todos)
        linhas = [paper_to_row(p) for p in todos]
        filename = f"semanticscholar_{nome}.csv"
        save_csv(linhas, filename)
        print(f"Arquivo salvo: {filename} ({len(linhas)} registros únicos)")

    print("\nConcluído!")


if __name__ == "__main__":
    main()
