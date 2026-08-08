import requests
import csv
import time
from pathlib import Path

# ====================== SUA CHAVE ======================
API_KEY = "ve4ar5wtshqhmft5ewxngvmj"
# =======================================================

MAX_RESULTS = 150
RESULTS_PER_PAGE = 100
BASE_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

queries = {
    "01_Vision_Language_Models": (
        '("vision-language model" OR "vision language model" OR "multimodal large language model" '
        'OR "medical vision-language model" OR MedGemma OR "LLaVA-Med" OR CheXagent OR RadFM OR XrayGPT OR BiomedGPT) '
        'AND (radiology OR "medical imaging" OR "diagnostic imaging" OR "chest X-ray" OR "chest radiograph" OR CXR OR pneumonia)'
    ),
    "02_Edge_AI": (
        '("edge AI" OR "edge computing" OR embedded OR "embedded AI" OR "on-device AI" OR "local inference" OR offline) '
        'AND (radiology OR "medical imaging" OR "medical image analysis")'
    ),
    "03_Hardware_Jetson": (
        '("NVIDIA Jetson" OR Jetson OR "Jetson Orin" OR "Jetson Nano") '
        'AND (radiology OR "medical imaging" OR "deep learning" OR AI)'
    ),
    "04_Quantizacao": (
        '(quantization OR quantisation OR GGUF OR GGML OR INT4 OR INT8 OR FP8 OR QLoRA OR LoRA) '
        'AND ("vision-language model" OR multimodal OR MedGemma OR Gemma)'
    ),
    "05_Eficiencia": (
        '("vision-language model" OR MedGemma OR Gemma) '
        'AND (latency OR throughput OR memory OR inference OR efficiency OR benchmark)'
    ),
    "06_Mista_Edge_Radiologia_VLM": (
        '("vision-language model" OR "multimodal large language model" OR MedGemma OR "LLaVA-Med" OR CheXagent OR RadFM) '
        'AND (radiology OR "medical imaging" OR "chest X-ray" OR pneumonia) '
        'AND ("edge computing" OR "local inference" OR embedded OR "NVIDIA Jetson" OR Jetson OR quantization OR llama.cpp OR GGUF)'
    )
}

def search_ieee(query, max_results=150):
    all_articles = []
    start_record = 1

    while len(all_articles) < max_results:
        params = {
            "apikey": API_KEY,
            "format": "json",
            "max_records": RESULTS_PER_PAGE,
            "start_record": start_record,
            "querytext": query,
            "sort": "relevance"
        }

        try:
            response = requests.get(BASE_URL, params=params, timeout=30)
        except Exception as e:
            print(f"Erro de conexão: {e}")
            break

        if response.status_code == 403:
            print("ERRO 403: Chave ainda inativa (Developer Inactive). Espere a ativação.")
            return []
        if response.status_code != 200:
            print(f"Erro {response.status_code}: {response.text[:400]}")
            break

        data = response.json()
        articles = data.get("articles", [])

        if not articles:
            break

        all_articles.extend(articles)
        total = data.get("total_records", 0)
        print(f"  → {len(all_articles)}/{min(max_results, total)} artigos baixados...")

        if start_record + RESULTS_PER_PAGE > total or len(all_articles) >= max_results:
            break

        start_record += RESULTS_PER_PAGE
        time.sleep(0.25)

    return all_articles[:max_results]

def save_to_csv(articles, filename):
    if not articles:
        print("Nenhum artigo para salvar.")
        return

    fieldnames = [
        "Title", "Authors", "Publication Title", "Publication Year",
        "DOI", "Abstract", "Content Type", "IEEE Link", "Article Number"
    ]

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for art in articles:
            authors_list = art.get("authors", {}).get("authors", [])
            authors = "; ".join([a.get("full_name", "") for a in authors_list])

            row = {
                "Title": art.get("title", ""),
                "Authors": authors,
                "Publication Title": art.get("publication_title", ""),
                "Publication Year": art.get("publication_year", ""),
                "DOI": art.get("doi", ""),
                "Abstract": art.get("abstract", ""),
                "Content Type": art.get("content_type", ""),
                "IEEE Link": f"https://doi.org/{art.get('doi')}" if art.get("doi") else "",
                "Article Number": art.get("article_number", "")
            }
            writer.writerow(row)

    print(f"✓ Salvo → {filename} ({len(articles)} registros)")

if __name__ == "__main__":
    print("Iniciando buscas no IEEE Xplore...\n")

    for nome, query in queries.items():
        print("=" * 65)
        print(f"Busca: {nome}")
        print("=" * 65)

        articles = search_ieee(query, max_results=MAX_RESULTS)

        if articles:
            save_to_csv(articles, f"{nome}.csv")
        else:
            print("Nenhum resultado ou chave ainda inativa.\n")

    print("\nProcesso finalizado!")
