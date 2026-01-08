# Setup Rápido - Deploy Automático

O repositório está no GitHub mas falta configurar o deploy automático. Siga estes passos:

## Passo 1: Criar Azure App Service

Execute estes comandos no terminal:

```bash
# 1. Criar App Service Plan (se não existir)
az appservice plan create \
  --name plan-audicore-storage \
  --resource-group rg-audicore-prod \
  --sku B1 \
  --is-linux

# 2. Criar Web App
az webapp create \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --plan plan-audicore-storage \
  --runtime "PYTHON:3.11"
```

**Nota**: Se quiser usar outro resource group, substitua `rg-audicore-prod` pelo nome desejado.

## Passo 2: Configurar Variáveis de Ambiente

```bash
az webapp config appsettings set \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --settings \
    AZURE_STORAGE_ACCOUNT=staudicoreapiprod \
    AZURE_STORAGE_KEY="SUA_CHAVE_DO_AZURE_STORAGE_AQUI" \
    AZURE_STORAGE_CONTAINER=arquivos \
    SQL_CONNECTION_STRING="SEU_SQL_CONNECTION_STRING_AQUI" \
    FLASK_ENV=production \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

**IMPORTANTE**: Substitua `SQL_CONNECTION_STRING` pela sua string de conexão real.

## Passo 3: Obter Publish Profile

```bash
az webapp deployment list-publishing-profiles \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --xml > publish-profile.xml

# Copiar conteúdo
cat publish-profile.xml | pbcopy  # macOS
# ou
cat publish-profile.xml  # Copiar manualmente
```

## Passo 4: Adicionar Secret no GitHub

1. Acesse: https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore/settings/secrets/actions

2. Clique em **"New repository secret"**

3. Preencha:
   - **Name**: `AZURE_WEBAPP_PUBLISH_PROFILE`
   - **Value**: Cole o conteúdo do arquivo `publish-profile.xml`

4. Clique em **"Add secret"**

## Passo 5: Atualizar Nome do App no Workflow (se necessário)

Se você usou um nome diferente de `audicore-storage-api`, edite o arquivo:
`.github/workflows/azure-deploy.yml`

E altere a linha:
```yaml
AZURE_WEBAPP_NAME: 'audicore-storage-api'  # ← Seu nome aqui
```

Depois, faça commit e push:
```bash
git add .github/workflows/azure-deploy.yml
git commit -m "chore: atualizar nome do app service"
git push
```

## Passo 6: Acionar Deploy

O deploy acontece automaticamente quando você faz push para `main`. Para forçar um novo deploy:

```bash
# Fazer qualquer alteração
echo "# Deploy test" >> README.md
git add README.md
git commit -m "chore: trigger deploy"
git push
```

Ou use o botão **"Run workflow"** em:
https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore/actions

## Passo 7: Verificar Deploy

1. Acompanhe o deploy em: https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore/actions

2. Após concluído, teste a API:
```bash
curl https://audicore-storage-api.azurewebsites.net/api/arquivos/health
```

Deve retornar:
```json
{
  "sucesso": true,
  "mensagem": "Serviço de arquivos funcionando",
  "storage_account": "staudicoreapiprod",
  "container": "arquivos"
}
```

## Solução Rápida: Deploy Manual (se GitHub Actions não funcionar)

Se preferir fazer deploy manual sem GitHub Actions:

```bash
cd ~/Desktop/AudicoreCode/servico-gerenciamento-arquivos-audicore

# Criar pacote zip
zip -r deploy.zip src/ requirements.txt

# Deploy via Azure CLI
az webapp deployment source config-zip \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod \
  --src deploy.zip

# Limpar
rm deploy.zip
```

## Troubleshooting

### Erro: Resource group não encontrado

Crie o resource group primeiro:
```bash
az group create --name rg-audicore-prod --location brazilsouth
```

### Erro: Nome do app já existe

Escolha outro nome único:
```bash
az webapp create \
  --name audicore-storage-api-2025 \
  --resource-group rg-audicore-prod \
  --plan plan-audicore-storage \
  --runtime "PYTHON:3.11"
```

### App não inicia

Verifique os logs:
```bash
az webapp log tail \
  --name audicore-storage-api \
  --resource-group rg-audicore-prod
```

## Próximos Passos

Após o deploy funcionar:

1. ✅ Executar script SQL: `database/create_table_arquivos.sql`
2. ✅ Testar endpoints da API
3. ✅ Configurar Power Apps (veja `docs/POWER_APPS_EXEMPLOS.md`)
4. ⏭️ Configurar autenticação (opcional)
5. ⏭️ Configurar Application Insights (opcional)

## URLs Úteis

- **Repositório**: https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore
- **Actions**: https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore/actions
- **Secrets**: https://github.com/adm-audicore/servico-gerenciamento-arquivos-audicore/settings/secrets/actions
- **Azure Portal**: https://portal.azure.com

---

**Tempo estimado**: 10-15 minutos

Para mais detalhes, consulte `DEPLOY.md`.
