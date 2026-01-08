"""
Aplicação Flask standalone para o serviço de gerenciamento de arquivos
Pode ser executado diretamente ou importado em outra aplicação
"""

from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from api_storage_routes import register_storage_routes

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)

# Configurar CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configurações da aplicação
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload

# Registrar rotas de storage
register_storage_routes(app)

# Rota raiz
@app.route('/')
def index():
    return {
        "servico": "Gerenciamento de Arquivos - Audicore",
        "versao": "1.0.0",
        "status": "online",
        "endpoints": {
            "upload": "/api/arquivos/upload",
            "download": "/api/arquivos/download/{id}",
            "info": "/api/arquivos/info/{id}",
            "listar": "/api/arquivos/listar",
            "deletar": "/api/arquivos/deletar/{id}",
            "health": "/api/arquivos/health"
        },
        "documentacao": "/api/docs"
    }

# Rota de documentação
@app.route('/api/docs')
def docs():
    return {
        "titulo": "API de Gerenciamento de Arquivos",
        "descricao": "API REST para upload, download e gerenciamento de arquivos no Azure Blob Storage",
        "versao": "1.0.0",
        "base_url": "/api/arquivos",
        "autenticacao": "Bearer Token (configurar)",
        "repositorio": "https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore"
    }

# Handler de erro
@app.errorhandler(413)
def request_entity_too_large(error):
    return {
        "sucesso": False,
        "mensagem": "Arquivo muito grande. Máximo: 50 MB"
    }, 413

@app.errorhandler(404)
def not_found(error):
    return {
        "sucesso": False,
        "mensagem": "Endpoint não encontrado"
    }, 404

@app.errorhandler(500)
def internal_error(error):
    return {
        "sucesso": False,
        "mensagem": "Erro interno do servidor"
    }, 500

# Executar aplicação
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
