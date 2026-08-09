#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crossref_acm_search_export.py

COMPLEMENTO (não substituto) à busca real na ACM Digital Library
--------------------------------------------------------------------
Sem ACM Digital Library Premium/institucional, não dá pra exportar
resultados de busca em massa (dl.acm.org exige assinatura para isso).
Este script usa a API pública e gratuita do Crossref -- sem chave, sem
cadastro -- filtrando por trabalhos com DOI da ACM (prefixo 10.1145,
"prefixo" = identifica o editor que registrou o DOI) para aproximar as 9
buscas.

LEIA ISTO ANTES DE USAR OS RESULTADOS
------------------------------------------
O Crossref NÃO tem busca booleana real (sem AND/OR/frase exata garantida
-- é uma busca por relevância). Isso significa que os resultados daqui
NÃO são equivalentes aos que a busca nativa da ACM DL traria. Para
aproximar o comportamento AND/OR das suas strings originais, o script
expande cada busca em todas as combinações possíveis de um termo de cada
grupo (produto cartesiano) e roda uma consulta separada para cada
combinação, juntando e deduplicando tudo no final. Ainda assim:
  - Cobertura de resumo (abstract) no Crossref é parcial -- nem toda
    editora deposita o resumo completo, então alguns registros virão sem
    "Resumo" preenchido.
  - Isso cobre só trabalhos com DOI registrado pela ACM (praticamente
    tudo que está na ACM DL, mas pode haver exceções raras).
Trate este CSV como uma fonte SUPLEMENTAR/de checagem cruzada, e deixe
isso explícito na sua documentação de metodologia (PRISMA) -- ele não
substitui uma exportação real da ACM DL feita com acesso Premium/
institucional (veja acm_bibtex_to_csv.py para esse fluxo, incluindo o
caminho gratuito de exportar artigo por artigo).

Requisitos
----------
    pip install requests

Uso
---
    python crossref_acm_search_export.py

Saída
-----
    crossref_acm_1_VLMs.csv
    crossref_acm_2_EdgeAI.csv
    crossref_acm_3_Jetson.csv
    crossref_acm_4_Quantizacao.csv
    crossref_acm_5_Inferencia.csv
    crossref_acm_6_Datasets.csv
    crossref_acm_7_Eficiencia.csv
    crossref_acm_8_ArquiteturaLocal.csv
    crossref_acm_9_Infraestrutura.csv
