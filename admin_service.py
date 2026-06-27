import os
import sys
import uuid
import pymysql
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base import logger, Config
from rag_qa.core.vector_store import VectorStore
from rag_qa.edu_text_spliter.edu_chinese_recursive_text_splitter import ChineseRecursiveTextSplitter

conf = Config()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

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
        处理上传文件：
        1. 保存到 uploads/{source}/
        2. 用对应 loader 加载文档
        3. 用 ChineseRecursiveTextSplitter 分块
        4. 存入 Milvus
        5. 记录到 MySQL uploads 表
        """
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in LOADER_MAP:
            raise ValueError(f"不支持的文件类型: {ext}，支持: {list(LOADER_MAP.keys())}")

        # 保存文件
        save_dir = os.path.join(UPLOAD_DIR, source)
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{uuid.uuid4().hex[:8]}_{file_name}")
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        file_size = len(file_bytes)
        logger.info(f"文件已保存: {save_path} ({file_size} bytes)")

        # 加载文档
        documents = self._load_file(save_path, ext, source)
        if not documents:
            raise RuntimeError("文档解析失败，未能提取到内容")

        logger.info(f"文档解析成功，获得 {len(documents)} 个文档块")

        # 父-子分块
        child_chunks = self._split_documents(documents)
        logger.info(f"分块完成，共 {len(child_chunks)} 个子块")

        # 存入 Milvus
        self.vector_store.add_documents(child_chunks)
        logger.info(f"已存入 Milvus: {len(child_chunks)} 个子块")

        # 记录到 MySQL
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

    def _load_file(self, file_path: str, ext: str, source: str) -> list:
        """加载单个文件"""
        from rag_qa.edu_document_loaders.edu_pdfloader import OCRPDFLoader
        from rag_qa.edu_document_loaders.edu_docloader import OCRDOCLoader
        from rag_qa.edu_document_loaders.edu_pptloader import OCRPPTLoader
        from rag_qa.edu_document_loaders.edu_imgloader import OCRIMGLoader
        from langchain_community.document_loaders import TextLoader
        from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader

        loader_map = {
            ".pdf": OCRPDFLoader,
            ".docx": OCRDOCLoader,
            ".ppt": OCRPPTLoader,
            ".pptx": OCRPPTLoader,
            ".jpg": OCRIMGLoader,
            ".png": OCRIMGLoader,
            ".txt": TextLoader,
            ".md": UnstructuredMarkdownLoader,
        }

        loader_class = loader_map[ext]
        if ext == ".txt":
            loader = loader_class(file_path, encoding="utf-8")
        else:
            loader = loader_class(file_path)

        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = source
            doc.metadata["file_path"] = file_path
            doc.metadata["timestamp"] = datetime.now().isoformat()
        return docs

    def _split_documents(self, documents: list) -> list:
        """父-子文档分块"""
        parent_splitter = ChineseRecursiveTextSplitter(
            chunk_size=conf.PARENT_CHUNK_SIZE, chunk_overlap=conf.CHUNK_OVERLAP
        )
        child_splitter = ChineseRecursiveTextSplitter(
            chunk_size=conf.CHILD_CHUNK_SIZE, chunk_overlap=conf.CHUNK_OVERLAP
        )

        child_chunks = []
        for i, doc in enumerate(documents):
            parent_docs = parent_splitter.split_documents([doc])
            for j, parent_doc in enumerate(parent_docs):
                parent_id = f"up_{os.path.basename(doc.metadata.get('file_path',''))}_{i}_parent_{j}"
                parent_doc.metadata["parent_id"] = parent_id
                parent_doc.metadata["parent_content"] = parent_doc.page_content

                sub_chunks = child_splitter.split_documents([parent_doc])
                for k, sub_chunk in enumerate(sub_chunks):
                    sub_chunk.metadata["parent_id"] = parent_id
                    sub_chunk.metadata["parent_content"] = parent_doc.page_content
                    sub_chunk.metadata["id"] = f"{parent_id}_child_{k}"
                    child_chunks.append(sub_chunk)

        return child_chunks

    def list_documents(self) -> list:
        """列出所有已上传文档（按 source 汇总）"""
        try:
            self.mysql.cursor.execute("""
                SELECT source, COUNT(*) as file_count, SUM(chunks_count) as total_chunks,
                       MAX(uploaded_at) as latest_upload
                FROM uploads
                GROUP BY source
                ORDER BY latest_upload DESC
            """)
            return [
                {
                    "source": row[0],
                    "file_count": row[1],
                    "total_chunks": row[2],
                    "latest_upload": str(row[3]) if row[3] else "",
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
            source_dir = os.path.join(UPLOAD_DIR, source)
            if os.path.exists(source_dir):
                shutil.rmtree(source_dir)

            return {"status": "success", "deleted_files": deleted_files, "source": source}
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return {"status": "error", "error": str(e)}
