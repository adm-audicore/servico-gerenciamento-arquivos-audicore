# API de Gerenciamento de Arquivos - Azure Blob Storage

Sistema completo para upload, download e gerenciamento de arquivos no Azure Blob Storage com integração Power Apps.

## Arquitetura da Solução

```
Power Apps → API Flask → Azure Blob Storage
                ↓
           Azure SQL Database (metadados)
```

## Componentes

1. **azure_storage_manager.py** - Classe principal para gerenciar operações de storage
2. **api_storage_routes.py** - Endpoints Flask para a API REST
3. **create_table_arquivos.sql** - Script para criar tabela de metadados

## Configuração

### 1. Instalar Dependências

```bash
pip install azure-storage-blob pyodbc flask werkzeug
```

### 2. Variáveis de Ambiente

Configurar no arquivo `.env`:

```bash
# Azure Storage
AZURE_STORAGE_ACCOUNT=staudicoreapiprod
AZURE_STORAGE_KEY=sua_chave_aqui
AZURE_STORAGE_CONTAINER=arquivos

# SQL Server
SQL_CONNECTION_STRING=Driver={ODBC Driver 18 for SQL Server};Server=tcp:seu-servidor.database.windows.net,1433;Database=seu-banco;Uid=usuario;Pwd=senha;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
```

### 3. Criar Tabela no Banco de Dados

Execute o script `create_table_arquivos.sql` no seu Azure SQL Database.

### 4. Integrar na sua API Flask

```python
from flask import Flask
from api_storage_routes import register_storage_routes

app = Flask(__name__)

# Registrar rotas de storage
register_storage_routes(app)

if __name__ == '__main__':
    app.run()
```

## Endpoints da API

### 1. Upload de Arquivo

**POST** `/api/arquivos/upload`

#### Formato JSON (recomendado para Power Apps):

```json
{
  "arquivo": "base64_string_do_arquivo",
  "nome_arquivo": "documento.pdf",
  "tipo_conteudo": "application/pdf",
  "usuario": "usuario@email.com",
  "pasta": "documentos_medicos"
}
```

#### Resposta de Sucesso:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "nome_original": "documento.pdf",
  "nome_armazenado": "550e8400-e29b-41d4-a716-446655440000.pdf",
  "caminho_blob": "documentos_medicos/550e8400-e29b-41d4-a716-446655440000.pdf",
  "url": "https://staudicoreapiprod.blob.core.windows.net/arquivos/...",
  "tamanho_bytes": 245678,
  "tipo_conteudo": "application/pdf",
  "sucesso": true,
  "mensagem": "Arquivo enviado com sucesso"
}
```

### 2. Download de Arquivo

**GET** `/api/arquivos/download/{file_id}`

#### Opção 1: Download Direto
```
GET /api/arquivos/download/123e4567-e89b-12d3-a456-426614174000
```
Retorna o arquivo binário para download.

#### Opção 2: Obter URL Temporária (recomendado para Power Apps)
```
GET /api/arquivos/download/123e4567-e89b-12d3-a456-426614174000?url_apenas=true&validade_horas=2
```

Resposta:
```json
{
  "sucesso": true,
  "url_download": "https://staudicoreapiprod.blob.core.windows.net/arquivos/...?se=2025-01-08T14:00:00Z&sp=r&sv=2021-06-08&sr=b&sig=...",
  "nome_original": "documento.pdf",
  "validade_horas": 2,
  "expira_em": "2025-01-08T14:00:00"
}
```

### 3. Informações do Arquivo

**GET** `/api/arquivos/info/{file_id}`

```
GET /api/arquivos/info/123e4567-e89b-12d3-a456-426614174000
```

Resposta:
```json
{
  "sucesso": true,
  "arquivo": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "nome_original": "documento.pdf",
    "tamanho_bytes": 245678,
    "tipo_conteudo": "application/pdf",
    "data_upload": "2025-01-08T12:00:00",
    "upload_por": "usuario@email.com",
    "container": "arquivos",
    "storage_account": "staudicoreapiprod"
  }
}
```

### 4. Listar Arquivos

**GET** `/api/arquivos/listar`

Parâmetros de query:
- `limite`: Número de registros (padrão: 100)
- `offset`: Offset para paginação (padrão: 0)
- `pasta`: Filtrar por pasta

```
GET /api/arquivos/listar?limite=50&offset=0&pasta=documentos_medicos
```

### 5. Deletar Arquivo

**DELETE** `/api/arquivos/deletar/{file_id}`

```
DELETE /api/arquivos/deletar/123e4567-e89b-12d3-a456-426614174000?permanente=false
```

- `permanente=false`: Soft delete (marca como inativo)
- `permanente=true`: Deleta permanentemente do storage

## Integração com Power Apps

### Upload de Arquivo no Power Apps

1. **Adicionar controle de anexo**:
   - Adicione um controle `AddMediaButton` ou `Attachments`
   - Nome do controle: `UploadControl`

2. **Botão para enviar**:

```powerfx
// OnSelect do botão de upload
With(
    {
        fileContent: JSON(
            UploadControl.Media,
            JSONFormat.IncludeBinaryData
        ),
        fileName: UploadControl.Media.FileName,
        fileType: UploadControl.Media.ContentType
    },
    Set(
        uploadResult,
        With(
            {
                response: 'SuaAPI'.UploadArquivo(
                    {
                        arquivo: First(Split(fileContent, ",")).Value,
                        nome_arquivo: fileName,
                        tipo_conteudo: fileType,
                        usuario: User().Email,
                        pasta: "documentos_medicos"
                    }
                )
            },
            response
        )
    )
)

