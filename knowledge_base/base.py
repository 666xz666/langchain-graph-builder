import os
import uuid
import json
import shutil
from text_to_vec import DocumentProcessor
from utils import *
import os
from graph import LLMGraphTransformer

os.environ['NUMEXPR_MAX_THREADS'] = NUMEXPR_MAX_THREADS

class KnowledgeBase:
    def __init__(self):
        if not os.path.exists(VEC_BASE_PATH):
            os.makedirs(VEC_BASE_PATH)
        self.metadata_file = os.path.join(VEC_BASE_PATH, 'kb_metadata.json')
        self.load_kb_metadata()

    def load_kb_metadata(self):
        if not os.path.exists(self.metadata_file):
            self.kb_metadata = {}
        else:
            with open(self.metadata_file, 'r') as f:
                self.kb_metadata = json.load(f)

    def get_vec_metadata(self, kb_uuid):
        kb_info = self.kb_metadata.get(kb_uuid)
        if not kb_info:
            return None
        vecs_path = os.path.join(VEC_BASE_PATH, kb_info['kb_dir'], 'vecs', 'vecs.json')
        if not os.path.exists(vecs_path):
            return None
        with open(vecs_path, 'r') as f:
            vec_metadata = json.load(f)
        return vec_metadata

    def save_kb_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.kb_metadata, f, indent=4, ensure_ascii=False)

    def create_kb(self, kb_name, desc):
        kb_uuid = str(uuid.uuid4())
        kb_dir_name = f"{kb_uuid}_{kb_name}"
        kb_dir_path = os.path.join(VEC_BASE_PATH, kb_dir_name)

        if not os.path.exists(kb_dir_path):
            os.makedirs(kb_dir_path)
            os.makedirs(os.path.join(kb_dir_path, 'files'))
            os.makedirs(os.path.join(kb_dir_path, 'vecs'))

            self.kb_metadata[kb_uuid] = {
                "kb_name": kb_name,
                "kb_dir": kb_dir_name,
                "desc": desc,
                "files": {}
            }
            self.save_kb_metadata()
            return kb_uuid
        else:
            raise Exception(f"知识库 {kb_name} 已存在")

    def upload_file(self, kb_uuid, file_stream, file_name):
        kb_info = self.kb_metadata.get(kb_uuid)
        if not kb_info:
            raise Exception(f"知识库 UUID {kb_uuid} 不存在")

        kb_dir_path = os.path.join(VEC_BASE_PATH, kb_info['kb_dir'])
        file_uuid = str(uuid.uuid4())
        unique_filename = f"{file_uuid}_{file_name}"
        file_path = os.path.join(kb_dir_path, 'files', unique_filename)
        file_stream.save(file_path)

        kb_info['files'][file_uuid] = {
            "filename": file_name,
            "file_path": "files/"+unique_filename
        }
        self.save_kb_metadata()
        return file_uuid

    def get_file(self, kb_uuid, file_uuid):
        kb_info = self.kb_metadata.get(kb_uuid)
        if not kb_info:
            raise Exception(f"知识库 UUID {kb_uuid} 不存在")

        file_info = kb_info.get('files', {}).get(file_uuid)
        if not file_info:
            raise Exception("文件未找到")

        file_path = os.path.join(VEC_BASE_PATH, kb_info['kb_dir'], file_info['file_path'])
        return file_path

    def get_kb_info(self, kb_uuid):
        kb_info = self.kb_metadata.get(kb_uuid)
        if not kb_info:
            raise Exception(f"知识库 UUID {kb_uuid} 不存在")
        return kb_info

    def delete_kb(self, kb_uuid):
        kb_info = self.kb_metadata.get(kb_uuid)
        if not kb_info:
            raise Exception(f"知识库 UUID {kb_uuid} 不存在")

        kb_dir_path = os.path.join(VEC_BASE_PATH, kb_info['kb_dir'])
        shutil.rmtree(kb_dir_path)
        del self.kb_metadata[kb_uuid]
        self.save_kb_metadata()

    def generate_vectors(self, kb_uuid):
        kb_info = self.kb_metadata.get(kb_uuid)
        if not kb_info:
            raise Exception(f"知识库 UUID {kb_uuid} 不存在")

        kb_dir_path = os.path.join(VEC_BASE_PATH, kb_info['kb_dir'])
        files = kb_info.get('files', {})

        total_files = len(files)
        if total_files == 0:
            logging.error(f"No files to process in knowledge base: {kb_info['kb_name']}")
            raise Exception(f"No files to process in knowledge base: {kb_info['kb_name']}")
        processed_files = 0

        # 处理文件向量化
        for file_uuid, file_info in files.items():
            file_path = os.path.join(kb_dir_path, file_info['file_path'])
            source_filename = file_info['filename']
            logging.info(f"Processing file {processed_files + 1}/{total_files}: {file_path}")
            processor = DocumentProcessor(file_path)

            processor.save_file_to_vec(kb_dir_path, source_filename, file_uuid)
            logging.info(f"File processed successfully: {file_path}")

            processed_files += 1

    def find_top_k_matches_in_kb(self, kb_uuid, user_query, k=5):
        kb_info = self.kb_metadata.get(kb_uuid)
        if not kb_info:
            raise Exception(f"知识库 UUID {kb_uuid} 不存在")

        vecs_path = os.path.join(VEC_BASE_PATH, kb_info['kb_dir'], 'vecs', 'vecs.json')
        if not os.path.exists(vecs_path):
            raise Exception(f"向量库文件不存在: {vecs_path}")

        # 创建DocumentProcessor实例
        processor = DocumentProcessor("")
        # 调用DocumentProcessor中的find_top_k_matches方法
        top_k_matches = processor.find_top_k_matches(user_query, vecs_path, k)
        logging.info(f"在知识库 {kb_uuid} 中为查询 '{user_query}' 找到前 {k} 个匹配项")
        return top_k_matches

    def clear_all_kbs(self):
        logging.info(f"Clearing all KBs")
        # 收集所有要删除的键
        keys_to_delete = list(self.kb_metadata.keys())

        # 遍历并删除每个键对应的知识库
        for kb_uuid in keys_to_delete:
            self.delete_kb(kb_uuid)
        logging.info(f"Cleared all KBs")

    def crete_graph_kb(self, kb_uuid, allow_nodes=None, allow_relationships=None, strict_mode=False):
        vec_metadata = self.get_vec_metadata(kb_uuid)
        if not vec_metadata:
            raise Exception(f"向量库文件不存在: {kb_uuid}")

        docs = []
        for item in vec_metadata:
            """数据示例
            {
                "id": "2438a50599c24a9b1018e02fe90159bb72c8a1946295d642fbda87b954a316c4",
                "text": "3 矿大知识平台 矿大知识平台 第一章 系统描述 1.1系统价值 矿大知识平台软件系统，作为一款集大成者的学习与研究辅助工具，深度整合并优化了来自全球各地的多样化知识信息资源，旨在为用户构建一个全面、便捷且高效的知识获取与应用环境。该系统不仅是一个庞大的知识库，更是一个智能化的知识管理与服务平台，它利用先进的信息技术手段，实现了知识的系统化整合与智能化管理，极大地提升了知识检索、利用与创新的效率。本系统主要功能包括：智能对话功能、知识图谱的可视化展示功能、多种文件格式的上传与存储功能、多模式对话功能、系统设置功能等。 智能对话功能是该平台的一大亮点，它基于自然语言处理技术，使得用户能够以日常交流的方式与系统进行互动，无论是查询特定知识点、获取最新资讯，还是提出研究疑问，系统都能迅速响应，提供准确且即时的信息反馈。这种人性化的交互方式不仅极大地降低了知识获取的难度，还显著提升了用户的使用体验和学习效率。",
                "embedding": [
                    -0.28859978914260864,
                    -0.3017699122428894,
                    ...
                ],
                "source_filename": "说明文档.docx",
                "source_url": "/get_file?file_uuid=8f614339-bfa7-45ed-ace8-705a8ec37273"
            },
            """
            logging.debug(item)
            doc = create_document_from_item(item)
            docs.append(doc)

        from langchain_community.chat_models import ChatOpenAI

        llm = ChatOpenAI(
            temperature=0,
            model="gpt-3.5-turbo",
            openai_api_key="sk-yYmSZsReFPFe09KtH1G1W4UQtzGK4HvkR1hr1yB0yFxpLNnQ",
            openai_api_base="https://yunwu.ai/v1"
        )

        # 初始化图谱转换器
        transformer = LLMGraphTransformer(
            llm=llm,
            allowed_nodes=allow_nodes,
            allowed_relationships=allow_relationships,
            strict_mode=False
        )

        res = transformer.convert_to_graph_documents(docs)
        for item in res:
            logging.debug(item)






# 使用示例
if __name__ == "__main__":
    # kb = KnowledgeBase()
    # kb_uuid = kb.create_kb("Example Knowledge Base", "This is an example description.")
    # file_uuid = kb.upload_file(kb_uuid, open(r"D:\xz\大创\矿大智慧助手\代码\langchain-graph-builder\assets\README.md", "rb"), "example_file.txt")
    # file_path = kb.get_file(kb_uuid, file_uuid)
    # kb.generate_vectors(kb_uuid)
    # kb.delete_kb(kb_uuid)

    kb = KnowledgeBase()
    # kb_uuid = "0d5da1ec-9b18-4d5b-b1c2-52ab4d38fd1f"
    # kb_uuid = "46bf6875-d24c-44c3-b33c-ccc30bc19f38"
    # print(kb.has_vec_file(kb_uuid))

    # kb.clear_all_kbs()