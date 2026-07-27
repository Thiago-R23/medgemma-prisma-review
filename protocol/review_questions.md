# Questões de Revisão Sistemática (RQs)

## RQ1: Quais Vision-Language Models são utilizados em radiologia?

Os modelos identificados variam de arquiteturas generalistas adaptadas a modelos de fundação especializados. Entre os principais citados estão:

* **MedGemma (1.5 4B e 27B):** Modelo de fundação do Google otimizado para raciocínio clínico e localização anatômica.
* **MediVLM:** Modelo que utiliza detectores de objetos pré-treinados para extrair regiões anatômicas e gerar laudos.
* **ChestGPT:** Integra o encoder visual EVA com o Llama 2 para classificação e localização de doenças.
* **XrayGPT:** Focado em análise de imagens e resposta a perguntas abertas via interface conversacional.
* **Outros modelos:** MiniGPT-Med, Med-Flamingo, META-CXR, CXR-LLaVA e RaDialog.

---

## RQ2: Quais datasets aparecem com maior frequência?

Os repositórios de imagens de tórax mais recorrentes na literatura são:

* **MIMIC-CXR / MIMIC-CXR-JPG:** O padrão *de facto* para geração de laudos, com mais de 377 mil imagens.
* **CheXpert / CheXpert Plus:** Amplamente utilizado para classificação de 14 achados patológicos.
* **IU X-Ray (Open-I):** Dataset público da Indiana University, muito usado em *benchmarking* de modelos menores.
* **BRAX:** Dataset brasileiro rotulado, essencial para adaptação ao contexto epidemiológico nacional.
* **VinDr-CXR:** Base de dados com anotações de consenso de radiologistas e caixas delimitadoras (*bounding boxes*).

---

## RQ3: Quais hardwares são utilizados?

A literatura descreve desde infraestruturas de nuvem até hardware de borda (*edge computing*):

* **GPUs de Consumo/Desktop:** NVIDIA RTX 4090 (24GB) e RTX 4070 (8GB/16GB) para treinamento e inferência local.
* **Hardware de Borda (Edge):** NVIDIA Jetson Orin Nano (8GB) e AGX Orin (64GB), destacados pela eficiência energética.
* **Outros dispositivos:** Apple Silicon (M-series) via framework Metal, Raspberry Pi 5 (CPU) e aceleradores como Google Coral e Hailo-8.

---

## RQ4: Quais métricas são reportadas?

As métricas dividem-se em eficácia clínica, qualidade de linguagem e desempenho técnico:

* **Eficácia Clínica:** F1-Score (especialmente RadGraph-F1 e CheXpert-F1), AUC, Precisão e Revocação (Recall).
* **Qualidade Textual (NLG):** BLEU (1 a 4), ROUGE-L, METEOR, CIDEr e BERTScore.
* **Performance Técnica:** Latência de inferência (segundos por imagem) e pico de uso de memória VRAM.

---

## RQ5: Há estudos utilizando inferência local?

**Sim.** Diversos trabalhos focam na soberania dos dados e privacidade:

* O uso de **MedGemma 1.5 4B** é explicitamente proposto para execução 100% offline em estações de trabalho clínicas para garantir conformidade com regulamentações de privacidade (LGPD/GDPR).
* Sistemas como o **Radio** e o **EdgeLoRA** são projetados para servir modelos localmente sem dependência de serviços em nuvem.

---

## RQ6: Quais estudos utilizam `llama.cpp`?

O motor `llama.cpp` é identificado como a ferramenta central para:

* Viabilizar a execução de modelos multimodais em hardware diversificado (CPU/GPU) através do formato **GGUF**.
* Implementação da arquitetura proposta para triagem de pneumonia em ambientes com infraestrutura limitada.
* O ecossistema **Radio** utiliza o `llama.cpp` como backend de inferência local.

---

## RQ7: Quais utilizam MedGemma?

O **MedGemma** é o foco principal dos relatórios técnicos e propostas de arquitetura recentes:

* **MedGemma Technical Report (Google DeepMind):** Detalha o treinamento do modelo com o encoder `MedSigLIP`.
* **Ollama e Hugging Face:** Repositórios que fornecem as versões quantizadas (GGUF) do MedGemma 1.5 4B para implantação imediata.
* **Avaliação da UNICAMP:** Estudo que compara o MedGemma com o CheXagent em tarefas de quantização e execução hospitalar.
