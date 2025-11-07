import os
import re
import json
import shutil
import zipfile
import subprocess
import time
from abc import ABC, abstractmethod
from typing import List
from typing import List, Dict, Any
import hashlib
import click

CALIBRE_CLI = "ebook-convert"
GEMINI_CLI = "gemini"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"

def set_gemini_api_key(api_key: str):
    """Exporta a chave da API para a variável de ambiente GEMINI_API_KEY."""
    if api_key:
        os.environ[GEMINI_API_KEY_ENV] = api_key
        print("Chave da API Gemini configurada na variável de ambiente.")

def unset_gemini_api_key():
    """Remove a variável de ambiente GEMINI_API_KEY."""
    if GEMINI_API_KEY_ENV in os.environ:
        del os.environ[GEMINI_API_KEY_ENV]
        print("Variável de ambiente GEMINI_API_KEY removida.")


class TranslatorBase(ABC):
    """Classe base abstrata para serviços de tradução (OCP, LSP)."""
    @abstractmethod
    def translate_file(self, input_path: str, output_path: str, source_lang: str, target_lang: str) -> None:
        """Traduz um arquivo de texto, mantendo tags HTML/XHTML."""
        pass


class GeminiCliTranslator(TranslatorBase):
    """Implementação que usa o Gemini CLI para tradução (LSP)."""
    
    def _translate_content(self, input_path: str, output_path: str, source_lang: str, target_lang: str) -> None:
        """
        Traduz o texto fora das tags usando o Gemini CLI.
        """
        
        prompt = (
            f"Traduza o seguinte conteúdo de {source_lang} para {target_lang}. "
            f"É um trecho de código HTML/XHTML. Você deve traduzir *apenas* "
            f"o texto que *não* está dentro de nenhuma tag (como <p>, <h1>, etc.). "
            f"Retorne o conteúdo completo, mantendo a estrutura original e todas as tags intactas, "
            f"substituindo apenas o texto traduzido."
        )

        command = f'{GEMINI_CLI} --model gemini-2.5-flash --prompt "{prompt}" < {input_path}'
        
        print(f"  > Executando: Gemini CLI para traduzir {input_path}...")

        total_lines_input_path = self._check_content_lines_from_path(input_path)

        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                shell=True, 
                encoding='utf-8', 
                check=True
            )
            
            content_translated = result.stdout
            content_translated = re.sub(r"^(?:```(?:html|xhtml|xml|opf|ncx)\n)", "", content_translated, flags=re.IGNORECASE)
            content_translated = re.sub(r"(\n)?```(\n)?$", "", content_translated)

            if not content_translated:
                raise ValueError("O Gemini CLI não retornou nenhum conteúdo (stdout vazio).")

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content_translated)

            total_lines_translated = self._check_content_lines_from_path(output_path)

            if total_lines_translated < round((total_lines_input_path * 0.90)):
                raise ValueError("Arquivo traduzido de forma incorreta pelo Gemini CLI.")

            print(f"  > Arquivo traduzido salvo em: {output_path}")

        except subprocess.CalledProcessError as e:
            print(f"  > ERRO ao executar o Gemini CLI: {e}")
            print(f"  > Stderr: {e.stderr}")
            raise e
        except FileNotFoundError:
            print(f"  > ERRO: O comando '{GEMINI_CLI}' não foi encontrado.")
            print("  > Verifique se o Gemini CLI está instalado e no PATH do sistema.")
            raise
        except Exception as e:
            print(f"  > ERRO inesperado na tradução: {e}")
            raise
    
    def _check_content_lines_from_path(self, content):
        try:
            with open(content, 'r', encoding='utf-8') as arquivo:
                conteudo = arquivo.read()
        except FileNotFoundError:
            print(f"Erro: O arquivo '{content}' não foi encontrado.")
            conteudo = 0

        if conteudo is not None:
            quantidade_linhas = len(conteudo.splitlines())
            return quantidade_linhas
        else:
            return 0
    
    def _check_content_lines(self, content):
        quantidade_linhas = len(content.splitlines())
        return quantidade_linhas

    def translate_file(self, input_path: str, output_path: str, source_lang: str, target_lang: str) -> None:
        """Executa a tradução no arquivo."""
        self._translate_content(input_path, output_path, source_lang, target_lang)


