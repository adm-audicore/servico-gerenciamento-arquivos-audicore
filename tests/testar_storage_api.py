"""
Script de teste para validar a API de Storage
Execute este script para verificar se tudo está configurado corretamente
"""

import os
import sys
import base64
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('.env.storage.example')

def test_imports():
    """Testa se todas as dependências estão instaladas"""
    print("=" * 60)
    print("TESTE 1: Verificando dependências")
    print("=" * 60)

    try:
        import azure.storage.blob
        print("✓ azure-storage-blob: OK")
    except ImportError:
        print("✗ azure-storage-blob: FALTANDO")
        print("  Instale com: pip install azure-storage-blob")
        return False

    try:
        import pyodbc
        print("✓ pyodbc: OK")
    except ImportError:
        print("✗ pyodbc: FALTANDO")
        print("  Instale com: pip install pyodbc")
        return False

    try:
        import flask
        print("✓ flask: OK")
    except ImportError:
        print("✗ flask: FALTANDO")
        print("  Instale com: pip install flask")
        return False

    try:
        import werkzeug
        print("✓ werkzeug: OK")
    except ImportError:
        print("✗ werkzeug: FALTANDO")
        print("  Instale com: pip install werkzeug")
        return False

    print("\n✓ Todas as dependências estão instaladas!\n")
    return True


def test_env_variables():
    """Testa se as variáveis de ambiente estão configuradas"""
    print("=" * 60)
    print("TESTE 2: Verificando variáveis de ambiente")
    print("=" * 60)

    required_vars = [
        'AZURE_STORAGE_ACCOUNT',
        'AZURE_STORAGE_KEY',
        'AZURE_STORAGE_CONTAINER',
        'SQL_CONNECTION_STRING'
    ]

    all_configured = True

    for var in required_vars:
        value = os.getenv(var)
        if value and value != 'sua_chave_aqui' and 'NOME_DO_BANCO' not in value:
            print(f"✓ {var}: Configurado")
        else:
            print(f"✗ {var}: NÃO CONFIGURADO ou usa valor de exemplo")
            all_configured = False

    if all_configured:
        print("\n✓ Todas as variáveis estão configuradas!\n")
    else:
        print("\n✗ Configure as variáveis no arquivo .env\n")

    return all_configured


def test_azure_connection():
    """Testa conexão com Azure Storage"""
    print("=" * 60)
    print("TESTE 3: Testando conexão com Azure Storage")
    print("=" * 60)

    try:
        from azure.storage.blob import BlobServiceClient

        storage_account = os.getenv('AZURE_STORAGE_ACCOUNT')
        storage_key = os.getenv('AZURE_STORAGE_KEY')

        connection_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={storage_account};"
            f"AccountKey={storage_key};"
            f"EndpointSuffix=core.windows.net"
        )

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Tentar listar containers
        containers = list(blob_service_client.list_containers())

        print(f"✓ Conexão com Azure Storage: OK")
        print(f"  Containers encontrados: {len(containers)}")

        # Verificar se o container 'arquivos' existe
        container_name = os.getenv('AZURE_STORAGE_CONTAINER')
        container_exists = any(c.name == container_name for c in containers)

        if container_exists:
            print(f"✓ Container '{container_name}': Existe")
        else:
            print(f"✗ Container '{container_name}': NÃO EXISTE")
            print(f"  Crie com: az storage container create --name {container_name} --account-name {storage_account}")
            return False

        print()
        return True

    except Exception as e:
        print(f"✗ Erro ao conectar com Azure Storage: {str(e)}\n")
        return False


