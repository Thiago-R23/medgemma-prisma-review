# Critérios de Elegibilidade

Este documento estabelece os limites para a seleção de estudos na revisão sistemática sobre a execução local de **Vision-Language Models (VLMs)** aplicados à radiologia.

---

## 1. Critérios de Inclusão (*Inclusion Criteria*)

Para serem incluídos na base de dados, os estudos devem atender a **todos** os seguintes critérios:

* **VLM (Vision-Language Model):** O estudo deve propor, adaptar ou avaliar modelos que integrem nativamente o processamento de imagens e linguagem natural em uma arquitetura única.
* **Aplicação Médica:** O foco principal deve ser o domínio da saúde, visando suporte à decisão clínica, diagnóstico ou auxílio na triagem médica.
* **Radiografia:** O modelo deve ser testado ou treinado especificamente com imagens de radiografia (preferencialmente de tórax), utilizando datasets reconhecidos como BRAX, MIMIC-CXR ou CheXpert.
* **Texto Completo Disponível:** Apenas artigos com acesso integral ao corpo do texto serão considerados, permitindo a extração detalhada de metodologias e resultados.
* **Revisão por Pares e Qualidade:** Serão aceitos artigos publicados em periódicos científicos, anais de conferências revisadas por pares (ex.: MICCAI, CVPR, IEEE Access) ou preprints em repositórios acadêmicos reconhecidos como o arXiv.
* **Métricas Quantitativas:** O estudo deve reportar resultados numéricos de performance, como acurácia clínica (F1-Score, AUC), latência de inferência ou eficiência de memória.

---

## 2. Critérios de Exclusão (*Exclusion Criteria*)

Estudos que apresentem **qualquer uma** das seguintes características serão descartados:

* **Modelos Unimodais:** Trabalhos focados exclusivamente em classificação de imagens sem componente de linguagem ou processamento de texto puro sem visão.
* **Domínio Geral:** VLMs genéricos (ex.: CLIP original) avaliados apenas em objetos do cotidiano, sem adaptação ou avaliação no contexto médico.
* **Ausência de Dados Empíricos:** Editoriais, cartas ao editor, resumos curtos (*abstract-only*), opiniões ou tutoriais sem experimentação técnica formal.
* **Dependência Estrita de Nuvem:** Trabalhos que não permitem ou não discutem a viabilidade de execução offline/local, visto que o foco desta arquitetura é a computação de borda via `llama.cpp`.

---

## 3. Idioma e Período

* **Idioma:** Serão incluídos estudos redigidos em **Português** e **Inglês**, dada a natureza global das arquiteturas de IA e o foco epidemiológico no Brasil.
* **Período:** Publicações entre **2020 e 2026**, abrangendo o surgimento dos modelos de fundação multimodais e as otimizações recentes de quantização.