class EpubExtractor:
    """Extrai o EPUB para uma pasta (SRP)."""
    def __init__(self, epub_path: str, output_dir: str):
        self.epub_path = epub_path
        self.output_dir = output_dir

    def extract(self) -> None:
        """Descompacta o EPUB (ZIP) para a pasta de saída."""
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)
        
        print(f"Extraindo EPUB: {self.epub_path} para {self.output_dir}")
        with zipfile.ZipFile(self.epub_path, 'r') as zip_ref:
            zip_ref.extractall(self.output_dir)
        
        print(f"Extração concluída.")

    def get_content_files(self) -> List[str]:
        """Retorna a lista de arquivos de conteúdo (HTML/XHTML) para tradução."""
        content_files = []
        for root, _, files in os.walk(self.output_dir):
            for file in files:
                if file.endswith(('.html', '.xhtml', '.htm', '.ncx', '.opf')):
                    content_files.append(os.path.join(root, file))
        return content_files

class EpubPackager:
    """Unifica os arquivos traduzidos de volta em um EPUB (SRP)."""
    def __init__(self, input_dir: str, output_epub_path: str):
        self.input_dir = input_dir
        self.output_epub_path = output_epub_path

    def package(self) -> None:
        """Reempacota a pasta de conteúdo em um novo arquivo EPUB."""
        print(f"Empacotando de volta: {self.input_dir} para {self.output_epub_path}")
        
        print(f"  > Simulação: Chamando Calibre CLI para reempacotar (ou usando zipfile)...")

        if os.path.exists(self.output_epub_path):
            os.remove(self.output_epub_path)

        base_name = os.path.basename(self.output_epub_path).replace('.epub', '')
        temp_zip_path = shutil.make_archive(base_name, 'zip', self.input_dir)
        
        shutil.move(temp_zip_path, self.output_epub_path)
        
        print(f"Empacotamento concluído. Novo EPUB salvo em: {self.output_epub_path}")


