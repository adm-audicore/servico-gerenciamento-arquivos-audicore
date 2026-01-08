# Guia de Deploy - Serviço de Gerenciamento de Arquivos

Este guia explica como fazer o deploy do serviço no Azure App Service com deploy automático via GitHub Actions.

## Pré-requisitos

- Conta no Azure
- Repositório GitHub: `https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore`
- Azure CLI instalado (opcional)
- Storage Account configurado: `staudicoreapiprod`
- Azure SQL Database configurado

## Passo 1: Criar Azure App Service

### Opção A: Via Azure Portal

1. Acesse o [Azure Portal](https://portal.azure.com)
2. Clique em **"Create a resource"** → **"Web App"**
3. Preencha os campos:
   - **Resource Group**: `rg-audicore-prod` (ou criar novo)
   - **Name**: `audicore-storage-api` (ou nome desejado)
   - **Publish**: `Code`
   - **Runtime stack**: `Python 3.11`
   - **Operating System**: `Linux`
   - **Region**: `Brazil South` (ou região mais próxima)
   - **Plan**: Escolha o plan adequado (B1, S1, etc)
4. Clique em **"Review + Create"** → **"Create"**

### Opção B: Via Azure CLI

```bash
# Login no Azure
az login

# Criar Resource Group (se não existir)
az group create --name rg-audicore-prod --location brazilsouth

# Criar App Service Plan
az appservice plan create \
  --name plan-audicore-storage \
  --resource-group rg-audicore-prod \
  --sku B1 \
  --is-linux

# Criar Web App
az webapp create \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --plan plan-audicore-storage \
  --runtime "PYTHON:3.11"
```

## Passo 2: Configurar Variáveis de Ambiente no Azure

### Via Azure Portal

1. Acesse seu App Service no portal
2. Vá em **"Configuration"** → **"Application settings"**
3. Adicione as seguintes variáveis:

| Nome | Valor |
|------|-------|
| `AZURE_STORAGE_ACCOUNT` | `staudicoreapiprod` |
| `AZURE_STORAGE_KEY` | `[sua chave do storage]` |
| `AZURE_STORAGE_CONTAINER` | `arquivos` |
| `SQL_CONNECTION_STRING` | `[sua connection string]` |
| `FLASK_ENV` | `production` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |

4. Clique em **"Save"**

### Via Azure CLI

```bash
az webapp config appsettings set \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --settings \
    AZURE_STORAGE_ACCOUNT=staudicoreapiprod \
    AZURE_STORAGE_KEY="sua_chave" \
    AZURE_STORAGE_CONTAINER=arquivos \
    SQL_CONNECTION_STRING="sua_connection_string" \
    FLASK_ENV=production \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

### Obter Storage Key

```bash
az storage account keys list \
  --account-name staudicoreapiprod \
  --resource-group rg-audicore-prod \
  --query '[0].value' \
  --output tsv
```

## Passo 3: Configurar GitHub Actions

### 3.1 Obter Publish Profile

#### Via Azure Portal

1. Acesse seu App Service
2. Clique em **"Get publish profile"** no topo
3. Salve o arquivo XML que será baixado
4. Copie todo o conteúdo do arquivo

#### Via Azure CLI

```bash
az webapp deployment list-publishing-profiles \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --xml
```

### 3.2 Adicionar Secret no GitHub

1. Acesse: `https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore/settings/secrets/actions`
2. Clique em **"New repository secret"**
3. Preencha:
   - **Name**: `AZURE_WEBAPP_PUBLISH_PROFILE`
   - **Value**: Cole o conteúdo do publish profile (XML completo)
4. Clique em **"Add secret"**

### 3.3 Configurar Nome do App no Workflow

Edite o arquivo `.github/workflows/azure-deploy.yml` e atualize:

```yaml
env:
  AZURE_WEBAPP_NAME: 'audicore-storage-api'  # Seu nome do App Service
```

## Passo 4: Fazer Push para GitHub

Agora, quando você fizer push para o repositório, o deploy será automático:

```bash
# O código já está no repositório, então qualquer push futuro acionará o deploy

git add .
git commit -m "feat: atualização do serviço"
git push origin main
```

### Monitorar Deploy

1. Acesse: `https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore/actions`
2. Você verá o workflow rodando
3. Clique no workflow para ver os logs

## Passo 5: Verificar Deploy

### Testar Endpoint

```bash
# Health check
curl https://audicore-storage-api.azurewebsites.net/api/arquivos/health

# Deve retornar:
{
  "sucesso": true,
  "mensagem": "Serviço de arquivos funcionando",
  "storage_account": "staudicoreapiprod",
  "container": "arquivos"
}
```

### Ver Logs no Azure

```bash
# Via CLI
az webapp log tail \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod

# Ou acesse o portal: App Service → Log stream
```

## Configuração Adicional

### Configurar Custom Domain (Opcional)

```bash
# Mapear domínio customizado
az webapp config hostname add \
  --webapp-name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --hostname storage.audicore.com.br

# Configurar SSL
az webapp config ssl bind \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --certificate-thumbprint [thumbprint] \
  --ssl-type SNI
```

### Configurar CORS (se necessário)

```bash
az webapp cors add \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --allowed-origins https://apps.powerapps.com https://make.powerapps.com
```

### Escalar Aplicação

```bash
# Escalar verticalmente (mudar tier)
az appservice plan update \
  --name plan-audicore-storage \
  --resource-group rg-audicore-prod \
  --sku S1

# Escalar horizontalmente (múltiplas instâncias)
az appservice plan update \
  --name plan-audicore-storage \
  --resource-group rg-audicore-prod \
  --number-of-workers 3
```

## Deploy Manual (Alternativa)

Se preferir fazer deploy manual sem GitHub Actions:

```bash
# Via Azure CLI
cd ~/Desktop/AudicoreCode/servico-gerenciamento-arquivos-audicore

# Criar pacote
zip -r deploy.zip src/ requirements.txt

# Deploy
az webapp deployment source config-zip \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --src deploy.zip

# Limpar
rm deploy.zip
```

## Troubleshooting

### Deploy Falha

1. Verifique os logs no GitHub Actions
2. Verifique se o publish profile está correto
3. Verifique se o nome do app está correto no workflow

### App Não Inicia

1. Verifique as variáveis de ambiente no Azure
2. Verifique os logs: `az webapp log tail`
3. Verifique se as dependências estão corretas em requirements.txt

### Erros de Conexão com Storage/SQL

1. Verifique se as credenciais estão corretas
2. Verifique firewall do SQL Server
3. Verifique se o App Service tem acesso à rede

### Timeout nos Requests

Configure timeout maior:

```bash
az webapp config set \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 app:app"
```

## Monitoramento

### Application Insights (Recomendado)

```bash
# Criar Application Insights
az monitor app-insights component create \
  --app audicore-storage-insights \
  --location brazilsouth \
  --resource-group rg-audicore-prod

# Vincular ao App Service
az webapp config appsettings set \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="[connection string]"
```

### Métricas Importantes

- Tempo de resposta
- Taxa de erro
- Uso de CPU/Memória
- Número de requests

## Backup e Recuperação

### Configurar Backup Automático

No Azure Portal:
1. App Service → **Backups**
2. Configure backup automático
3. Escolha Storage Account para backups

## Custos Estimados

- **App Service B1**: ~$13/mês
- **Storage Account**: ~$2/mês (100GB)
- **SQL Database Basic**: ~$5/mês
- **Application Insights**: ~$2-5/mês

**Total**: ~$22-25/mês

## Próximos Passos

1. ✅ Deploy realizado
2. ⏭️ Configurar autenticação (Azure AD/JWT)
3. ⏭️ Implementar rate limiting
4. ⏭️ Configurar Application Insights
5. ⏭️ Configurar alertas de erro
6. ⏭️ Integrar com Power Apps

## Suporte

- Documentação: `README.md`
- Repositório: https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore
- Azure Docs: https://docs.microsoft.com/azure/app-service/
