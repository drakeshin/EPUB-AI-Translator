# 📚 EPUB-AI-Translator: Tradutor de EPUB Inteligente via Gemini CLI

Uma poderosa ferramenta de linha de comando (**CLI**) para traduzir o conteúdo de arquivos **EPUB** utilizando o poder do **Gemini CLI**. O projeto garante que apenas o texto legível seja traduzido, mantendo intacta toda a estrutura interna (tags HTML/XHTML, *metadata* e *packaging*).

---

## ✨ Funcionalidades Principais

* **Extração e Empacotamento de EPUB:** Descompacta o EPUB, isola os arquivos de conteúdo e reempacota o resultado final (dependência conceitual do Calibre, mas usa `zipfile` para o fluxo).
* **Tradução Inteligente:** Utiliza o **Gemini CLI** com um *prompt* de sistema direcionado para traduzir *apenas* o texto contido nas tags HTML/XHTML, ignorando o código e mantendo a formatação original.
* **Interface de Linha de Comando (CLI):** Usa a biblioteca **`click`** para fornecer uma interface simples e robusta.
* **Gestão Segura de API Key:** A chave da API do Gemini é configurada e desativada da variável de ambiente (`GEMINI_API_KEY`) automaticamente após a conclusão ou falha do processo.
* **Modo de Rastreamento (`--track`):** Permite retomar a tradução de onde parou, registrando o progresso de cada arquivo processado.

---

## 🛠 Pré-requisitos

Para utilizar este *script*, você precisa ter os seguintes componentes instalados e configurados no seu sistema:

1. **Python 3.x**
2. **Gemini CLI:** O utilitário de linha de comando do Gemini instalado e acessível via PATH.
3. **Calibre (`ebook-convert`):** (Opcional, mas recomendado para empacotamento robusto) O comando `ebook-convert` do Calibre deve estar no PATH. O *script* usa uma simulação com `zipfile` se o Calibre não for detectado.

### Instalação das Dependências Python

```bash
pip install click
```

---

## 🚀 Uso

Execute o *script* via linha de comando, fornecendo os parâmetros obrigatórios:

```bash
python seu_script_aqui.py --input-path <caminho/do/epub/entrada.epub> \
                         --output-path <caminho/do/epub/saida.epub> \
                         --source-lang <código da lingua de origem> \
                         --target-lang <código da lingua de destino> \
                         --api-key <SUA_CHAVE_API_GEMINI>
```

### Exemplo

Traduzindo um EPUB de Inglês (en) para Português Brasileiro (pt-br):

```bash
python epub_translator.py -i "livro_original.epub" -o "livro_traduzido_ptbr.epub" -s "en" -t "pt-br" -k "AIzaSy...SuaChave..."
```

---

## 🧭 Utilizando o parâmetro `--track`

O parâmetro `--track` ativa o **modo de rastreamento de progresso**, permitindo **retomar uma tradução interrompida** sem precisar reiniciar o processo do zero.

Quando este modo está ativo:

* O script cria um arquivo JSON de rastreio com hash único do EPUB (ex: `a1b2c3d4e5.json`).
* Cada arquivo interno do EPUB é registrado com o status `"translated": true` ou `false`.
* Em execuções futuras, os arquivos já marcados como traduzidos são **pulados automaticamente**, evitando retrabalho e consumo desnecessário da API do Gemini.

### Exemplo de uso

```bash
python epub_translator.py -i "livro.epub" -o "livro_traduzido.epub" -s "zh" -t "pt-br" -k "AIzaSy...Chave..." --track
```

### Quando usar `--track`

Use este modo quando:

* Você vai traduzir **EPUBs grandes** (com dezenas de arquivos internos).
* A tradução pode **ser interrompida** por tempo de execução, rede ou limite de API.
* Você quer **retomar** o processo automaticamente sem perder o progresso.

---

## ⚠️ Aviso Legal (Disclaimer)

Este código-fonte tem propósito unicamente educacional e demonstrativo. O objetivo é ilustrar a aplicação de engenharia de software (como CLI, classes de orquestração e princípios de design) em conjunto com ferramentas de Inteligência Artificial (Gemini CLI).

Não me responsabilizo por qualquer modificação, uso indevido ou ilegal que possa ser feito com este código. O usuário é o único responsável por garantir que o uso do script cumpra todas as leis e regulamentos aplicáveis, incluindo direitos autorais.

---

## 🏗 Estrutura do Projeto (Abstrações)

O *script* segue princípios de design orientado a objetos:

* **`TranslatorBase`:** Interface Abstrata para serviços de tradução (DIP/OCP).
* **`GeminiCliTranslator`:** Implementação concreta que usa o `subprocess` para chamar o Gemini CLI.
* **`EpubExtractor` / `EpubPackager`:** Classes responsáveis pelas operações de I/O do EPUB (SRP).
* **`TranslationFlow`:** Classe orquestradora que gerencia a sequência de extração, tradução e empacotamento, utilizando uma **API Fluente**.

---

## ⚖️ Licença

Este projeto é liberado sob a licença **MIT (Massachusetts Institute of Technology)**.

Você tem a liberdade de:

* **Usar:** Uso privado e comercial.
* **Modificar:** Alterar o código-fonte como desejar.
* **Distribuir:** Compartilhar o código original ou modificado.
* **Vender:** Vender o código ou produtos baseados nele.

A única condição é que a licença MIT original seja incluída em todas as cópias ou porções substanciais do software.

**FAÇA O QUE QUISER COM ESTE CÓDIGO!**