// Mostrar mensagem de sucesso/erro
If(
    uploadResult.sucesso,
    Notify("Arquivo enviado: " & uploadResult.nome_original, NotificationType.Success),
    Notify("Erro: " & uploadResult.mensagem, NotificationType.Error)
)
```

### Download de Arquivo no Power Apps

1. **Obter URL temporária**:

```powerx
// OnSelect do botão de download
Set(
    downloadInfo,
    'SuaAPI'.DownloadArquivo(
        fileId,
        {url_apenas: true, validade_horas: 1}
    )
)

// Abrir arquivo no navegador
If(
    downloadInfo.sucesso,
    Launch(downloadInfo.url_download),
    Notify("Erro ao obter arquivo: " & downloadInfo.mensagem, NotificationType.Error)
)
```

2. **Exibir arquivo em Image/PDF Viewer**:

```powerx
// Para imagens
Set(imgUrl, downloadInfo.url_download)
// Vincular à propriedade Image de um controle Image

// Para PDFs
Set(pdfUrl, downloadInfo.url_download)
// Vincular à propriedade Document de um controle PDF viewer
```

### Configurar Conexão Personalizada no Power Apps

1. **Criar Custom Connector**:
   - No Power Apps, vá em Data → Custom Connectors → New custom connector
   - Importe OpenAPI ou configure manualmente

2. **Configuração básica**:
   - Host: `sua-api.azurewebsites.net`
   - Base URL: `/api/arquivos`

3. **Ações**:
   - UploadArquivo (POST /upload)
   - DownloadArquivo (GET /download/{id})
   - ListarArquivos (GET /listar)
   - DeletarArquivo (DELETE /deletar/{id})

## Segurança

### Recomendações:

1. **Autenticação**: Adicionar autenticação JWT ou Azure AD
2. **Validação de tipo de arquivo**: Implementar whitelist de extensões permitidas
3. **Limite de tamanho**: Configurar tamanho máximo de arquivo
4. **Rate limiting**: Implementar limite de requisições por usuário
5. **Scan de vírus**: Integrar com Azure Defender for Storage

### Exemplo de validação de tipo:

```python
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xls', '.xlsx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def validar_arquivo(filename, file_size):
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Tipo de arquivo não permitido. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}"

    if file_size > MAX_FILE_SIZE:
        return False, f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE / 1024 / 1024}MB"

    return True, "OK"
```

## Monitoramento

### Logs importantes:

1. Operações de upload/download
2. Erros de acesso ao storage
3. Erros de banco de dados
4. Tempo de resposta das operações

### Exemplo com Azure Application Insights:

```python
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string='InstrumentationKey=your-key'
))

# Usar nos endpoints
logger.info(f"Upload realizado: {file_id}")
logger.error(f"Erro no upload: {str(e)}")
```

## Testes

### Teste com cURL:

```bash
# Upload
curl -X POST https://sua-api.azurewebsites.net/api/arquivos/upload \
  -H "Content-Type: application/json" \
  -d '{
    "arquivo": "'"$(base64 -i arquivo.pdf)"'",
    "nome_arquivo": "arquivo.pdf",
    "tipo_conteudo": "application/pdf",
    "usuario": "teste@email.com"
  }'

# Download (URL temporária)
curl -X GET "https://sua-api.azurewebsites.net/api/arquivos/download/{file_id}?url_apenas=true"

# Listar
curl -X GET "https://sua-api.azurewebsites.net/api/arquivos/listar?limite=10"
```

## Troubleshooting

### Erro: "Arquivo não encontrado no storage"
- Verificar se o blob existe no container
- Verificar permissões da Storage Account Key

### Erro: "Conexão com banco de dados falhou"
- Verificar SQL_CONNECTION_STRING
- Verificar regras de firewall do Azure SQL

### Erro: "Permission denied" ao criar container
- Verificar permissões da Storage Account Key
- Verificar se o usuário tem permissão de Storage Blob Data Contributor

## Custos Azure

### Estimativa mensal (baseado em uso médio):

- **Blob Storage**:
  - 100 GB: ~$2.00
  - 10.000 transações: ~$0.20

- **SQL Database**:
  - Basic tier: ~$5.00

- **App Service**:
  - Depende do plan escolhido

**Total estimado**: ~$7-20/mês (uso leve)

## Próximos Passos

1. Implementar autenticação (Azure AD / JWT)
2. Adicionar suporte para arquivos grandes (chunk upload)
3. Implementar versionamento de arquivos
4. Adicionar thumbnail generation para imagens
5. Implementar busca full-text nos metadados
6. Adicionar suporte para compartilhamento de arquivos (URLs públicas temporárias)

## Suporte

Para dúvidas ou problemas, consulte:
- [Documentação Azure Blob Storage](https://docs.microsoft.com/azure/storage/blobs/)
- [Power Apps Custom Connectors](https://docs.microsoft.com/connectors/custom-connectors/)
