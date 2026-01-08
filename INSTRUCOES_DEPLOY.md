# ✅ App Service Criado com Sucesso!

## Status

- ✅ App Service Plan criado: `plan-audicore-storage`
- ✅ Web App criado: `audicore-storage-api`
- ✅ Variáveis de ambiente configuradas
- ✅ Publish profile obtido e copiado para área de transferência
- ⏳ **Falta**: Adicionar secret no GitHub para deploy automático

## URL da API

**Produção**: https://audicore-storage-api.azurewebsites.net

## Passo Final: Configurar GitHub Actions

### 1. Adicionar Secret no GitHub

O **publish profile** já está copiado na sua área de transferência!

Agora faça:

1. Acesse: https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore/settings/secrets/actions

2. Clique em **"New repository secret"**

3. Preencha:
   - **Name**: `AZURE_WEBAPP_PUBLISH_PROFILE`
   - **Value**: Cole (Cmd+V) o conteúdo que está na área de transferência

4. Clique em **"Add secret"**

### 2. Acionar o Deploy

Após adicionar o secret, o deploy pode ser feito de duas formas:

#### Opção A: Manual (pelo GitHub)

1. Acesse: https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore/actions
2. Clique em "Deploy to Azure App Service"
3. Clique em "Run workflow" → "Run workflow"
4. Aguarde 2-3 minutos

#### Opção B: Automático (push no repositório)

```bash
cd ~/Desktop/AudicoreCode/servico-gerenciamento-arquivos-audicore

# Fazer qualquer alteração
echo "# API em produção" >> README.md

git add README.md
git commit -m "chore: trigger deploy to production"
git push
```

O deploy será acionado automaticamente!

### 3. Acompanhar o Deploy

Acompanhe o progresso em:
https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore/actions

Aguarde até ver: ✅ (verde) - Deploy concluído com sucesso

### 4. Testar a API

Após o deploy concluir, teste:

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

## Configurações Aplicadas

| Variável | Valor |
|----------|-------|
| AZURE_STORAGE_ACCOUNT | staudicoreapiprod |
| AZURE_STORAGE_CONTAINER | arquivos |
| SQL_CONNECTION_STRING | sql-dataverse-audicore (DataverseAnalytics) |
| FLASK_ENV | production |

## Próximos Passos (Após Deploy)

### 1. Criar Tabela no Banco de Dados

Execute o script SQL:

```bash
# Via Azure Data Studio ou portal
# Arquivo: database/create_table_arquivos.sql
```

Ou execute direto:

```bash
sqlcmd -S sql-dataverse-audicore.database.windows.net \
  -d DataverseAnalytics \
  -U sqladmin \
  -P Admin@2024 \
  -i database/create_table_arquivos.sql
```

### 2. Testar Endpoints

```bash
# Upload (teste com arquivo base64)
curl -X POST https://audicore-storage-api.azurewebsites.net/api/arquivos/upload \
  -H "Content-Type: application/json" \
  -d '{
    "arquivo": "VGVzdGUgZGUgYXJxdWl2bw==",
    "nome_arquivo": "teste.txt",
    "tipo_conteudo": "text/plain",
    "usuario": "teste@audicore.com"
  }'

# Listar
curl https://audicore-storage-api.azurewebsites.net/api/arquivos/listar
```

### 3. Configurar Power Apps

Consulte: `docs/POWER_APPS_EXEMPLOS.md`

1. Criar Custom Connector
2. Configurar URL base: `https://audicore-storage-api.azurewebsites.net`
3. Importar as ações (Upload, Download, Listar)
4. Testar no Power Apps

## Informações Importantes

### Resource Group
`rg-audicore-prod`

### Custo Estimado
- App Service B1: ~$13/mês
- Storage: ~$2/mês
- SQL: Já existente
- **Total novo**: ~$15/mês

### URLs Úteis

- **API Produção**: https://audicore-storage-api.azurewebsites.net
- **Portal Azure**: https://portal.azure.com
- **App Service**: https://portal.azure.com/#resource/subscriptions/864502da-c884-4d97-9f89-c57619360894/resourceGroups/rg-audicore-prod/providers/Microsoft.Web/sites/audicore-storage-api
- **GitHub Actions**: https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore/actions
- **Repositório**: https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore

### Logs em Tempo Real

```bash
# Ver logs da aplicação
az webapp log tail \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod
```

## Troubleshooting

### App não inicia após deploy

1. Verifique os logs:
```bash
az webapp log tail --name audicore-storage-api --resource-group rg-audicore-prod
```

2. Verifique variáveis de ambiente:
```bash
az webapp config appsettings list \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --output table
```

### Erro 500 na API

- Verifique se a tabela `ArquivosStorage` existe no banco
- Verifique se a connection string do SQL está correta
- Verifique se a Storage Account Key está correta

### Deploy falha no GitHub Actions

- Verifique se o secret `AZURE_WEBAPP_PUBLISH_PROFILE` foi adicionado corretamente
- Verifique os logs no GitHub Actions

## Suporte

- Documentação completa: `README.md`
- Exemplos Power Apps: `docs/POWER_APPS_EXEMPLOS.md`
- Deploy detalhado: `DEPLOY.md`

---

**Status**: ✅ App Service configurado e pronto para receber deploy

**Próximo passo**: Adicionar secret no GitHub (1 minuto)
