-- Tabela para armazenar metadados dos arquivos no Azure Blob Storage
CREATE TABLE ArquivosStorage (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    NomeOriginal NVARCHAR(500) NOT NULL,
    NomeArmazenado NVARCHAR(500) NOT NULL,
    CaminhoBlob NVARCHAR(1000) NOT NULL,
    UrlBlob NVARCHAR(2000) NOT NULL,
    TamanhoBytes BIGINT NOT NULL,
    TipoConteudo NVARCHAR(200),
    Container NVARCHAR(100) NOT NULL DEFAULT 'arquivos',
    StorageAccount NVARCHAR(100) NOT NULL DEFAULT 'staudicoreapiprod',
    DataUpload DATETIME2 DEFAULT GETDATE(),
    UploadPor NVARCHAR(200),
    Tags NVARCHAR(MAX), -- JSON com tags adicionais
    Ativo BIT DEFAULT 1,
    CONSTRAINT CK_TamanhoBytes CHECK (TamanhoBytes >= 0)
);

-- Índices para melhorar performance
CREATE INDEX IX_ArquivosStorage_DataUpload ON ArquivosStorage(DataUpload DESC);
CREATE INDEX IX_ArquivosStorage_NomeOriginal ON ArquivosStorage(NomeOriginal);
CREATE INDEX IX_ArquivosStorage_Container ON ArquivosStorage(Container);
CREATE INDEX IX_ArquivosStorage_Ativo ON ArquivosStorage(Ativo);

-- Comentários nas colunas
EXEC sp_addextendedproperty
    @name = N'MS_Description', @value = 'Identificador único do arquivo',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'ArquivosStorage',
    @level2type = N'COLUMN', @level2name = N'Id';

EXEC sp_addextendedproperty
    @name = N'MS_Description', @value = 'Nome original do arquivo enviado pelo usuário',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'ArquivosStorage',
    @level2type = N'COLUMN', @level2name = N'NomeOriginal';

EXEC sp_addextendedproperty
    @name = N'MS_Description', @value = 'Nome do arquivo armazenado no Blob (geralmente com GUID)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'ArquivosStorage',
    @level2type = N'COLUMN', @level2name = N'NomeArmazenado';

EXEC sp_addextendedproperty
    @name = N'MS_Description', @value = 'Caminho completo do blob: container/pasta/arquivo',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'ArquivosStorage',
    @level2type = N'COLUMN', @level2name = N'CaminhoBlob';

EXEC sp_addextendedproperty
    @name = N'MS_Description', @value = 'URL completa do blob no Azure Storage',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'ArquivosStorage',
    @level2type = N'COLUMN', @level2name = N'UrlBlob';
