import os
import re
import shutil
import zipfile
import subprocess
from abc import ABC, abstractmethod
from typing import List
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
            
            if not content_translated:
                raise ValueError("O Gemini CLI não retornou nenhum conteúdo (stdout vazio).")

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content_translated)

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
                if file.endswith(('.html', '.xhtml', '.htm')):
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
        self.temp_dir = "temp_epub_data"
        self.original_temp_dir = "temp_epub_data"
        self.content_files: List[str] = []

    def extract(self) -> 'TranslationFlow':
        """Etapa 1: Extrai o EPUB."""
        print("--- INICIANDO EXTRAÇÃO ---")
        extractor = EpubExtractor(self.epub_path, self.temp_dir)
        extractor.extract()
        self.content_files = extractor.get_content_files()
        return self

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
            
            self.translator.translate_file(file_path, output_path, source_lang, target_lang)
            translated_files.append(output_path)
            
        self.temp_dir = temp_translated_dir 
        return self

    def package(self) -> 'TranslationFlow':
        """Etapa 3: Unifica os arquivos traduzidos em um novo EPUB."""
        print("\n--- INICIANDO EMPACOTAMENTO ---")
        packager = EpubPackager(self.temp_dir, self.output_epub_path)
        packager.package()
        return self
        
    def cleanup(self) -> None:
        """Limpa arquivos temporários."""
        print("\n--- LIMPEZA ---")
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"Diretório temporário removido: {self.temp_dir}")
        
        if self.original_temp_dir != self.temp_dir and os.path.exists(self.original_temp_dir):
            shutil.rmtree(self.original_temp_dir)
            print(f"Diretório original removido: {self.original_temp_dir}")


@click.command()
@click.option('--input-path', '-i', required=True, type=click.Path(exists=True), help='Caminho para o arquivo EPUB de entrada.')
@click.option('--output-path', '-o', required=True, type=click.Path(), help='Caminho para o arquivo EPUB de saída traduzido.')
@click.option('--source-lang', '-s', required=True, help='Linguagem de origem (ex: en).')
@click.option('--target-lang', '-t', required=True, help='Linguagem de destino (ex: pt-br).')
@click.option('--api-key', '-k', required=True, help='Chave da API do Gemini. Será configurada temporariamente na variável de ambiente.')
def cli_main(input_path: str, output_path: str, source_lang: str, target_lang: str, api_key: str):
    """
    Ferramenta para tradução de EPUBs usando o Gemini CLI.
    """
    
    flow = None
    try:
        set_gemini_api_key(api_key)
        
        print(f"\n--- INICIANDO FLUXO DE TRADUÇÃO ---")
        print(f"De: {input_path} ({source_lang})")
        print(f"Para: {output_path} ({target_lang})")

        translator_service = GeminiCliTranslator() 
        
        flow = TranslationFlow(
            epub_path=input_path,
            output_epub_path=output_path,
            translator=translator_service
        )
        
        flow.extract().translate_all(source_lang=source_lang, target_lang=target_lang).package()
        
        print("\nFLUXO CONCLUÍDO COM SUCESSO.")
        
    except FileNotFoundError as e:
        print(f"\nERRO: Um arquivo necessário não foi encontrado. {e}")
    except subprocess.CalledProcessError as e:
        print(f"\nERRO DE PROCESSO: Falha na execução de um comando externo (Calibre ou Gemini CLI). {e}")
    except Exception as e:
        print(f"\nERRO CRÍTICO NO FLUXO: {e}")
        
    finally:
        if flow:
            flow.cleanup()
        unset_gemini_api_key()
        pass

if __name__ == "__main__":
    cli_main()