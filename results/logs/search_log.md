# Registro das buscas

Este arquivo documenta a execução das estratégias de busca utilizadas nesta revisão sistemática.

## Objetivo

Registrar de forma transparente e reprodutível as buscas realizadas nas bases de dados selecionadas.

## Bases consultadas

As seguintes bases foram utilizadas:

- PubMed
- IEEE Xplore
- ACM Digital Library
- arXiv
- Google Scholar

## Período da busca

As buscas foram realizadas durante o período definido no protocolo da revisão.

O intervalo temporal considerado para os estudos foi:

**01/01/2023 até a data final definida na estratégia de busca.**

## PubMed

Foram utilizadas três estratégias independentes.

### Q1 — IA multimodal

Resultado identificado:

**2.717 registros**

Estratégia completa disponível em:

`search_strategies/pubmed.txt`

Os registros recuperados foram armazenados em:

`search_results/pubmed_q1.csv`

### Q2 — Inteligência artificial em radiologia

Resultado identificado:

**30.621 registros**

Devido ao elevado número de resultados, a recuperação dos registros foi realizada utilizando a API NCBI E-utilities, evitando a limitação da interface web do PubMed.

Estratégia completa disponível em:

`search_strategies/pubmed.txt`

Registros recuperados por meio do script:

`analysis/scripts/pubmed_q2_search.py`

Arquivos resultantes:

- `search_results/pubmed_q2_pmids.txt`
- `search_results/pubmed_q2.csv`
- `search_results/pubmed_q2_search.log`

### Q3 — MedGemma

Resultado identificado:

**40 registros**

A busca foi realizada utilizando o termo:

`MedGemma`

A estratégia completa encontra-se documentada nos arquivos de estratégia de busca.

Registros recuperados por meio do script:

`analysis/scripts/pubmed_q3_search.py`

## Reprodutibilidade

As consultas automatizadas realizadas no PubMed foram executadas utilizando a API NCBI E-utilities.

Os scripts utilizados estão disponíveis em:

`analysis/scripts/`

Cada estratégia foi implementada separadamente para permitir sua reprodução e auditoria.

## Observações

Os números registrados neste documento correspondem aos resultados retornados pelas bases no momento da execução das buscas.

Alterações posteriores nas bases de dados podem produzir resultados diferentes.
