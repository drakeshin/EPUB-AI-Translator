VENV_DIR = .venv
PYTHON = python3
PIP = $(VENV_DIR)/bin/pip
VENV_PYTHON = $(VENV_DIR)/bin/python
SCRIPT_NAME = epub_translator.py
REQUIREMENTS = click

.PHONY: all setup venv install run clean help

all: setup run

venv:
	@echo "Criando ambiente virtual em '$(VENV_DIR)'..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Ambiente virtual criado. Para ativá-lo: source $(VENV_DIR)/bin/activate"

install: venv
	@echo "Instalando dependências: $(REQUIREMENTS)..."
	$(PIP) install $(REQUIREMENTS)
	@echo "Instalação concluída."

setup: install

run:
	@echo "Executando o script principal (Placeholder para demonstração)..."
	@echo "=================================================================="
	@echo ">> INFORMAÇÃO: Execute manualmente com os parâmetros corretos:"
	@echo ">> make run-prod I=<input_path> O=<output_path> S=<source_lang> T=<target_lang> K=<api_key>"
	@echo "=================================================================="

run-prod:
	@if [ -z "$(I)" ] || [ -z "$(O)" ] || [ -z "$(S)" ] || [ -z "$(T)" ] || [ -z "$(K)" ]; then \
		echo "ERRO: Todos os parâmetros (I, O, S, T, K) são obrigatórios para 'run-prod'."; \
		exit 1; \
	fi
	@echo "Iniciando tradução com os parâmetros fornecidos..."
	$(VENV_PYTHON) $(SCRIPT_NAME) --input-path "$(I)" --output-path "$(O)" --source-lang "$(S)" --target-lang "$(T)" --api-key "$(K)"

clean:
	@echo "Removendo ambiente virtual '$(VENV_DIR)' e arquivos temporários..."
	rm -rf $(VENV_DIR)
	rm -rf temp_epub_data temp_epub_data_translated
	@echo "Limpeza concluída."

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
