# Exemplos Práticos - Power Apps + API Storage

Guia completo com exemplos práticos de como usar a API de Storage no Power Apps.

## Índice

1. [Configuração Inicial](#configuração-inicial)
2. [Upload de Arquivo](#upload-de-arquivo)
3. [Download de Arquivo](#download-de-arquivo)
4. [Listar Arquivos](#listar-arquivos)
5. [Galeria de Arquivos](#galeria-de-arquivos)
6. [Upload com Progress Bar](#upload-com-progress-bar)
7. [Formulário Completo](#formulário-completo)

---

## Configuração Inicial

### 1. Criar Custom Connector

1. No Power Apps Studio, vá em **Data** → **Custom connectors** → **+ New custom connector**
2. Escolha **Create from blank**
3. Nome: `APIStorage`

### 2. Configurar General

- **Host**: `sua-api.azurewebsites.net`
- **Base URL**: `/api/arquivos`

### 3. Adicionar Ações

#### Ação: UploadArquivo

- **Operação ID**: `UploadArquivo`
- **Visibility**: important
- **Method**: POST
- **URL**: `/upload`

**Request Body:**
```json
{
  "type": "object",
  "properties": {
    "arquivo": {
      "type": "string",
      "description": "Arquivo em base64"
    },
    "nome_arquivo": {
      "type": "string",
      "description": "Nome do arquivo"
    },
    "tipo_conteudo": {
      "type": "string",
      "description": "Tipo MIME"
    },
    "usuario": {
      "type": "string",
      "description": "Email do usuário"
    },
    "pasta": {
      "type": "string",
      "description": "Pasta no container"
    }
  },
  "required": ["arquivo", "nome_arquivo"]
}
```

#### Ação: DownloadArquivo

- **Operação ID**: `DownloadArquivo`
- **Method**: GET
- **URL**: `/download/{file_id}`

**Parameters:**
- `file_id` (path, required)
- `url_apenas` (query, optional, boolean)
- `validade_horas` (query, optional, integer)

#### Ação: ListarArquivos

- **Operação ID**: `ListarArquivos`
- **Method**: GET
- **URL**: `/listar`

**Parameters:**
- `limite` (query, optional, integer)
- `offset` (query, optional, integer)
- `pasta` (query, optional, string)

---

## Upload de Arquivo

### Exemplo 1: Upload Simples com AddMediaButton

```powerapps
// Screen: ScreenUpload

// Controles:
// - btnUpload: AddMediaButton (ou Attachments)
// - btnEnviar: Button
// - lblStatus: Label

// btnEnviar.OnSelect:
If(
    !IsBlank(btnUpload.Media),
    // Preparar dados do arquivo
    With(
        {
            arquivo: btnUpload.Media,
            nomeArquivo: btnUpload.Media.FileName,
            tipoArquivo: btnUpload.Media.ContentType
        },
        // Fazer upload
        Set(
            varUploadResult,
            APIStorage.UploadArquivo({
                arquivo: Last(
                    FirstN(
                        Split(
                            JSON(arquivo, JSONFormat.IncludeBinaryData),
                            ","
                        ),
                        2
                    )
                ).Result,
                nome_arquivo: nomeArquivo,
                tipo_conteudo: tipoArquivo,
                usuario: User().Email,
                pasta: "documentos"
            })
        );

        // Exibir resultado
        If(
            varUploadResult.sucesso,
            Notify("Arquivo enviado com sucesso!", NotificationType.Success);
            Set(varArquivoId, varUploadResult.id),
            Notify("Erro: " & varUploadResult.mensagem, NotificationType.Error)
        )
    ),
    Notify("Selecione um arquivo primeiro", NotificationType.Warning)
)

// lblStatus.Text:
If(
    !IsBlank(varUploadResult),
    If(
        varUploadResult.sucesso,
        "✓ Arquivo enviado: " & varUploadResult.nome_original &
        " (" & Round(varUploadResult.tamanho_bytes / 1024, 2) & " KB)",
        "✗ Erro: " & varUploadResult.mensagem
    ),
    "Nenhum arquivo enviado"
)
```

### Exemplo 2: Upload de Múltiplos Arquivos

```powerapps
// Screen: ScreenUploadMultiplo

// Controles:
// - attFiles: Attachments (AllowMultiple = true)
// - btnEnviarTodos: Button
// - galStatus: Gallery

// btnEnviarTodos.OnSelect:
Clear(colResultadosUpload);

ForAll(
    attFiles.Attachments,
    Collect(
        colResultadosUpload,
        {
            nome: DisplayName,
            resultado: APIStorage.UploadArquivo({
                arquivo: Last(
                    FirstN(
                        Split(
                            JSON(ThisRecord, JSONFormat.IncludeBinaryData),
                            ","
                        ),
                        2
                    )
                ).Result,
                nome_arquivo: DisplayName,
                tipo_conteudo: ContentType,
                usuario: User().Email,
                pasta: "documentos_multiplos"
            })
        }
    )
);

Notify(
    "Upload concluído: " &
    CountRows(Filter(colResultadosUpload, resultado.sucesso)) &
    " de " & CountRows(colResultadosUpload) & " arquivos",
    NotificationType.Success
)

// galStatus - Items:
colResultadosUpload

// galStatus - Template (Label):
If(
    ThisItem.resultado.sucesso,
    "✓ " & ThisItem.nome & " - Enviado",
    "✗ " & ThisItem.nome & " - " & ThisItem.resultado.mensagem
)
```

---

## Download de Arquivo

### Exemplo 1: Download/Visualização com URL Temporária

```powerapps
// Screen: ScreenDownload

// Controles:
// - txtFileId: Text Input
// - btnBaixar: Button
// - imgPreview: Image (para imagens)
// - pdfViewer: PDF Viewer (para PDFs)

// btnBaixar.OnSelect:
Set(
    varDownloadInfo,
    APIStorage.DownloadArquivo(
        txtFileId.Text,
        {
            url_apenas: true,
            validade_horas: 2
        }
    )
);

If(
    varDownloadInfo.sucesso,
    // Sucesso - decidir ação baseada no tipo
    If(
        StartsWith(varDownloadInfo.nome_original, ".jpg") ||
        StartsWith(varDownloadInfo.nome_original, ".png") ||
        StartsWith(varDownloadInfo.nome_original, ".jpeg"),
        // Exibir imagem
        Set(varImageUrl, varDownloadInfo.url_download);
        Notify("Imagem carregada", NotificationType.Success),

        StartsWith(varDownloadInfo.nome_original, ".pdf"),
        // Exibir PDF
        Set(varPdfUrl, varDownloadInfo.url_download);
        Notify("PDF carregado", NotificationType.Success),

        // Outros arquivos - abrir no navegador
        Launch(varDownloadInfo.url_download);
        Notify("Arquivo aberto", NotificationType.Success)
    ),
    // Erro
    Notify("Erro: " & varDownloadInfo.mensagem, NotificationType.Error)
)

// imgPreview.Image:
varImageUrl

// pdfViewer.Document:
varPdfUrl
```

### Exemplo 2: Download Direto

```powerapps
// btnDownloadDireto.OnSelect:
Launch(
    "https://sua-api.azurewebsites.net/api/arquivos/download/" &
    txtFileId.Text
)
```

---

## Listar Arquivos

### Exemplo 1: Lista Simples

```powerapps
// Screen: ScreenListar

// Controles:
// - galArquivos: Gallery (vertical)
// - btnCarregar: Button

// btnCarregar.OnSelect:
Set(
    varListaArquivos,
    APIStorage.ListarArquivos({
        limite: 50,
        offset: 0,
        pasta: ""
    })
);

If(
    varListaArquivos.sucesso,
    ClearCollect(colArquivos, varListaArquivos.arquivos);
    Notify(
        "Carregados " & varListaArquivos.total & " arquivos",
        NotificationType.Success
    ),
    Notify("Erro: " & varListaArquivos.mensagem, NotificationType.Error)
)

// galArquivos.Items:
colArquivos

// galArquivos - Template:
// - lblNome: Label
lblNome.Text = ThisItem.nome_original

// - lblTamanho: Label
lblTamanho.Text = Round(ThisItem.tamanho_bytes / 1024, 2) & " KB"

// - lblData: Label
lblData.Text = Text(
    DateTimeValue(ThisItem.data_upload),
    "dd/mm/yyyy hh:mm"
)

// - btnBaixar: Icon (Download)
btnBaixar.OnSelect =
    Set(varSelectedFileId, ThisItem.id);
    Navigate(ScreenDownload)
```

### Exemplo 2: Lista com Paginação

```powerapps
// Variáveis:
// - varPagina: número da página atual
// - varTamanhoPagina: 20 registros por página

// btnProxima.OnSelect:
Set(varPagina, varPagina + 1);
Set(
    varListaArquivos,
    APIStorage.ListarArquivos({
        limite: varTamanhoPagina,
        offset: varPagina * varTamanhoPagina,
        pasta: ""
    })
);
ClearCollect(colArquivos, varListaArquivos.arquivos)

// btnAnterior.OnSelect:
If(
    varPagina > 0,
    Set(varPagina, varPagina - 1);
    Set(
        varListaArquivos,
        APIStorage.ListarArquivos({
            limite: varTamanhoPagina,
            offset: varPagina * varTamanhoPagina,
            pasta: ""
        })
    );
    ClearCollect(colArquivos, varListaArquivos.arquivos)
)

// lblPagina.Text:
"Página " & (varPagina + 1)
```

---

## Galeria de Arquivos

### Exemplo Completo com Upload e Visualização

```powerapps
// Screen: ScreenGaleria

// OnVisible:
// Carregar arquivos
Set(
    varListaArquivos,
    APIStorage.ListarArquivos({limite: 100, offset: 0})
);
ClearCollect(colArquivos, varListaArquivos.arquivos)

// Controles:
// - galArquivos: Gallery (flexible height, wrap)
// - btnNovoArquivo: Button
// - containerUpload: Container (visible = varModoUpload)

// galArquivos.Items:
colArquivos

// galArquivos.Template:
With(
    {
        ehImagem: ThisItem.tipo_conteudo in [
            "image/jpeg",
            "image/png",
            "image/jpg"
        ]
    },

    // Container com:
    // 1. Imagem/Ícone
    If(
        ehImagem,
        // Carregar thumbnail (você pode criar uma API para isso)
        Image(imgUrl),
        // Mostrar ícone baseado no tipo
        Icon.Document
    );

    // 2. Nome do arquivo
    Label(ThisItem.nome_original);

    // 3. Informações
    Label(
        Round(ThisItem.tamanho_bytes / 1024, 2) & " KB • " &
        Text(DateTimeValue(ThisItem.data_upload), "dd/mm")
    );

    // 4. Botões de ação
    Icon.Download -> OnSelect:
        Set(
            varDownloadUrl,
            APIStorage.DownloadArquivo(
                ThisItem.id,
                {url_apenas: true}
            ).url_download
        );
        Launch(varDownloadUrl)
)
```

---

## Upload com Progress Bar

```powerapps
// Note: Power Apps não suporta progress nativo para upload
// Esta é uma simulação visual

// btnUpload.OnSelect:
Set(varUploadInProgress, true);
Set(varUploadProgress, 0);

// Atualizar progress (simulado)
UpdateContext({_refresh: true});
Set(varUploadProgress, 33);

// Fazer upload
Set(
    varUploadResult,
    APIStorage.UploadArquivo({
        arquivo: /* ... */,
        nome_arquivo: /* ... */
    })
);

Set(varUploadProgress, 66);
UpdateContext({_refresh: true});

// Processar resultado
Set(varUploadProgress, 100);
Set(varUploadInProgress, false);

// Exibir resultado
Notify(
    If(
        varUploadResult.sucesso,
        "Upload concluído!",
        "Erro no upload"
    ),
    If(
        varUploadResult.sucesso,
        NotificationType.Success,
        NotificationType.Error
    )
)

// Progress Bar (Rectangle):
Width = Parent.Width * (varUploadProgress / 100)
Visible = varUploadInProgress
```

---

## Formulário Completo

### Exemplo: Formulário de Guia Médica com Anexos

```powerapps
// Screen: ScreenGuiaMedica

// Campos do formulário:
// - txtNumeroGuia: Text Input
// - txtPaciente: Text Input
// - ddTipo: Dropdown
// - attAnexos: Attachments
// - btnSalvar: Button

// btnSalvar.OnSelect:

// 1. Validar campos
If(
    IsBlank(txtNumeroGuia.Text) || IsBlank(txtPaciente.Text),
    Notify("Preencha todos os campos obrigatórios", NotificationType.Error),

    // 2. Salvar guia no banco de dados (sua lógica existente)
    Set(
        varGuiaId,
        /* Sua lógica de criação de guia */
        "GUID-DA-GUIA"
    );

    // 3. Fazer upload dos anexos
    If(
        CountRows(attAnexos.Attachments) > 0,

        // Upload de cada arquivo
        ForAll(
            attAnexos.Attachments,
            Collect(
                colAnexosGuia,
                {
                    guia_id: varGuiaId,
                    resultado: APIStorage.UploadArquivo({
                        arquivo: Last(
                            FirstN(
                                Split(
                                    JSON(
                                        ThisRecord,
                                        JSONFormat.IncludeBinaryData
                                    ),
                                    ","
                                ),
                                2
                            )
                        ).Result,
                        nome_arquivo: DisplayName,
                        tipo_conteudo: ContentType,
                        usuario: User().Email,
                        pasta: "guias/" & varGuiaId
                    })
                }
            )
        );

        // 4. Verificar resultados
        If(
            CountRows(
                Filter(colAnexosGuia, !resultado.sucesso)
            ) = 0,
            // Todos os uploads foram bem-sucedidos
            Notify(
                "Guia salva com " &
                CountRows(colAnexosGuia) &
                " anexo(s)",
                NotificationType.Success
            );

            // 5. Limpar formulário
            Reset(txtNumeroGuia);
            Reset(txtPaciente);
            Reset(attAnexos);
            Clear(colAnexosGuia);

            // 6. Navegar de volta
            Back(),

            // Alguns uploads falharam
            Notify(
                "Guia salva, mas " &
                CountRows(Filter(colAnexosGuia, !resultado.sucesso)) &
                " anexo(s) falharam",
                NotificationType.Warning
            )
        )
    );

    // Guia salva sem anexos
    Notify("Guia salva com sucesso", NotificationType.Success);
    Reset(txtNumeroGuia);
    Reset(txtPaciente);
    Back()
)
```

---

## Dicas e Boas Práticas

### 1. Otimização de Performance

```powerapps
// Carregar arquivos apenas quando necessário
If(
    IsEmpty(colArquivos),
    // Carregar apenas na primeira vez
    ClearCollect(
        colArquivos,
        APIStorage.ListarArquivos({limite: 50}).arquivos
    )
)
```

### 2. Tratamento de Erros

```powerapps
// Sempre verificar sucesso antes de usar os dados
If(
    varResult.sucesso,
    // Processar dados
    Set(varDados, varResult.dados),
    // Tratar erro
    Notify("Erro: " & varResult.mensagem, NotificationType.Error);
    Trace("Erro API Storage: " & varResult.mensagem)
)
```

### 3. Cache de URLs

```powerapps
// Armazenar URLs temporárias em coleção para evitar múltiplas chamadas
If(
    IsBlank(
        LookUp(colUrlsCache, id = varFileId)
    ),
    // URL não está em cache - buscar
    Collect(
        colUrlsCache,
        {
            id: varFileId,
            url: APIStorage.DownloadArquivo(
                varFileId,
                {url_apenas: true}
            ).url_download,
            expira: Now() + Time(1, 0, 0) // 1 hora
        }
    )
);

// Usar URL do cache
Set(
    varUrl,
    LookUp(colUrlsCache, id = varFileId).url
)
```

### 4. Validação de Tipos de Arquivo

```powerapps
// Validar extensão antes do upload
With(
    {
        extensao: Lower(
            Right(
                btnUpload.Media.FileName,
                Len(btnUpload.Media.FileName) -
                Find(".", btnUpload.Media.FileName, -1)
            )
        ),
        extensoesPermitidas: [
            "pdf", "jpg", "jpeg", "png", "doc", "docx"
        ]
    },
    If(
        extensao in extensoesPermitidas,
        // Fazer upload
        /* ... */,
        // Extensão não permitida
        Notify(
            "Tipo de arquivo não permitido. Use: " &
            Concat(extensoesPermitidas, "." & Value, ", "),
            NotificationType.Error
        )
    )
)
```

---

## Troubleshooting

### Erro: "Invalid base64 string"

**Problema**: String base64 malformada

**Solução**:
```powerapps
// Remover prefixo data:mime;base64, se existir
Last(FirstN(Split(base64String, ","), 2)).Result
```

### Erro: "File too large"

**Solução**: Verificar tamanho antes do upload
```powerapps
If(
    btnUpload.Media.Size > 10 * 1024 * 1024, // 10 MB
    Notify("Arquivo muito grande (máx 10MB)", NotificationType.Error),
    // Fazer upload
)
```

### URLs não carregam em Image/PDF Viewer

**Solução**: Verificar se a URL tem permissão SAS válida e se o controle aceita URLs externas.

---

## Recursos Adicionais

- [Documentação oficial Power Apps - Custom Connectors](https://docs.microsoft.com/connectors/custom-connectors/)
- [Working with attachments in Power Apps](https://docs.microsoft.com/power-apps/maker/canvas-apps/controls/control-attachments)
- [JSON function in Power Apps](https://docs.microsoft.com/power-platform/power-fx/reference/function-json)
