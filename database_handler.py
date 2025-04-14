from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Dict
import os
from sqlalchemy import Float
from sqlalchemy.dialects.postgresql import ARRAY

Base = declarative_base()

class Document(Base):
    __tablename__ = 'test_vector'
    __table_args__ = {'schema': 'test'}
    key_id = Column(String(100), primary_key=True, nullable=False, server_default='')
    id = Column(String(50))
    create_time = Column(DateTime)
    modif_time = Column(DateTime)
    company = Column(String(30))
    industry = Column(Text)
    # 使用 vector 类型
    industry_embedding = Column('industry_embedding', nullable=True)
    title = Column(Text)
    # 使用 vector 类型
    title_embedding = Column('title_embedding', nullable=True)
    content = Column(Text)
    # 使用 vector 类型
    content_embedding = Column('content_embedding', nullable=True)
    status = Column(Integer)
    hash = Column(String(64))

class DatabaseHandler:
    def __init__(self, host: str, port: int, username: str, password: str, database: str):
        db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        self.engine = create_engine(db_url)
        # 在创建表之前确保 pgvector 扩展已启用
        from sqlalchemy.sql import text
        try:
            with self.engine.connect() as conn:
                # 检查是否已安装pgvector扩展
                result = conn.execute(text("SELECT 1 FROM pg_extension WHERE extname='vector'"))
                if not result.scalar():
                    try:
                        conn.execute(text("CREATE EXTENSION vector;"))
                    except Exception as create_ex:
                        raise Exception(f"创建pgvector扩展失败，请确保有足够权限: {str(create_ex)}")
                
                # 确保vector类型可用，如果不可用则尝试重新加载扩展
                try:
                    conn.execute(text("SELECT 1 FROM pg_type WHERE typname='vector'"))
                except Exception as type_ex:
                    try:
                        conn.execute(text("DROP EXTENSION IF EXISTS vector CASCADE; CREATE EXTENSION vector;"))
                        conn.execute(text("SELECT 1 FROM pg_type WHERE typname='vector'"))
                    except Exception as reload_ex:
                        raise Exception(f"无法加载pgvector扩展，请确保已正确安装: {str(reload_ex)}")
                
                Base.metadata.create_all(self.engine)
                self.Session = sessionmaker(bind=self.engine)
        except Exception as e:
            # 提供更详细的错误信息
            raise Exception(f"初始化数据库失败: {str(e)}")
    
    def insert_documents(self, documents: List[Dict]) -> bool:
        try:
            session = self.Session()
            docs_to_add = []
            for doc in documents:
                key_id = f"{doc['title']}-{doc['id']}"
                existing_doc = session.query(Document).filter(Document.key_id == key_id).first()
                if existing_doc:
                    print(f"文档 {key_id} 已存在，跳过插入")
                    continue
                
                docs_to_add.append(Document(
                    key_id=key_id,
                    id=doc['id'],
                    create_time=datetime.strptime(doc['create_time'], '%Y-%m-%d') if isinstance(doc['create_time'], str) else doc['create_time'],
                    modif_time=datetime.strptime(doc['modif_time'], '%Y-%m-%d') if isinstance(doc['modif_time'], str) else (datetime.strptime(doc['modif_time'], '%Y-%m-%d') if doc['modif_time'] else None),
                    company=doc['company'],
                    industry=doc['industry'],
                    industry_embedding=doc['industry_embedding'],
                    title=doc['title'],
                    title_embedding=doc['title_embedding'],
                    content=doc['content'],
                    content_embedding=doc['content_embedding'],
                    status=1 if doc['status'] == 'enabled' else 0,
                    hash=doc['hash']
                ))
                
            if not docs_to_add:
                print("所有文档都已存在，无需插入")
                return False
                
            session.add_all(docs_to_add)
            try:
                session.commit()
                return True
            except Exception as flush_ex:
                session.rollback()
                print(f"插入文档详细错误: {str(flush_ex)}")
                print(f"当前文档数据: {docs_to_add}")
                raise Exception(f"文档插入过程中发生错误: {str(flush_ex)}")
        except Exception as e:
            session.rollback()
            raise Exception(f"插入文档失败: {str(e)}")
        finally:
            session.close()
    
    def get_document_by_id(self, key_id: str) -> Dict:
        """根据key_id查询文档"""
        try:
            session = self.Session()
            doc = session.query(Document).filter(Document.key_id == key_id).first()
            if doc:
                return {
                    'key_id': doc.key_id,
                    'id': doc.id,
                    'create_time': doc.create_time,
                    'modif_time': doc.modif_time,
                    'company': doc.company,
                    'industry': doc.industry,
                    'industry_embedding': doc.industry_embedding,
                    'title': doc.title,
                    'title_embedding': doc.title_embedding,
                    'content': doc.content,
                    'content_embedding': doc.content_embedding,
                    'status': doc.status,
                    'hash': doc.hash
                }
            return None
        except Exception as e:
            raise Exception(f"查询文档失败: {str(e)}")
        finally:
            session.close()
    
    def get_documents_by_company(self, company: str) -> List[Dict]:
        """根据公司名称查询文档"""
        try:
            session = self.Session()
            docs = session.query(Document).filter(Document.company == company).all()
            return [{
                'key_id': doc.key_id,
                'id': doc.id,
                'create_time': doc.create_time,
                'modif_time': doc.modif_time,
                'company': doc.company,
                'industry': doc.industry,
                'industry_embedding': list(doc.industry_embedding) if doc.industry_embedding is not None else None,
                'title': doc.title,
                'title_embedding': list(doc.title_embedding) if doc.title_embedding is not None else None,
                'content': doc.content,
                'content_embedding': list(doc.content_embedding) if doc.content_embedding is not None else None,
                'status': doc.status,
                'hash': doc.hash
            } for doc in docs]
        except Exception as e:
            raise Exception(f"查询文档失败: {str(e)}")
        finally:
            session.close()
    
    def update_document_status(self, key_id: str, status: int) -> bool:
        """更新文档状态"""
        try:
            session = self.Session()
            doc = session.query(Document).filter(Document.key_id == key_id).first()
            if doc:
                doc.status = status
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise Exception(f"更新文档状态失败: {str(e)}")
        finally:
            session.close()
    
    def delete_document(self, key_id: str) -> bool:
        """删除文档"""
        try:
            session = self.Session()
            doc = session.query(Document).filter(Document.key_id == key_id).first()
            if doc:
                session.delete(doc)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise Exception(f"删除文档失败: {str(e)}")
        finally:
            session.close()