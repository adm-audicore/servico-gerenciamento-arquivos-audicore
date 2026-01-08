# Serviço de Gerenciamento de Arquivos - Audicore

Sistema completo para upload, download e gerenciamento de arquivos no Azure Blob Storage com integração Power Apps.

## Visão Geral

Este serviço fornece uma API REST completa para gerenciar arquivos no Azure Blob Storage, com armazenamento de metadados no Azure SQL Database e integração nativa com Power Apps.

### Funcionalidades

- ✅ Upload de arquivos (base64 ou multipart/form-data)
- ✅ Download direto ou via URL temporária (SAS token)
- ✅ Armazenamento de metadados no Azure SQL Database
- ✅ Organização por pastas
- ✅ Listagem com paginação
- ✅ Soft delete (marca como inativo)
- ✅ Integração completa com Power Apps
- ✅ Suporte para múltiplos tipos de arquivo

## Estrutura do Projeto

```
servico-gerenciamento-arquivos-audicore/
├── src/                          # Código fonte
│   ├── azure_storage_manager.py  # Gerenciador de storage
│   ├── api_storage_routes.py     # Endpoints da API
│   └── exemplo_integracao_api.py # Exemplo de integração
├── database/                     # Scripts de banco de dados
│   └── create_table_arquivos.sql # Criação da tabela
├── docs/                         # Documentação
│   ├── DOCUMENTACAO_STORAGE_API.md
│   └── POWER_APPS_EXEMPLOS.md
├── tests/                        # Testes
│   └── testar_storage_api.py
├── config/                       # Configurações
│   └── .env.storage.example
├── README.md                     # Este arquivo
└── requirements.txt              # Dependências Python
```

## Requisitos

- Python 3.8+
- Azure Storage Account
- Azure SQL Database
- Flask API (ou aplicação compatível)

## Instalação

### 1. Clonar/Copiar o Projeto

```bash
cd ~/Desktop/AudicoreCode/servico-gerenciamento-arquivos-audicore
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar Banco de Dados

Execute o script SQL para criar a tabela de metadados:

```bash
# Via Azure Data Studio, Azure Portal ou sqlcmd
sqlcmd -S seu-servidor.database.windows.net -d seu-banco -U usuario -P senha -i database/create_table_arquivos.sql
```

### 4. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp config/.env.storage.example .env

# Editar o arquivo .env com suas credenciais
# - AZURE_STORAGE_ACCOUNT
# - AZURE_STORAGE_KEY
# - AZURE_STORAGE_CONTAINER
# - SQL_CONNECTION_STRING
```

### 5. Testar Configuração

```bash
python tests/testar_storage_api.py
```

## Uso Rápido

### Integrar na API Flask

```python
from flask import Flask
from src.api_storage_routes import register_storage_routes

app = Flask(__name__)

# Registrar rotas de storage
register_storage_routes(app)

if __name__ == '__main__':
    app.run()
```

### Usar Diretamente no Código

```python
from src.azure_storage_manager import AzureStorageManager
import os

# Inicializar
storage = AzureStorageManager(
    storage_account=os.getenv('AZURE_STORAGE_ACCOUNT'),
    storage_key=os.getenv('AZURE_STORAGE_KEY'),
    container_name=os.getenv('AZURE_STORAGE_CONTAINER'),
    sql_connection_string=os.getenv('SQL_CONNECTION_STRING')
)

# Upload
with open('documento.pdf', 'rb') as f:
    resultado = storage.upload_file(
        file_content=f.read(),
        original_filename='documento.pdf',
        content_type='application/pdf',
        upload_user='usuario@email.com'
    )

print(resultado)
```

## Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/arquivos/upload` | Upload de arquivo |
| GET | `/api/arquivos/download/{id}` | Download ou URL temporária |
| GET | `/api/arquivos/info/{id}` | Informações do arquivo |
| GET | `/api/arquivos/listar` | Listar arquivos |
| DELETE | `/api/arquivos/deletar/{id}` | Deletar arquivo |
| GET | `/api/arquivos/health` | Health check |

## Integração com Power Apps

Consulte a documentação completa em:
- `docs/POWER_APPS_EXEMPLOS.md` - Exemplos práticos de integração

### Exemplo Rápido - Upload no Power Apps

```powerapps
// OnSelect do botão de upload
APIStorage.UploadArquivo({
    arquivo: Last(FirstN(Split(JSON(UploadControl.Media, JSONFormat.IncludeBinaryData), ","), 2)).Result,
    nome_arquivo: UploadControl.Media.FileName,
    tipo_conteudo: UploadControl.Media.ContentType,
    usuario: User().Email,
    pasta: "documentos"
})
```

## Documentação

- **Documentação da API**: `docs/DOCUMENTACAO_STORAGE_API.md`
- **Exemplos Power Apps**: `docs/POWER_APPS_EXEMPLOS.md`
- **Exemplo de Integração**: `src/exemplo_integracao_api.py`

## Configuração do Azure

### Container Blob Storage

Container criado: **arquivos**
Storage Account: **staudicoreapiprod**

### Tabela SQL

Tabela: **ArquivosStorage**
Campos principais:
- Id (UNIQUEIDENTIFIER)
- NomeOriginal (NVARCHAR)
- CaminhoBlob (NVARCHAR)
- UrlBlob (NVARCHAR)
- TamanhoBytes (BIGINT)
- DataUpload (DATETIME2)
- Ativo (BIT)

## Segurança

⚠️ **Importante**: Em produção, implemente:

1. Autenticação (JWT, Azure AD)
2. Validação de tipo de arquivo
3. Limite de tamanho
4. Rate limiting
5. Scan de vírus (Azure Defender)

## Testes

Execute os testes automatizados:

```bash
python tests/testar_storage_api.py
```

Os testes verificam:
- ✅ Dependências instaladas
- ✅ Variáveis de ambiente configuradas
- ✅ Conexão com Azure Storage
- ✅ Conexão com SQL Server
- ✅ Upload/Download funcional

## Deploy

### Azure App Service

```bash
# Deploy via Azure CLI
az webapp up \
  --name sua-api \
  --resource-group seu-rg \
  --runtime PYTHON:3.11

# Configurar variáveis de ambiente no portal
az webapp config appsettings set \
  --name sua-api \
  --resource-group seu-rg \
  --settings \
    AZURE_STORAGE_ACCOUNT=staudicoreapiprod \
    AZURE_STORAGE_KEY=sua_chave \
    AZURE_STORAGE_CONTAINER=arquivos \
    SQL_CONNECTION_STRING=sua_connection_string
```

## Troubleshooting

### Erro: "Permission denied"
- Verifique as permissões da Storage Account Key
- Verifique se o container existe

### Erro: "Connection timeout" (SQL)
- Verifique regras de firewall do Azure SQL
- Verifique a string de conexão

### Erro: "Invalid base64"
- Verifique se está removendo o prefixo `data:mime;base64,`

Consulte a documentação completa para mais detalhes.

## Suporte

Para dúvidas ou problemas:
- Consulte a documentação em `docs/`
- Revise os exemplos em `src/exemplo_integracao_api.py`
- Execute os testes em `tests/testar_storage_api.py`

## Licença

Projeto interno Audicore.

## Autores

- Desenvolvido para Audicore
- Data: Janeiro 2025

---

**Status do Projeto**: ✅ Pronto para uso

**Última Atualização**: 2025-01-08