"""

import csv
import itertools
import re
import time

import requests

# ----------------------------------------------------------------------
# CONFIGURAÇÕES
# ----------------------------------------------------------------------
CONTACT_EMAIL = "seu_email@exemplo.com"  # <<< recomendado: entra no "polite pool" (rate limit maior)

CROSSREF_BASE_URL = "https://api.crossref.org/works"
ACM_PREFIX = "10.1145"     # prefixo de DOI da ACM
MIN_YEAR = 2023

ROWS_PER_CALL = 100
MAX_PAGES_PER_SUBQUERY = 3   # limite de segurança: até 300 registros por combinação de termos
SLEEP_BETWEEN_CALLS = 0.5    # com mailto no polite pool, esse ritmo é tranquilo

# ----------------------------------------------------------------------
# STRINGS DE BUSCA
# Cada busca é uma lista de "grupos" (cada grupo = uma lista de termos
# que seriam unidos por OR). O script gera o produto cartesiano entre os
# grupos para aproximar o AND entre eles.
# ----------------------------------------------------------------------
SEARCHES = {
    "1_VLMs": [
        ['"vision-language model"', '"vision language models"', '"multimodal large language model"',
         '"medical vision-language model"', 'MedGemma', '"LLaVA-Med"', 'CheXagent', 'RadFM',
         'XrayGPT', 'BiomedGPT'],
        ['radiology', '"medical imaging"', '"diagnostic imaging"', '"chest X-ray"',
         '"chest radiograph"', 'CXR', 'pneumonia'],
    ],
    "2_EdgeAI": [
        ['"edge AI"', '"edge computing"', 'embedded', '"embedded AI"', '"local inference"',
         'offline', '"on-device AI"'],
        ['radiology', '"medical imaging"', '"medical image analysis"'],
    ],
    "3_Jetson": [
        ['"NVIDIA Jetson"', 'Jetson', '"Jetson Orin"', '"Jetson Nano"'],
        ['AI', '"deep learning"', 'radiology', '"medical imaging"'],
    ],
    "4_Quantizacao": [
        ['quantization', 'quantisation', 'GGUF', 'GGML', 'INT4', 'INT8', 'FP8', 'QLoRA', 'LoRA'],
        ['MedGemma', 'Gemma', 'multimodal', '"vision-language model"'],
    ],
    "5_Inferencia": [
        ['llama.cpp', 'GGUF', 'GGML'],
        ['MedGemma', 'Gemma', 'multimodal', '"vision-language model"'],
    ],
    "6_Datasets": [
        ['MedGemma', '"LLaVA-Med"', 'CheXagent', 'RadFM'],
        ['BRAX', '"MIMIC-CXR"', 'CheXpert', 'PadChest', 'VinDr-CXR'],
    ],
    "7_Eficiencia": [
        ['"vision-language model"', 'MedGemma', 'Gemma'],
        ['latency', 'throughput', 'memory', 'inference', 'efficiency', 'benchmark'],
    ],
    "8_ArquiteturaLocal": [
        ['"vision-language model"', '"multimodal large language model"', 'MedGemma',
         '"LLaVA-Med"', 'CheXagent', 'RadFM'],
        ['radiology', '"medical imaging"', '"chest X-ray"', 'pneumonia'],
        ['"edge computing"', 'embedded', '"local inference"', '"NVIDIA Jetson"', 'Jetson',
         'llama.cpp', 'GGUF', 'quantization'],
    ],
    "9_Infraestrutura": [
        ['llama.cpp', 'GGUF', '"large language model"', '"multimodal model"'],
        ['"edge computing"', 'embedded', '"NVIDIA Jetson"', 'Jetson', 'quantization', 'inference'],
    ],
}

# ----------------------------------------------------------------------
# FUNÇÕES
# ----------------------------------------------------------------------

TAG_RE = re.compile(r"<[^>]+>")


def strip_jats(texto):
    """Remove marcação JATS/XML que às vezes vem no campo abstract do Crossref."""
    if not texto:
        return ""
    limpo = TAG_RE.sub(" ", texto)
    return " ".join(limpo.split())


def crossref_search(query, offset=0, rows=ROWS_PER_CALL):
    params = {
        "query": query,
        "filter": f"prefix:{ACM_PREFIX},from-pub-date:{MIN_YEAR}-01-01",
        "rows": rows,
        "offset": offset,
    }
    headers = {"User-Agent": f"prisma-review-script/1.0 (mailto:{CONTACT_EMAIL})"}
    for attempt in range(3):
        try:
            resp = requests.get(CROSSREF_BASE_URL, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as exc:
            print(f"      Aviso: erro na chamada (tentativa {attempt + 1}/3): {exc}")
            time.sleep(3)
    raise RuntimeError("Não foi possível completar a chamada à API do Crossref após 3 tentativas.")


def fetch_subquery(combo_terms):
    query = " ".join(combo_terms)
    registros = []
    offset = 0
    total = None
    for _ in range(MAX_PAGES_PER_SUBQUERY):
        data = crossref_search(query, offset=offset)
        msg = data.get("message", {})
        if total is None:
            total = msg.get("total-results", 0)
        itens = msg.get("items", [])
        if not itens:
            break
        registros.extend(itens)
        offset += ROWS_PER_CALL
        if offset >= total:
            break
        time.sleep(SLEEP_BETWEEN_CALLS)

    if total and total > MAX_PAGES_PER_SUBQUERY * ROWS_PER_CALL:
        print(f"      Aviso: '{query}' tem {total} resultados no Crossref; baixados só os {len(registros)} primeiros.")

    return registros


def item_to_row(item):
    autores_raw = item.get("author", []) or []
    nomes = "; ".join(
        " ".join(filter(None, [a.get("given"), a.get("family")]))
        for a in autores_raw if isinstance(a, dict)
    )
    titulo = " ".join(item.get("title", []) or [])
    container = " ".join(item.get("container-title", []) or [])

    data_info = item.get("published") or item.get("published-print") or item.get("published-online") or {}
    date_parts = data_info.get("date-parts", [[None]])
    ano = date_parts[0][0] if date_parts and date_parts[0] and date_parts[0][0] else ""

    return {
        "DOI": item.get("DOI", ""),
        "Titulo": titulo,
        "Autores": nomes,
        "Ano": ano,
        "Publicacao": container,
        "Tipo": item.get("type", ""),
        "URL": item.get("URL", ""),
        "Resumo": strip_jats(item.get("abstract", "")),
    }


def dedupe_by_doi(rows):
    vistos = set()
    saida = []
    for r in rows:
        doi = (r.get("DOI") or "").lower()
        if doi and doi in vistos:
            continue
        if doi:
            vistos.add(doi)
        saida.append(r)
    return saida


def save_csv(rows, filename):
    fieldnames = ["DOI", "Titulo", "Autores", "Ano", "Publicacao", "Tipo", "URL", "Resumo"]
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ----------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ----------------------------------------------------------------------

def main():
    if CONTACT_EMAIL == "seu_email@exemplo.com":
        print("Aviso: preencha CONTACT_EMAIL com seu e-mail para entrar no 'polite pool' do Crossref (rate limit maior). Continuando mesmo assim...\n")

    for nome, grupos in SEARCHES.items():
        print(f"\n=== Busca: {nome} ===")
        combinacoes = list(itertools.product(*grupos))
        print(f"  {len(combinacoes)} combinação(ões) de termos a consultar no Crossref...")

        todos = []
        for i, combo in enumerate(combinacoes, 1):
            query_legivel = " ".join(combo)
            registros = fetch_subquery(combo)
            print(f"    [{i}/{len(combinacoes)}] {query_legivel} -> {len(registros)} registros")
            todos.extend(registros)
            time.sleep(SLEEP_BETWEEN_CALLS)

        linhas = [item_to_row(it) for it in todos]
        linhas = dedupe_by_doi(linhas)

        filename = f"crossref_acm_{nome}.csv"
        save_csv(linhas, filename)
        print(f"Arquivo salvo: {filename} ({len(linhas)} registros únicos)")

    print("\nConcluído! Lembre-se: trate estes CSVs como fonte suplementar, não como equivalente à busca nativa da ACM DL.")


if __name__ == "__main__":
    main()