class TranslationFlow:
    """
    Orquestrador principal usando Fluent API.
    A dependência do tradutor é injetada (DIP).
    """
    def __init__(self, epub_path: str, output_epub_path: str, translator: TranslatorBase):
        self.epub_path = epub_path
        self.output_epub_path = output_epub_path
        self.translator = translator
        # Modificado para garantir que o temp_dir seja único por execução/livro
        epub_hash_short = hashlib.md5(epub_path.encode('utf-8')).hexdigest()[:10]
        self.temp_dir = f"temp_epub_data_{epub_hash_short}"
        self.original_temp_dir = f"temp_epub_data_{epub_hash_short}"
        self.content_files: List[str] = []
        self.track: List[Dict[str, Any]] = []
        self.track_filename = ""
        self.can_retry = False
        self.retry_limit = 1
        self.retry_time = 10
    
    def setRetry(self, can:bool) -> 'TranslationFlow':
        self.can_retry = can
        return self
    
    def setRetryLimit(self, limit:int) -> 'TranslationFlow':
        self.retry_limit = limit
        return self
    
    def setRetryTime(self, time:int) -> 'TranslationFlow':
        self.retry_time = time
        return self
    
    def extract(self) -> 'TranslationFlow':
        """Etapa 1: Extrai o EPUB."""
        print("--- INICIANDO EXTRAÇÃO ---")
        extractor = EpubExtractor(self.epub_path, self.temp_dir)
        extractor.extract()
        self.content_files = extractor.get_content_files()
        return self
    
    def setTrack(self) -> 'TranslationFlow':
        print("--- Fazendo track ---")
        
        # O HASH DO EPUB_PATH JÁ GARANTE UM TRACK POR ARQUIVO
        epub_hash = hashlib.md5(self.epub_path.encode('utf-8')).hexdigest()
        self.track_filename = f"{epub_hash}.json"
        
        if os.path.exists(self.track_filename):
            print(f"Arquivo de track existente: {self.track_filename}. Carregando...")
            with open(self.track_filename, 'r', encoding='utf-8') as f:
                self.track = json.load(f)
            # Recarregar os caminhos de arquivo baseados no temp_dir atual
            # (caso o temp_dir original tenha sido limpo)
            # Isto é uma salvaguarda:
            new_content_files = []
            for root, _, files in os.walk(self.original_temp_dir):
                for file in files:
                    if file.endswith(('.html', '.xhtml', '.htm', '.ncx', '.opf')):
                        new_content_files.append(os.path.join(root, file))

            if len(new_content_files) != len(self.track):
                 print("Inconsistência detectada. Gerando novo track...")
                 # Força a regeneração se os arquivos extraídos não baterem com o track
                 os.remove(self.track_filename)
                 return self.setTrack() # Recomeça a função
            
            # Atualiza os caminhos no track carregado para refletir o temp_dir atual
            for i, track_item in enumerate(self.track):
                # Assume que a ordem está preservada
                track_item["file"] = new_content_files[i]

            return self

        print("Arquivo de track não encontrado. Gerando novo track...")
        self.track = []
        for file in self.content_files:
            self.track.append({
                "file": file, 
                "relative": "", 
                "output": "",   
                "translated": False
            })

        try:
            with open(self.track_filename, 'w', encoding='utf-8') as f:
                json.dump(self.track, f, indent=4)
            print(f"Novo arquivo de track salvo: {self.track_filename}")
        except Exception as e:
            print(f"Erro ao salvar arquivo de track: {e}")

        return self
    
    def updateTrackFile(self) -> 'TranslationFlow' :
        try:
            with open(self.track_filename, 'w', encoding='utf-8') as f:
                json.dump(self.track, f, indent=4)
            print(f"Arquivo de track atualizado: {self.track_filename}")
        except Exception as e:
            print(f"Erro ao atualizar arquivo de track: {e}")
        return self
    
    def isTrackComplete(self):
        try:
            track_to_verify = None
            if os.path.exists(self.track_filename):
                print(f"Verificando se track está completo. Carregando {self.track_filename}...")
                with open(self.track_filename, 'r', encoding='utf-8') as f:
                    track_to_verify = json.load(f)
                for track in track_to_verify:
                    is_already_translated = track.get("translated", False)
                    if not is_already_translated:
                        print(f"Arquivo de track {self.track_filename} incompleto!")
                        return False
                print(f"Arquivo de track {self.track_filename} completo!")
                return True
            print(f"Arquivo de track {self.track_filename} não encontrado!")
            return False
        except Exception as e:
            print(f"Erro ao verificar arquivo de track: {e}")
            return False

    def translate_all(self, source_lang: str, target_lang: str) -> 'TranslationFlow':
        """Etapa 2: Traduz todos os arquivos de conteúdo."""
        print("\n--- INICIANDO TRADUÇÃO ---")
        if not self.content_files:
            print("Nenhum arquivo de conteúdo encontrado para tradução.")
            return self
            
        temp_translated_dir = f"{self.original_temp_dir}_translated"
        if os.path.exists(temp_translated_dir):
            shutil.rmtree(temp_translated_dir)
        shutil.copytree(self.temp_dir, temp_translated_dir)
        
        translated_files = []
        for file_path in self.content_files:
            relative_path = os.path.relpath(file_path, self.temp_dir)
            output_path = os.path.join(temp_translated_dir, relative_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            for timel in range(self.retry_limit):
                try:
                    self.translator.translate_file(file_path, output_path, source_lang, target_lang)
                    translated_files.append(output_path)
                    break
                except:
                    if self.can_retry:
                        print(f"Erro na tradução, tentando novamente em {self.retry_time}m")
                        time.sleep(self.retry_time)
                        continue
                    raise ValueError("Arquivo não foi devidamente traduzido.")
                
        self.temp_dir = temp_translated_dir 
        return self
    
    def has_chinese(text: str) -> bool:
        """Verifica se o texto contém caracteres chineses (simplificado ou tradicional)."""
        return bool(re.search(r'[\u4e00-\u9fff]', text))

    def translate_all_from_track(self, source_lang: str, target_lang: str) -> 'TranslationFlow':
        """Etapa 2: Traduz todos os arquivos de conteúdo, 
        verificando se arquivos marcados como traduzidos ainda contêm chinês."""
        print("\n--- INICIANDO TRADUÇÃO ---")
        if not self.track:
            print("Nenhum arquivo de conteúdo encontrado para tradução.")
            return self

        temp_translated_dir = f"{self.original_temp_dir}_translated"
        if not os.path.exists(temp_translated_dir):
            shutil.copytree(self.temp_dir, temp_translated_dir)

        translated_files = []   

        for file in self.track:
            file_path = file.get("file")
            is_translated = file.get("translated", False)   

            if is_translated:
                print(f"Arquivo {file_path} já traduzido. Pulando...")
                continue

            relative_path = os.path.relpath(file_path, self.temp_dir)
            output_path = os.path.join(temp_translated_dir, relative_path)
            file["relative"] = relative_path
            file["output"] = output_path

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            for timelimit in range(self.retry_limit):
                try:
                    self.translator.translate_file(file_path, output_path, source_lang, target_lang)
                    translated_files.append(output_path)
                    file["translated"] = True
                    break
                except:
                    if self.can_retry:
                        print(f"Erro na tradução, tentando novamente em {self.retry_time}m")
                        time.sleep((self.retry_time*60))
                        continue
                    raise ValueError("Arquivo não foi devidamente traduzido.")

            self.updateTrackFile()

        self.temp_dir = temp_translated_dir 
        return self

    def package(self) -> 'TranslationFlow':
        """Etapa 3: Unifica os arquivos traduzidos em um novo EPUB."""
        print("\n--- INICIANDO EMPACOTAMENTO ---")
        if not self.isTrackComplete():
            print("Arquivo de track incompleto, impossível realizar empacotamento!")
            raise Exception("Arquivo de track incompleto, impossível realizar empacotamento!")
        packager = EpubPackager(self.temp_dir, self.output_epub_path)
        packager.package()
        return self
        
    def cleanup(self) -> None:
        """Limpa arquivos temporários."""
        print("\n--- LIMPEZA ---")
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"Diretório temporário removido: {self.temp_dir}")

        if os.path.exists(self.track_filename):
            os.remove(self.track_filename)
            print(f"Arquivo de track removido: {self.track_filename}")
        
        if self.original_temp_dir != self.temp_dir and os.path.exists(self.original_temp_dir):
            shutil.rmtree(self.original_temp_dir)
            print(f"Diretório original removido: {self.original_temp_dir}")


