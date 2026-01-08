"""
Endpoints da API Flask para gerenciamento de arquivos no Azure Blob Storage
Integração com Power Apps
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import io
from azure_storage_manager import AzureStorageManager

# Criar Blueprint
storage_bp = Blueprint('storage', __name__, url_prefix='/api/arquivos')

# Configurações (mover para variáveis de ambiente em produção)
STORAGE_ACCOUNT = os.getenv('AZURE_STORAGE_ACCOUNT', 'staudicoreapiprod')
STORAGE_KEY = os.getenv('AZURE_STORAGE_KEY')
CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER', 'arquivos')
SQL_CONNECTION_STRING = os.getenv('SQL_CONNECTION_STRING')

# Inicializar gerenciador de storage
storage_manager = AzureStorageManager(
    storage_account=STORAGE_ACCOUNT,
    storage_key=STORAGE_KEY,
    container_name=CONTAINER_NAME,
    sql_connection_string=SQL_CONNECTION_STRING
)


@storage_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para upload de arquivos

    Aceita dois formatos:
    1. multipart/form-data (arquivo enviado diretamente)
    2. application/json com arquivo em base64

    Exemplo JSON (Power Apps):
    {
        "arquivo": "base64_string_aqui",
        "nome_arquivo": "documento.pdf",
        "tipo_conteudo": "application/pdf",
        "usuario": "usuario@email.com",
        "pasta": "documentos_medicos" (opcional)
    }

    Exemplo multipart/form-data:
    - file: arquivo binário
    - usuario: usuário que fez upload (opcional)
    - pasta: pasta dentro do container (opcional)
    """
    try:
        # Verificar se é JSON (base64) ou multipart
        if request.content_type and 'application/json' in request.content_type:
            # Formato JSON com base64 (comum no Power Apps)
            data = request.get_json()

            if not data or 'arquivo' not in data or 'nome_arquivo' not in data:
                return jsonify({
                    "sucesso": False,
                    "mensagem": "Campos obrigatórios: 'arquivo' (base64) e 'nome_arquivo'"
                }), 400

            resultado = storage_manager.upload_file_base64(
                file_content_base64=data['arquivo'],
                original_filename=data['nome_arquivo'],
                content_type=data.get('tipo_conteudo', 'application/octet-stream'),
                upload_user=data.get('usuario'),
                tags=data.get('tags'),
                folder=data.get('pasta')
            )

        else:
            # Formato multipart/form-data
            if 'file' not in request.files:
                return jsonify({
                    "sucesso": False,
                    "mensagem": "Nenhum arquivo enviado"
                }), 400

            file = request.files['file']

            if file.filename == '':
                return jsonify({
                    "sucesso": False,
                    "mensagem": "Nome de arquivo vazio"
                }), 400

            # Ler conteúdo do arquivo
            file_content = file.read()

            resultado = storage_manager.upload_file(
                file_content=file_content,
                original_filename=secure_filename(file.filename),
                content_type=file.content_type or 'application/octet-stream',
                upload_user=request.form.get('usuario'),
                tags=request.form.get('tags'),
                folder=request.form.get('pasta')
            )

        status_code = 200 if resultado.get('sucesso') else 400
        return jsonify(resultado), status_code

    except Exception as e:
        return jsonify({
            "sucesso": False,
            "mensagem": f"Erro no servidor: {str(e)}"
        }), 500


@storage_bp.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """
    Endpoint para download de arquivo

    Parâmetros de query:
    - url_apenas: Se true, retorna apenas a URL com SAS token (padrão: false)
    - validade_horas: Tempo de validade da URL em horas (padrão: 1)

    Exemplos:
    - GET /api/arquivos/download/123e4567-e89b-12d3  -> Baixa o arquivo diretamente
    - GET /api/arquivos/download/123e4567-e89b-12d3?url_apenas=true  -> Retorna URL temporária
    """
    try:
        url_apenas = request.args.get('url_apenas', 'false').lower() == 'true'
        validade_horas = int(request.args.get('validade_horas', 1))

        if url_apenas:
            # Retornar apenas URL com SAS token
            resultado = storage_manager.generate_download_url(
                file_id=file_id,
                expiry_hours=validade_horas
            )

            status_code = 200 if resultado.get('sucesso') else 404
            return jsonify(resultado), status_code

        else:
            # Download direto do arquivo
            resultado = storage_manager.download_file(file_id)

            if not resultado.get('sucesso'):
                return jsonify(resultado), 404

            # Retornar arquivo como stream
            return send_file(
                io.BytesIO(resultado['conteudo']),
                mimetype=resultado['tipo_conteudo'],
                as_attachment=True,
                download_name=resultado['nome_original']
            )

    except Exception as e:
        return jsonify({
            "sucesso": False,
            "mensagem": f"Erro no servidor: {str(e)}"
        }), 500


@storage_bp.route('/info/<file_id>', methods=['GET'])
def get_file_info(file_id):
    """
    Endpoint para obter informações de um arquivo

    Retorna metadados do arquivo sem fazer download
    """
    try:
        file_info = storage_manager.get_file_info(file_id)

        if not file_info:
            return jsonify({
                "sucesso": False,
                "mensagem": "Arquivo não encontrado"
            }), 404

        return jsonify({
            "sucesso": True,
            "arquivo": file_info
        }), 200

    except Exception as e:
        return jsonify({
            "sucesso": False,
            "mensagem": f"Erro no servidor: {str(e)}"
        }), 500


@storage_bp.route('/listar', methods=['GET'])
def list_files():
    """
    Endpoint para listar arquivos

    Parâmetros de query:
    - limite: Número máximo de registros (padrão: 100)
    - offset: Offset para paginação (padrão: 0)
    - pasta: Filtrar por pasta específica

    Exemplo:
    GET /api/arquivos/listar?limite=50&offset=0&pasta=documentos_medicos
    """
    try:
        limite = int(request.args.get('limite', 100))
        offset = int(request.args.get('offset', 0))
        pasta = request.args.get('pasta')

        resultado = storage_manager.list_files(
            limit=limite,
            offset=offset,
            folder=pasta
        )

        status_code = 200 if resultado.get('sucesso') else 400
        return jsonify(resultado), status_code

    except Exception as e:
        return jsonify({
            "sucesso": False,
            "mensagem": f"Erro no servidor: {str(e)}"
        }), 500


@storage_bp.route('/deletar/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """
    Endpoint para deletar arquivo

    Parâmetros de query:
    - permanente: Se true, deleta permanentemente do storage (padrão: false)

    Por padrão, faz soft delete (marca como inativo)
    """
    try:
        permanente = request.args.get('permanente', 'false').lower() == 'true'

        resultado = storage_manager.delete_file(
            file_id=file_id,
            permanent=permanente
        )

        status_code = 200 if resultado.get('sucesso') else 404
        return jsonify(resultado), status_code

    except Exception as e:
        return jsonify({
            "sucesso": False,
            "mensagem": f"Erro no servidor: {str(e)}"
        }), 500


@storage_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar se o serviço está funcionando
    """
    return jsonify({
        "sucesso": True,
        "mensagem": "Serviço de arquivos funcionando",
        "storage_account": STORAGE_ACCOUNT,
        "container": CONTAINER_NAME
    }), 200


# Função para registrar o blueprint na aplicação Flask
def register_storage_routes(app):
    """
    Registra as rotas de storage na aplicação Flask

    Usage:
        from api_storage_routes import register_storage_routes
        register_storage_routes(app)
    """
    app.register_blueprint(storage_bp)
