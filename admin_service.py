import os
import sys
import pymysql

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base import logger, Config
from rag_qa.core.vector_store import VectorStore

conf = Config()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rag_qa", "data")

# 文件扩展名 → loader 映射（同 document_processor）
LOADER_MAP = {
    ".txt": "TextLoader",
    ".pdf": "OCRPDFLoader",
    ".docx": "OCRDOCLoader",
    ".ppt": "OCRPPTLoader",
    ".pptx": "OCRPPTLoader",
    ".jpg": "OCRIMGLoader",
    ".png": "OCRIMGLoader",
    ".md": "UnstructuredMarkdownLoader",
}


class AdminService:
    """管理员服务：文件上传处理 + 文档管理"""

    def __init__(self, mysql_client, vector_store: VectorStore):
        self.mysql = mysql_client
        self.vector_store = vector_store
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        self._ensure_table()

    def _ensure_table(self):
        """确保 uploads 表存在"""
        try:
            self.mysql.cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file_name VARCHAR(255) NOT NULL,
                    source VARCHAR(50) NOT NULL,
                    file_size INT DEFAULT 0,
                    chunks_count INT DEFAULT 0,
                    uploaded_by VARCHAR(50) NOT NULL,
                    uploaded_at DATETIME DEFAULT NOW()
                )
            """)
            self.mysql.connection.commit()
        except pymysql.MySQLError as e:
            logger.error(f"初始化 uploads 表失败: {e}")

    def process_upload(self, file_bytes: bytes, file_name: str, source: str, username: str) -> dict:
        """
        处理上传文件：保存 → 复用 process_documents 处理 → 存 Milvus → 记录
        """
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in LOADER_MAP:
            raise ValueError(f"不支持的文件类型: {ext}，支持: {list(LOADER_MAP.keys())}")

        # 1. 保存到 rag_qa/data/{source}_data/
        save_dir = os.path.join(UPLOAD_DIR, f"{source}_data")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file_name)
        # 重名则加序号
        if os.path.exists(save_path):
            base, ext = os.path.splitext(file_name)
            for i in range(1, 100):
                save_path = os.path.join(save_dir, f"{base}({i}){ext}")
                if not os.path.exists(save_path):
                    break
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        file_size = len(file_bytes)
        logger.info(f"文件已保存: {save_path} ({file_size} bytes)")

        # 2. 复用 document_processor 的 process_documents 处理整个目录
        from rag_qa.core.document_processor import process_documents
        conf = Config()
        child_chunks = process_documents(
            save_dir,
            parent_chunk_size=conf.PARENT_CHUNK_SIZE,
            child_chunk_size=conf.CHILD_CHUNK_SIZE,
            chunk_overlap=conf.CHUNK_OVERLAP,
        )
        logger.info(f"分块完成，共 {len(child_chunks)} 个子块")

        # 3. 存入 Milvus
        self.vector_store.add_documents(child_chunks)
        logger.info(f"已存入 Milvus: {len(child_chunks)} 个子块")

        # 4. 记录到 MySQL
        try:
            self.mysql.cursor.execute(
                "INSERT INTO uploads (file_name, source, file_size, chunks_count, uploaded_by) VALUES (%s, %s, %s, %s, %s)",
                (file_name, source, file_size, len(child_chunks), username),
            )
            self.mysql.connection.commit()
        except pymysql.MySQLError as e:
            logger.error(f"记录上传失败: {e}")

        return {
            "file_name": file_name,
            "source": source,
            "file_size": file_size,
            "chunks_count": len(child_chunks),
            "status": "success",
        }

    def list_documents(self) -> list:
        """列出所有已上传文档详情"""
        try:
            self.mysql.cursor.execute("""
                SELECT id, file_name, source, file_size, chunks_count, uploaded_by, uploaded_at
                FROM uploads
                ORDER BY uploaded_at DESC
            """)
            return [
                {
                    "id": row[0],
                    "file_name": row[1],
                    "source": row[2],
                    "file_size": row[3],
                    "chunks_count": row[4],
                    "uploaded_by": row[5],
                    "uploaded_at": str(row[6]) if row[6] else "",
                }
                for row in self.mysql.cursor.fetchall()
            ]
        except pymysql.MySQLError as e:
            logger.error(f"获取文档列表失败: {e}")
            return []

    def list_files(self, source: str = None) -> list:
        """列出文件详情"""
        try:
            if source:
                self.mysql.cursor.execute(
                    "SELECT id, file_name, source, file_size, chunks_count, uploaded_by, uploaded_at FROM uploads WHERE source=%s ORDER BY uploaded_at DESC",
                    (source,),
                )
            else:
                self.mysql.cursor.execute(
                    "SELECT id, file_name, source, file_size, chunks_count, uploaded_by, uploaded_at FROM uploads ORDER BY uploaded_at DESC"
                )
            return [
                {
                    "id": row[0], "file_name": row[1], "source": row[2],
                    "file_size": row[3], "chunks_count": row[4],
                    "uploaded_by": row[5], "uploaded_at": str(row[6]) if row[6] else "",
                }
                for row in self.mysql.cursor.fetchall()
            ]
        except pymysql.MySQLError as e:
            logger.error(f"获取文件列表失败: {e}")
            return []

    def delete_by_source(self, source: str) -> dict:
        """
        按 source 删除文档：Milvus + MySQL + 磁盘文件
        """
        try:
            # 删除 Milvus 中该 source 的数据
            from pymilvus import MilvusClient
            client = MilvusClient(
                uri=f"http://{conf.MILVUS_HOST}:{conf.MILVUS_PORT}",
                db_name=conf.MILVUS_DATABASE_NAME,
            )
            res = client.delete(
                collection_name=conf.MILVUS_COLLECTION_NAME,
                filter=f'source == "{source}"',
            )
            logger.info(f"Milvus 删除: {res}")

            # 删除 MySQL 记录
            self.mysql.cursor.execute("DELETE FROM uploads WHERE source=%s", (source,))
            self.mysql.connection.commit()
            deleted_files = self.mysql.cursor.rowcount

            # 删除磁盘文件
            import shutil
            source_dir = os.path.join(UPLOAD_DIR, f"{source}_data")
            if os.path.exists(source_dir):
                shutil.rmtree(source_dir)

            return {"status": "success", "deleted_files": deleted_files, "source": source}
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return {"status": "error", "error": str(e)}
