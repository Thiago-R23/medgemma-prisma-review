# Protocolo de Revisão Sistemática da Literatura

## 1. Identificação

* **Título:** Vision-Language Models (VLMs) para Análise de Radiografias de Tórax em Ambiente Local via `llama.cpp`: Uma Revisão Sistemática.
* **Objetivo:** Identificar o estado da arte, desafios técnicos e métricas de desempenho para a execução de VLMs especializados em radiologia executados localmente em hardware de borda (*edge computing*).

---

## 2. Metodologia (Diretriz PRISMA 2020)

Esta revisão segue as recomendações do PRISMA 2020 para garantir a transparência e reprodutibilidade no processo de seleção e análise dos estudos.

### 2.1 Critérios de Elegibilidade

#### Critérios de Inclusão (CI)
* **CI1:** Estudos que propõem, adaptam ou avaliam *Vision-Language Models* (VLMs) aplicados a dados médicos (preferencialmente radiografias de tórax).
* **CI2:** Estudos que abordam técnicas de quantização (ex.: 4-bit, `Q4_K_M`) e formatos de compressão como GGUF para viabilizar inferência local.
* **CI3:** Estudos que relatam métricas quantitativas de desempenho (F1-score, precisão, recall, latência e uso de VRAM).
* **CI4:** Artigos publicados em periódicos, conferências ou repositórios de preprints reconhecidos (arXiv).

#### Critérios de Exclusão (CE)
* **CE1:** Estudos focados exclusivamente em modelos unimodais (apenas visão ou apenas texto) sem integração multimodal.
* **CE2:** Trabalhos que dependem estritamente de processamento em nuvem sem possibilidade de execução offline.
* **CE3:** Artigos sem resultados empíricos ou revisões anteriores que não tragam novos dados técnicos.

### 2.2 Estratégia de Busca

* **Período de busca:** 2020 – 2026 (abrangendo desde a introdução das arquiteturas fundacionais até as otimizações recentes).
* **Idiomas:** Português e Inglês.
* **Bases de dados:** Google Scholar, PubMed/MEDLINE, IEEE Xplore, ACM Digital Library e arXiv.
* **String de Busca (Exemplo):**
  > `("Vision-Language Model" OR "VLM") AND ("Chest X-ray" OR "Radiography") AND ("llama.cpp" OR "quantization" OR "edge computing" OR "NVIDIA Jetson")`

### 2.3 Processo de Seleção (Fluxo PRISMA)

O número final de estudos será determinado pela seguinte equação:

$$N_f = N_i - D - T - A$$

Onde:
* $N_f$: Registros finais incluídos na síntese.
* $N_i$: Registros identificados nas bases de dados.
* $D$: Registros duplicados removidos.
* $T$: Registros excluídos após triagem de títulos e resumos.
* $A$: Artigos excluídos após leitura do texto completo por não atenderem aos critérios técnicos.

---

## 3. Extração de Dados e Avaliação de Qualidade

Para cada estudo incluído, serão extraídos os seguintes parâmetros:

| Categoria | Parâmetros Extraídos |
| :--- | :--- |
| **Arquitetura do Modelo** | Encoders (ex.: `MedSigLIP`) e decodificadores (ex.: `Gemma`). |
| **Otimização** | Método de quantização e motor de inferência (`llama.cpp`). |
| **Dataset** | Uso de bases públicas ou privadas (ex.: BRAX, MIMIC-CXR, CheXpert). |
| **Hardware** | Especificações de CPU/GPU e consumo de memória (ex.: NVIDIA Jetson Orin Nano Super 8GB). |
| **Métricas** | F1-Score para detecção de condições clínicas (ex.: pneumonia), latência de inferência e pico de VRAM. |

---

## 4. Cronograma

| Etapa | Data Prevista |
| :--- | :--- |
| **Execução das Buscas** | Julho de 2026 |
| **Triagem e Seleção (PRISMA)** | Julho de 2026 |
| **Análise, Extração e Síntese** | Agosto de 2026 |
| **Redação Final do Artigo** | Agosto de 2026 |