@click.command()
@click.option('--input-path', '-i', required=True, type=click.Path(exists=True), help='Caminho para o arquivo EPUB de entrada ou diretório contendo EPUBs.')
@click.option('--output-path', '-o', required=False, default=None, type=click.Path(), help='Caminho para o arquivo EPUB de saída traduzido. Ignorado se --input-path for um diretório.')
@click.option('--source-lang', '-s', required=True, help='Linguagem de origem (ex: en).')
@click.option('--target-lang', '-t', required=True, help='Linguagem de destino (ex: pt-br).')
@click.option('--api-key', '-k', required=True, help='Chave da API do Gemini. Será configurada temporariamente na variável de ambiente.')
@click.option('--track', '-r', is_flag=True, default=False,required=False, help='Mantem rastreio de onde parou')
@click.option('--retry', '-e', is_flag=True, default=False,required=False, help='Em caso de erro na tradução, será feito retry')
@click.option('--retry-limit', '-l', required=False, default=10, help='Limite de retry')
@click.option('--retry-time', '-u', required=False, default=10, help='Tempo de espera entre cada retry em minutos')
def cli_main(input_path: str, output_path: str, source_lang: str, target_lang: str, api_key: str, track: bool, retry:bool, retry_limit: int, retry_time: int):
    """
    Ferramenta para tradução de EPUBs usando o Gemini CLI.
    """
    
    flow = None
    try:
        set_gemini_api_key(api_key)
        translator_service = GeminiCliTranslator() # Definido uma vez
        
        # --- MODO DIRETÓRIO ---
        if os.path.isdir(input_path):
            print(f"\n--- INICIANDO FLUXO DE TRADUÇÃO (MODO DIRETÓRIO) ---")
            print(f"Diretório de entrada: {input_path}")
            print(f"Linguagem de destino: {target_lang.upper()}")

            # Obtém todos os arquivos para verificação de existência
            all_files_set = set(os.listdir(input_path))
            
            # Define o prefixo de saída esperado
            prefix = f"[TRANSLATED][{target_lang.upper()}]"
            
            epub_files = [] # Lista final de arquivos a processar

            for filename in all_files_set:
                # 1. Encontra apenas arquivos .epub originais
                if filename.lower().endswith('.epub') and not filename.startswith('[TRANSLATED]'):
                    
                    # 2. Constrói o nome do arquivo de saída esperado
                    expected_output_name = f"{prefix}{filename}"
                    
                    # 3. VERIFICAÇÃO CRUCIAL: Processa o original APENAS SE a saída NÃO existir
                    if expected_output_name not in all_files_set:
                        epub_files.append(filename)
            
            if not epub_files:
                print("Nenhum arquivo .epub novo (que precise de tradução) foi encontrado no diretório.")
                return # Sai da função cli_main

            print(f"Arquivos EPUB encontrados para tradução: {len(epub_files)}")
            
            for i, epub_file in enumerate(epub_files):
                current_input = os.path.join(input_path, epub_file)
                
                # Gera o nome do arquivo de saída conforme requisito
                output_filename = f"[TRANSLATED][{target_lang.upper()}]{epub_file}"
                current_output = os.path.join(input_path, output_filename)
                
                print(f"\n--- Processando Arquivo {i+1}/{len(epub_files)}: {epub_file} ---")
                
                flow = None # Reseta o flow para cada iteração
                try:
                    flow = TranslationFlow(
                        epub_path=current_input,
                        output_epub_path=current_output,
                        translator=translator_service
                    )
                    
                    if track:
                        # O cleanup (incluindo remoção do track) é chamado no sucesso
                        flow.setRetry(retry).setRetryLimit(retry_limit).setRetryTime(retry_time).extract().setTrack().translate_all_from_track(source_lang=source_lang, target_lang=target_lang).package()
                        flow.cleanup()
                    else:
                        flow.extract().translate_all(source_lang=source_lang, target_lang=target_lang).package()
                        flow.cleanup() # Limpa os temps (sem track)
                    
                    print(f"--- Arquivo {epub_file} concluído ---")
                
                except Exception as e:
                    print(f"\nERRO CRÍTICO NO FLUXO (Arquivo: {epub_file}): {e}")
                    print(f"Continuando para o próximo arquivo...")
                    # Limpeza parcial se falhar (sem track)
                    if flow and track == False:
                        flow.cleanup()
                    # Se for com track, NÃO limpa, para preservar o .json
                    if flow and track == True and hasattr(flow, 'track_filename') and flow.track_filename:
                         print(f"Preservando arquivo de track: {flow.track_filename}")

            print("\nFLUXO (MODO DIRETÓRIO) CONCLUÍDO.")

        # --- MODO ARQUIVO ÚNICO ---
        elif os.path.isfile(input_path):
            
            # Validação do output_path obrigatório para modo arquivo
            if output_path is None:
                raise click.UsageError("O --output-path ('-o') é obrigatório quando --input-path é um arquivo.")

            print(f"\n--- INICIANDO FLUXO DE TRADUÇÃO (MODO ARQUIVO ÚNICO) ---")
            print(f"De: {input_path} ({source_lang})")
            print(f"Para: {output_path} ({target_lang})")
            
            flow = TranslationFlow(
                epub_path=input_path,
                output_epub_path=output_path,
                translator=translator_service
            )
            
            if track:
                flow.setRetry(retry).setRetryLimit(retry_limit).setRetryTime(retry_time).extract().setTrack().translate_all_from_track(source_lang=source_lang, target_lang=target_lang).package()
                flow.cleanup() # Limpa o track file e temps
            else:
                flow.extract().translate_all(source_lang=source_lang, target_lang=target_lang).package()
                # A limpeza de track=False será pega pelo 'finally'
            
            print("\nFLUXO (MODO ARQUIVO ÚNICO) CONCLUÍDO COM SUCESSO.")
        
        else:
             raise FileNotFoundError(f"O caminho de entrada não é um arquivo ou diretório válido: {input_path}")

    except (FileNotFoundError, subprocess.CalledProcessError, click.UsageError, Exception) as e:
        # Captura erros de setup (API key), erros de validação do Click, ou falhas no modo arquivo único
        print(f"\nERRO CRÍTICO NO FLUXO: {e}")
        
    finally:
        if os.path.isfile(input_path) and flow and track == False:
            print("Executando limpeza final (modo arquivo, sem track)...")
            flow.cleanup()
        unset_gemini_api_key()
        pass

if __name__ == "__main__":
    cli_main()