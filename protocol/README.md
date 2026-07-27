# Review Protocol: Vision-Language Models for Local Radiology Analysis

Este diretório contém o protocolo completo para a Revisão Sistemática da Literatura que fundamenta o desenvolvimento da arquitetura de triagem de pneumonia em dispositivos *edge*.

---

## Objetivo da Revisão

Identificar e sintetizar evidências quantitativas sobre o desempenho de **Vision-Language Models (VLMs)** especializados em radiologia, com foco em técnicas de quantização e inferência local via motores como o `llama.cpp` em hardware de borda (ex.: NVIDIA Jetson).

---

## Estrutura de Arquivos

Para facilitar a reprodução do estudo por outros pesquisadores, a documentação está dividida da seguinte forma:

* **[`protocol.md`](protocol.md):** Documento principal detalhando o fluxo de trabalho seguindo a diretriz PRISMA 2020. Inclui a estratégia de busca nas bases PubMed, arXiv, IEEE Xplore, ACM e Google Scholar, além do cronograma previsto.
* **[`review_questions.md`](review_questions.md):** Define as 7 Questões de Pesquisa (RQs) que guiam a extração de dados, focando em arquiteturas de modelos (ex.: MedGemma), frequência de datasets (ex.: BRAX, MIMIC-CXR) e métricas de eficiência técnica e clínica.
* **[`eligibility.md`](eligibility.md):** Estabelece os critérios rigorosos de inclusão e exclusão. Focam em artigos revisados por pares, disponibilidade de texto completo e suporte técnico para execução offline/local, garantindo a soberania dos dados conforme a LGPD.

---

## Contexto Técnico do Artigo

A revisão aqui documentada serve de base para a validação do modelo **MedGemma 1.5 (4B)** submetido a ajuste-fino via Unsloth e quantizado para o formato GGUF. O objetivo final é medir o *trade-off* entre acurácia clínica (F1-Score) e latência em sistemas hospitalares com infraestrutura tecnológica limitada.

---

## Diretrizes de Qualidade

Os estudos selecionados através deste protocolo são avaliados quanto à:

1. **Clareza da arquitetura do modelo.**
2. **Disponibilidade de código e pesos (reprodutibilidade).**
3. **Uso de conjuntos de teste independentes (*held-out*).**
