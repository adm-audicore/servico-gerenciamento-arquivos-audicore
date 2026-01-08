"""
Exemplo de como integrar o sistema de arquivos na sua API Flask existente
"""

# ============================================
# 1. ATUALIZAR requirements.txt
# ============================================
"""
Adicionar ao requirements.txt:

azure-storage-blob>=12.19.0
pyodbc>=5.0.0
werkzeug>=3.0.0
"""

# ============================================
# 2. CONFIGURAR VARIÁVEIS DE AMBIENTE
# ============================================
"""
Adicionar ao arquivo .env:

# Azure Storage
AZURE_STORAGE_ACCOUNT=staudicoreapiprod
AZURE_STORAGE_KEY=sua_chave_aqui
AZURE_STORAGE_CONTAINER=arquivos

# SQL Server (se ainda não tiver)
SQL_CONNECTION_STRING=Driver={ODBC Driver 18 for SQL Server};Server=tcp:sql-dataverse-audicore.database.windows.net,1433;Database=seu-banco;Uid=usuario;Pwd=senha;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
"""

# ============================================
# 3. ATUALIZAR SEU app.py EXISTENTE
# ============================================

from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)
CORS(app)

# ... suas configurações existentes ...

# ============================================
# ADICIONAR: Registrar rotas de storage
# ============================================
from api_storage_routes import register_storage_routes

# Registrar as rotas de arquivos
register_storage_routes(app)

# ... resto do seu código existente ...

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


# ============================================
# 4. EXEMPLO DE USO DIRETO (sem usar as rotas)
# ============================================

"""
Se você quiser usar o storage manager diretamente no seu código,
sem passar pelos endpoints HTTP:
"""

from azure_storage_manager import AzureStorageManager

# Inicializar
storage = AzureStorageManager(
    storage_account=os.getenv('AZURE_STORAGE_ACCOUNT'),
    storage_key=os.getenv('AZURE_STORAGE_KEY'),
    container_name=os.getenv('AZURE_STORAGE_CONTAINER'),
    sql_connection_string=os.getenv('SQL_CONNECTION_STRING')
)

# Exemplo 1: Upload de arquivo
def exemplo_upload():
    with open('documento.pdf', 'rb') as f:
        conteudo = f.read()

    resultado = storage.upload_file(
        file_content=conteudo,
        original_filename='documento.pdf',
        content_type='application/pdf',
        upload_user='usuario@email.com',
        folder='documentos_medicos'
    )

    if resultado['sucesso']:
        print(f"Arquivo salvo! ID: {resultado['id']}")
        print(f"URL: {resultado['url']}")
    else:
        print(f"Erro: {resultado['mensagem']}")


# Exemplo 2: Download de arquivo
def exemplo_download(file_id):
    resultado = storage.download_file(file_id)

    if resultado['sucesso']:
        # Salvar arquivo localmente
        with open(f"downloaded_{resultado['nome_original']}", 'wb') as f:
            f.write(resultado['conteudo'])
        print("Arquivo baixado com sucesso!")
    else:
        print(f"Erro: {resultado['mensagem']}")


# Exemplo 3: Gerar URL temporária
def exemplo_url_temporaria(file_id):
    resultado = storage.generate_download_url(
        file_id=file_id,
        expiry_hours=2
    )

    if resultado['sucesso']:
        print(f"URL temporária (válida por 2 horas):")
        print(resultado['url_download'])
    else:
        print(f"Erro: {resultado['mensagem']}")


# Exemplo 4: Listar arquivos de uma pasta
def exemplo_listar_arquivos():
    resultado = storage.list_files(
        limit=50,
        offset=0,
        folder='documentos_medicos'
    )

    if resultado['sucesso']:
        print(f"Total de arquivos: {resultado['total']}")
        for arquivo in resultado['arquivos']:
            print(f"- {arquivo['nome_original']} ({arquivo['tamanho_bytes']} bytes)")
    else:
        print(f"Erro: {resultado['mensagem']}")


# ============================================
# 5. INTEGRAR COM SUAS ROTAS EXISTENTES
# ============================================

"""
Exemplo: Se você tem uma rota de guias médicas e quer anexar arquivos
"""

from flask import request, jsonify

@app.route('/api/guias/<guia_id>/anexar-arquivo', methods=['POST'])
def anexar_arquivo_guia(guia_id):
    """Anexa um arquivo a uma guia médica específica"""

    data = request.get_json()

    # Fazer upload do arquivo
    resultado = storage.upload_file_base64(
        file_content_base64=data['arquivo'],
        original_filename=data['nome_arquivo'],
        content_type=data.get('tipo_conteudo', 'application/octet-stream'),
        upload_user=data.get('usuario'),
        tags={'guia_id': guia_id, 'tipo': 'anexo_guia'},
        folder=f'guias/{guia_id}'
    )

    if resultado['sucesso']:
        # Aqui você pode salvar a referência do arquivo na tabela de guias
        # Exemplo:
        # UPDATE Guias SET arquivo_id = ? WHERE id = ?

        return jsonify({
            "sucesso": True,
            "mensagem": "Arquivo anexado à guia com sucesso",
            "arquivo": {
                "id": resultado['id'],
                "nome": resultado['nome_original'],
                "url": resultado['url']
            }
        }), 200
    else:
        return jsonify(resultado), 400


@app.route('/api/guias/<guia_id>/arquivos', methods=['GET'])
def listar_arquivos_guia(guia_id):
    """Lista todos os arquivos de uma guia"""

    resultado = storage.list_files(
        limit=100,
        offset=0,
        folder=f'guias/{guia_id}'
    )

    return jsonify(resultado), 200 if resultado['sucesso'] else 400


# ============================================
# 6. OBTER A STORAGE KEY DO AZURE
# ============================================

"""
Para obter a Storage Key, execute no terminal:

az storage account keys list \\
    --account-name staudicoreapiprod \\
    --resource-group rg-audicore-prod \\
    --query '[0].value' \\
    --output tsv

Copie o valor retornado e adicione no .env como AZURE_STORAGE_KEY
"""

# ============================================
# 7. TESTAR A INTEGRAÇÃO
# ============================================

"""
Após configurar tudo, teste com:

# 1. Testar health check
curl http://localhost:5000/api/arquivos/health

# 2. Testar upload (você precisa ter um arquivo base64)
import base64

with open('teste.pdf', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

import requests
response = requests.post('http://localhost:5000/api/arquivos/upload', json={
    'arquivo': b64,
    'nome_arquivo': 'teste.pdf',
    'tipo_conteudo': 'application/pdf',
    'usuario': 'teste@email.com'
})

print(response.json())

# 3. Testar download
file_id = response.json()['id']
response = requests.get(f'http://localhost:5000/api/arquivos/download/{file_id}?url_apenas=true')
print(response.json())
"""

# ============================================
# 8. DEPLOY NO AZURE
# ============================================

"""
Para fazer deploy no Azure Web App:

1. Adicionar os arquivos ao repositório:
   - azure_storage_manager.py
   - api_storage_routes.py

2. Configurar variáveis de ambiente no Azure Portal:
   - AZURE_STORAGE_ACCOUNT=staudicoreapiprod
   - AZURE_STORAGE_KEY=sua_chave
   - AZURE_STORAGE_CONTAINER=arquivos
   - SQL_CONNECTION_STRING=sua_connection_string

3. Deploy:
   az webapp up --name sua-api --resource-group seu-rg

Ou se usar GitHub Actions, adicionar as variáveis como secrets.
"""
