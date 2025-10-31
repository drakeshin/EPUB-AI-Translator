# ==============================================================================
# Makefile para o EPUB-AI-Translator
# Gerenciamento de ambiente virtual, dependências e execução do projeto.
# ==============================================================================

# Variáveis
VENV_DIR = .venv
PYTHON = python3
PIP = $(VENV_DIR)/bin/pip
VENV_PYTHON = $(VENV_DIR)/bin/python
SCRIPT_NAME = epub_translator.py # Ajuste o nome do seu script principal, se necessário

# Dependências Python (apenas click, conforme o script atual)
REQUIREMENTS = click

.PHONY: all setup venv install run clean help

# Target padrão (executa o setup e a execução)
all: setup run

# ------------------------------------------------------------------------------
# GERENCIAMENTO DE AMBIENTE E DEPENDÊNCIAS
# ------------------------------------------------------------------------------

# Cria o ambiente virtual
venv:
	@echo "Criando ambiente virtual em '$(VENV_DIR)'..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Ambiente virtual criado. Para ativá-lo: source $(VENV_DIR)/bin/activate"

# Instala as dependências
install: venv
	@echo "Instalando dependências: $(REQUIREMENTS)..."
	$(PIP) install $(REQUIREMENTS)
	@echo "Instalação concluída."

# Faz o setup completo (venv + install)
setup: install

# ------------------------------------------------------------------------------
# EXECUÇÃO DO PROJETO (REQUER QUE O FLUXO 'setup' TENHA SIDO EXECUTADO)
# ------------------------------------------------------------------------------

# Target para executar o script.
# NOTA: Este comando é um PLACEHOLDER.
# Você deve ajustá-lo com caminhos, idiomas e sua chave de API reais.
run:
	@echo "Executando o script principal (Placeholder para demonstração)..."
	@echo "=================================================================="
	@echo ">> INFORMAÇÃO: Execute manualmente com os parâmetros corretos:"
	@echo ">> make run-prod I=<input_path> O=<output_path> S=<source_lang> T=<target_lang> K=<api_key>"
	@echo "=================================================================="
	# Exemplo de execução (Comandos reais devem usar make run-prod)
	# $(VENV_PYTHON) $(SCRIPT_NAME) -i "input.epub" -o "output.epub" -s "en" -t "pt" -k "SUA_CHAVE_AQUI"


# Target real de execução com variáveis de ambiente do Makefile
# Uso: make run-prod I="epub.epub" O="traduzido.epub" S="en" T="pt-br" K="SUA_CHAVE"
run-prod:
	@if [ -z "$(I)" ] || [ -z "$(O)" ] || [ -z "$(S)" ] || [ -z "$(T)" ] || [ -z "$(K)" ]; then \
		echo "ERRO: Todos os parâmetros (I, O, S, T, K) são obrigatórios para 'run-prod'."; \
		exit 1; \
	fi
	@echo "Iniciando tradução com os parâmetros fornecidos..."
	$(VENV_PYTHON) $(SCRIPT_NAME) --input-path "$(I)" --output-path "$(O)" --source-lang "$(S)" --target-lang "$(T)" --api-key "$(K)"

# ------------------------------------------------------------------------------
# UTILITÁRIOS
# ------------------------------------------------------------------------------

# Limpa o ambiente virtual
clean:
	@echo "Removendo ambiente virtual '$(VENV_DIR)' e arquivos temporários..."
	rm -rf $(VENV_DIR)
	rm -rf temp_epub_data temp_epub_data_translated
	@echo "Limpeza concluída."

# Exibe as opções de ajuda
help:
	@echo "Uso: make [target]"
	@echo ""
	@echo "Targets disponíveis:"
	@echo "  all        : Executa 'setup' e 'run' (placeholder)."
	@echo "  setup      : Cria o venv e instala todas as dependências."
	@echo "  venv       : Cria o ambiente virtual (.venv)."
	@echo "  install    : Instala as dependências no venv."
	@echo "  run        : Exibe o comando de execução real (placeholder)."
	@echo "  run-prod   : Executa o script com os parâmetros (I, O, S, T, K) via variáveis."
	@echo "  clean      : Remove o ambiente virtual e diretórios temporários."