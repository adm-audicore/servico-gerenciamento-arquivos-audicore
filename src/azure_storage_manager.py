"""
Módulo para gerenciar upload e download de arquivos no Azure Blob Storage
Integração com Power Apps
"""

import os
import uuid
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, BinaryIO
import pyodbc
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError


class AzureStorageManager:
    """Gerencia operações de upload/download de arquivos no Azure Blob Storage"""

    def __init__(
        self,
        storage_account: str,
        storage_key: str,
        container_name: str,
        sql_connection_string: str
    ):
        """
        Inicializa o gerenciador de storage

        Args:
            storage_account: Nome da conta de storage
            storage_key: Chave de acesso da conta
            container_name: Nome do container
            sql_connection_string: String de conexão do SQL Server
        """
        self.storage_account = storage_account
        self.storage_key = storage_key
        self.container_name = container_name
        self.sql_connection_string = sql_connection_string

        # Criar cliente do Blob Storage
        connection_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={storage_account};"
            f"AccountKey={storage_key};"
            f"EndpointSuffix=core.windows.net"
        )
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)

    def _get_db_connection(self):
        """Retorna uma conexão com o banco de dados"""
        return pyodbc.connect(self.sql_connection_string)

    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Gera um nome único para o arquivo mantendo a extensão original

        Args:
            original_filename: Nome original do arquivo

        Returns:
            Nome único gerado
        """
        file_ext = os.path.splitext(original_filename)[1]
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_ext}"

    def upload_file(
        self,
        file_content: bytes,
        original_filename: str,
        content_type: str,
        upload_user: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Faz upload de um arquivo para o Azure Blob Storage e registra no banco de dados

        Args:
            file_content: Conteúdo do arquivo em bytes
            original_filename: Nome original do arquivo
            content_type: Tipo MIME do arquivo
            upload_user: Usuário que fez o upload
            tags: Dicionário com tags adicionais (será armazenado como JSON)
            folder: Pasta dentro do container (opcional)

        Returns:
            Dicionário com informações do arquivo salvo
        """
        try:
            # Gerar nome único
            unique_filename = self._generate_unique_filename(original_filename)

            # Montar o caminho do blob
            if folder:
                blob_path = f"{folder}/{unique_filename}"
            else:
                blob_path = unique_filename

            # Fazer upload do arquivo
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_client.upload_blob(
                file_content,
                content_type=content_type,
                overwrite=False
            )

            # Obter URL do blob
            blob_url = blob_client.url

            # Tamanho do arquivo
            file_size = len(file_content)

            # Registrar no banco de dados
            file_id = str(uuid.uuid4())
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ArquivosStorage (
                        Id, NomeOriginal, NomeArmazenado, CaminhoBlob,
                        UrlBlob, TamanhoBytes, TipoConteudo, Container,
                        StorageAccount, UploadPor, Tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_id,
                    original_filename,
                    unique_filename,
                    blob_path,
                    blob_url,
                    file_size,
                    content_type,
                    self.container_name,
                    self.storage_account,
                    upload_user,
                    str(tags) if tags else None
                ))
                conn.commit()

            return {
                "id": file_id,
                "nome_original": original_filename,
                "nome_armazenado": unique_filename,
                "caminho_blob": blob_path,
                "url": blob_url,
                "tamanho_bytes": file_size,
                "tipo_conteudo": content_type,
                "sucesso": True,
                "mensagem": "Arquivo enviado com sucesso"
            }

        except ResourceExistsError:
            return {
                "sucesso": False,
                "mensagem": "Arquivo já existe no storage"
            }
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Erro ao fazer upload: {str(e)}"
            }

    def upload_file_base64(
        self,
        file_content_base64: str,
        original_filename: str,
        content_type: str,
        upload_user: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Faz upload de um arquivo a partir de uma string base64 (formato comum do Power Apps)

        Args:
            file_content_base64: Conteúdo do arquivo em base64
            original_filename: Nome original do arquivo
            content_type: Tipo MIME do arquivo
            upload_user: Usuário que fez o upload
            tags: Dicionário com tags adicionais
            folder: Pasta dentro do container (opcional)

        Returns:
            Dicionário com informações do arquivo salvo
        """
        try:
            # Decodificar base64
            file_content = base64.b64decode(file_content_base64)

            # Chamar upload normal
            return self.upload_file(
                file_content=file_content,
                original_filename=original_filename,
                content_type=content_type,
                upload_user=upload_user,
                tags=tags,
                folder=folder
            )
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Erro ao decodificar arquivo base64: {str(e)}"
            }

    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações de um arquivo do banco de dados

        Args:
            file_id: ID do arquivo

        Returns:
            Dicionário com informações do arquivo ou None se não encontrado
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        Id, NomeOriginal, NomeArmazenado, CaminhoBlob,
                        UrlBlob, TamanhoBytes, TipoConteudo, Container,
                        StorageAccount, DataUpload, UploadPor, Tags, Ativo
                    FROM ArquivosStorage
                    WHERE Id = ? AND Ativo = 1
                """, (file_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                return {
                    "id": row.Id,
                    "nome_original": row.NomeOriginal,
                    "nome_armazenado": row.NomeArmazenado,
                    "caminho_blob": row.CaminhoBlob,
                    "url": row.UrlBlob,
                    "tamanho_bytes": row.TamanhoBytes,
                    "tipo_conteudo": row.TipoConteudo,
                    "container": row.Container,
                    "storage_account": row.StorageAccount,
                    "data_upload": row.DataUpload.isoformat() if row.DataUpload else None,
                    "upload_por": row.UploadPor,
                    "tags": row.Tags,
                    "ativo": row.Ativo
                }
        except Exception as e:
            print(f"Erro ao buscar arquivo: {e}")
            return None

    def download_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Baixa um arquivo do Azure Blob Storage

        Args:
            file_id: ID do arquivo no banco de dados

        Returns:
            Dicionário com conteúdo do arquivo e metadados
        """
        try:
            # Obter informações do arquivo
            file_info = self.get_file_info(file_id)
            if not file_info:
                return {
                    "sucesso": False,
                    "mensagem": "Arquivo não encontrado"
                }

            # Baixar o blob
            blob_client = self.container_client.get_blob_client(file_info["caminho_blob"])
            blob_data = blob_client.download_blob()
            file_content = blob_data.readall()

            return {
                "sucesso": True,
                "conteudo": file_content,
                "nome_original": file_info["nome_original"],
                "tipo_conteudo": file_info["tipo_conteudo"],
                "tamanho_bytes": file_info["tamanho_bytes"]
            }

        except ResourceNotFoundError:
            return {
                "sucesso": False,
                "mensagem": "Arquivo não encontrado no storage"
            }
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Erro ao baixar arquivo: {str(e)}"
            }

    def generate_download_url(
        self,
        file_id: str,
        expiry_hours: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Gera uma URL temporária (SAS) para download direto do arquivo
        Útil para o Power Apps fazer download sem passar pela API

        Args:
            file_id: ID do arquivo
            expiry_hours: Tempo de validade da URL em horas (padrão: 1 hora)

        Returns:
            Dicionário com a URL de download
        """
        try:
            # Obter informações do arquivo
            file_info = self.get_file_info(file_id)
            if not file_info:
                return {
                    "sucesso": False,
                    "mensagem": "Arquivo não encontrado"
                }

            # Gerar SAS token
            sas_token = generate_blob_sas(
                account_name=self.storage_account,
                container_name=self.container_name,
                blob_name=file_info["caminho_blob"],
                account_key=self.storage_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )

            # Montar URL completa
            download_url = f"{file_info['url']}?{sas_token}"

            return {
                "sucesso": True,
                "url_download": download_url,
                "nome_original": file_info["nome_original"],
                "validade_horas": expiry_hours,
                "expira_em": (datetime.utcnow() + timedelta(hours=expiry_hours)).isoformat()
            }

        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Erro ao gerar URL de download: {str(e)}"
            }

    def delete_file(self, file_id: str, permanent: bool = False) -> Dict[str, Any]:
        """
        Deleta um arquivo (soft delete por padrão)

        Args:
            file_id: ID do arquivo
            permanent: Se True, deleta permanentemente do storage também

        Returns:
            Dicionário com resultado da operação
        """
        try:
            # Obter informações do arquivo
            file_info = self.get_file_info(file_id)
            if not file_info:
                return {
                    "sucesso": False,
                    "mensagem": "Arquivo não encontrado"
                }

            if permanent:
                # Deletar do blob storage
                blob_client = self.container_client.get_blob_client(file_info["caminho_blob"])
                blob_client.delete_blob()

                # Deletar do banco de dados
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM ArquivosStorage WHERE Id = ?", (file_id,))
                    conn.commit()

                return {
                    "sucesso": True,
                    "mensagem": "Arquivo deletado permanentemente"
                }
            else:
                # Soft delete - apenas marca como inativo
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE ArquivosStorage SET Ativo = 0 WHERE Id = ?",
                        (file_id,)
                    )
                    conn.commit()

                return {
                    "sucesso": True,
                    "mensagem": "Arquivo marcado como inativo"
                }

        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Erro ao deletar arquivo: {str(e)}"
            }

    def list_files(
        self,
        limit: int = 100,
        offset: int = 0,
        folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lista arquivos do banco de dados

        Args:
            limit: Número máximo de registros
            offset: Offset para paginação
            folder: Filtrar por pasta específica

        Returns:
            Lista de arquivos
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT
                        Id, NomeOriginal, TamanhoBytes, TipoConteudo,
                        DataUpload, UploadPor
                    FROM ArquivosStorage
                    WHERE Ativo = 1
                """
                params = []

                if folder:
                    query += " AND CaminhoBlob LIKE ?"
                    params.append(f"{folder}/%")

                query += " ORDER BY DataUpload DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
                params.extend([offset, limit])

                cursor.execute(query, params)

                files = []
                for row in cursor.fetchall():
                    files.append({
                        "id": row.Id,
                        "nome_original": row.NomeOriginal,
                        "tamanho_bytes": row.TamanhoBytes,
                        "tipo_conteudo": row.TipoConteudo,
                        "data_upload": row.DataUpload.isoformat() if row.DataUpload else None,
                        "upload_por": row.UploadPor
                    })

                return {
                    "sucesso": True,
                    "arquivos": files,
                    "total": len(files)
                }

        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Erro ao listar arquivos: {str(e)}"
            }