def test_sql_connection():
    """Testa conexão com SQL Server"""
    print("=" * 60)
    print("TESTE 4: Testando conexão com SQL Server")
    print("=" * 60)

    try:
        import pyodbc

        sql_connection_string = os.getenv('SQL_CONNECTION_STRING')

        if 'NOME_DO_BANCO' in sql_connection_string or 'USUARIO' in sql_connection_string:
            print("✗ SQL_CONNECTION_STRING ainda usa valores de exemplo")
            print("  Configure com suas credenciais reais\n")
            return False

        conn = pyodbc.connect(sql_connection_string, timeout=10)
        cursor = conn.cursor()

        # Testar conexão
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]

        print("✓ Conexão com SQL Server: OK")
        print(f"  Versão: {version[:50]}...")

        # Verificar se a tabela existe
        cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'ArquivosStorage'
        """)
        table_exists = cursor.fetchone()[0] > 0

        if table_exists:
            print("✓ Tabela 'ArquivosStorage': Existe")
        else:
            print("✗ Tabela 'ArquivosStorage': NÃO EXISTE")
            print("  Execute o script: create_table_arquivos.sql")

        conn.close()
        print()
        return table_exists

    except Exception as e:
        print(f"✗ Erro ao conectar com SQL Server: {str(e)}\n")
        return False


def test_storage_manager():
    """Testa a classe AzureStorageManager"""
    print("=" * 60)
    print("TESTE 5: Testando AzureStorageManager")
    print("=" * 60)

    try:
        from azure_storage_manager import AzureStorageManager

        storage = AzureStorageManager(
            storage_account=os.getenv('AZURE_STORAGE_ACCOUNT'),
            storage_key=os.getenv('AZURE_STORAGE_KEY'),
            container_name=os.getenv('AZURE_STORAGE_CONTAINER'),
            sql_connection_string=os.getenv('SQL_CONNECTION_STRING')
        )

        print("✓ AzureStorageManager: Instanciado com sucesso")

        # Teste de upload (arquivo pequeno de teste)
        print("\nTestando upload...")
        test_content = b"Conteudo de teste para validacao do sistema de storage"
        test_filename = "teste_validacao.txt"

        resultado = storage.upload_file(
            file_content=test_content,
            original_filename=test_filename,
            content_type="text/plain",
            upload_user="teste@teste.com",
            folder="testes"
        )

        if resultado.get('sucesso'):
            print(f"✓ Upload: OK")
            print(f"  ID: {resultado['id']}")
            print(f"  Nome: {resultado['nome_original']}")
            print(f"  Tamanho: {resultado['tamanho_bytes']} bytes")

            file_id = resultado['id']

            # Teste de download
            print("\nTestando download...")
            resultado_download = storage.download_file(file_id)

            if resultado_download.get('sucesso'):
                print(f"✓ Download: OK")
                print(f"  Conteúdo recuperado: {len(resultado_download['conteudo'])} bytes")

                # Teste de URL temporária
                print("\nTestando geração de URL temporária...")
                resultado_url = storage.generate_download_url(file_id, expiry_hours=1)

                if resultado_url.get('sucesso'):
                    print(f"✓ URL temporária: OK")
                    print(f"  URL: {resultado_url['url_download'][:80]}...")

                    # Limpar arquivo de teste
                    print("\nLimpando arquivo de teste...")
                    storage.delete_file(file_id, permanent=True)
                    print("✓ Arquivo de teste deletado")

                    print("\n✓ TODOS OS TESTES PASSARAM COM SUCESSO!\n")
                    return True
                else:
                    print(f"✗ Erro ao gerar URL: {resultado_url['mensagem']}")
            else:
                print(f"✗ Erro no download: {resultado_download['mensagem']}")
        else:
            print(f"✗ Erro no upload: {resultado['mensagem']}")

        return False

    except Exception as e:
        print(f"✗ Erro ao testar AzureStorageManager: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "=" * 60)
    print("TESTE DE CONFIGURAÇÃO - API DE STORAGE")
    print("=" * 60 + "\n")

    results = []

    # Teste 1: Imports
    results.append(("Dependências", test_imports()))

    # Teste 2: Variáveis de ambiente
    results.append(("Variáveis de ambiente", test_env_variables()))

    # Teste 3: Conexão Azure
    results.append(("Azure Storage", test_azure_connection()))

    # Teste 4: Conexão SQL
    results.append(("SQL Server", test_sql_connection()))

    # Teste 5: Storage Manager (apenas se todos os anteriores passaram)
    if all(r[1] for r in results):
        results.append(("Storage Manager", test_storage_manager()))
    else:
        print("=" * 60)
        print("TESTE 5: Pulado (testes anteriores falharam)")
        print("=" * 60 + "\n")
        results.append(("Storage Manager", False))

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASSOU" if passed else "✗ FALHOU"
        print(f"{test_name:.<40} {status}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n" + "=" * 60)
        print("✓ SISTEMA PRONTO PARA USO!")
        print("=" * 60)
        print("\nPróximos passos:")
        print("1. Integre as rotas na sua API (veja exemplo_integracao_api.py)")
        print("2. Configure o Power Apps (veja DOCUMENTACAO_STORAGE_API.md)")
        print("3. Teste os endpoints com Postman ou cURL")
        print()
        return 0
    else:
        print("\n" + "=" * 60)
        print("✗ ALGUNS TESTES FALHARAM")
        print("=" * 60)
        print("\nCorreja os problemas acima antes de usar o sistema.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
