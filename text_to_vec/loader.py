import os
import re
import json
import numpy as np
import hashlib
import logging
from config import *
from langchain.document_loaders import (
    TextLoader,
    CSVLoader,
    DirectoryLoader,
    BSHTMLLoader,
    JSONLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader
)
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceBgeEmbeddings

class DocumentProcessor:
    def __init__(self, file_path, chunck_size=500, chunk_overlap=100):
        self.file_path = file_path
        self.document = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunck_size,
            chunk_overlap=chunk_overlap
        )
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=EMBEDDING_MODEL_PATH
        )
        self.vec_base_dir = VEC_BASE_PATH

    def load_document(self):
        file_extension = self.file_path.split('.')[-1].lower()
        loader = self.get_loader(file_extension)
        if loader:
            self.document = loader.load()
            logging.info(f"Document loaded from {self.file_path}")
            return self.document
        else:
            logging.error(f"Unsupported file extension: {file_extension}")
            raise ValueError(f"Unsupported file extension: {file_extension}")

    def get_loader(self, file_extension):
        loaders = {
            'txt': TextLoader,
            'md': TextLoader,
            'csv': CSVLoader,
            'xlsx': UnstructuredExcelLoader,
            'html': BSHTMLLoader,
            'json': JSONLoader,
            'pdf': PyPDFLoader,
            'docx': Docx2txtLoader
        }
        loader_class = loaders.get(file_extension)
        if loader_class:
            return loader_class(self.file_path)
        return None

    def get_text_content(self):
        if self.document:
            return '\n'.join([doc.page_content for doc in self.document])
        else:
            logging.error("Document not loaded. Call load_document first.")
            raise ValueError("Document not loaded. Call load_document first.")

    def clean_text(self, text):
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        logging.info("Text cleaned")
        return cleaned_text

    def split_text(self, text):
        text_chunks = self.text_splitter.split_text(text)
        logging.info(f"Text split into {len(text_chunks)} chunks")
        return text_chunks

    def embed_text(self, text_chunks):
        embeddings = self.embeddings.embed_documents(text_chunks)
        logging.info(f"Embedded {len(text_chunks)} text chunks")
        return embeddings

    def generate_unique_id(self, text):
        unique_id = hashlib.sha256(text.encode()).hexdigest()
        return unique_id

    def process_document(self):
        self.load_document()
        text_content = self.get_text_content()
        cleaned_content = self.clean_text(text_content)
        text_chunks = self.split_text(cleaned_content)
        embeddings = self.embed_text(text_chunks)
        result = [
            {
                "id": self.generate_unique_id(chunk),
                "text": chunk,
                "embedding": embedding
            }
            for chunk, embedding in zip(text_chunks, embeddings)
        ]
        logging.info(f"Processed document: {self.file_path}")
        return result

    def load_vector_library(self, vector_library_path):
        with open(vector_library_path, 'r', encoding='utf-8') as f:
            vector_library = json.load(f)
        logging.info(f"Vector library loaded from {vector_library_path}")
        return vector_library

    def calculate_cosine_similarity(self, user_query_embedding, vector_library):
        similarities = []
        for entry in vector_library:
            embedding = np.array(entry['embedding'])
            similarity = np.dot(user_query_embedding, embedding) / (np.linalg.norm(user_query_embedding) * np.linalg.norm(embedding))
            similarities.append((entry['id'], entry['text'], similarity))
        logging.info("Cosine similarities calculated")
        return similarities

    def find_top_k_matches(self, user_query, vector_library_path, k=5):
        user_query_embedding = self.embeddings.embed_query(user_query)
        vector_library = self.load_vector_library(vector_library_path)
        similarities = self.calculate_cosine_similarity(user_query_embedding, vector_library)
        top_k_matches = sorted(similarities, key=lambda x: x[2], reverse=True)[:k]
        logging.info(f"Top {k} matches found for query: {user_query}")
        return top_k_matches

    def init_vec(self, kb_dir_path):
        logging.info(f"Initializing vector library for {kb_dir_path}")
        vecs_path = os.path.join(kb_dir_path, 'vecs')
        if not os.path.exists(vecs_path):
            os.makedirs(vecs_path)
        output_file = os.path.join(vecs_path, "vecs.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        logging.info(f"Vector library initialized for {kb_dir_path}")

    def save_file_to_vec(self, kb_dir_path, source_filename, source_id, kb_uuid):
        result = self.process_document()
        vecs_path = os.path.join(kb_dir_path, 'vecs')
        if not os.path.exists(vecs_path):
            os.makedirs(vecs_path)

        for item in result:
            item['source_filename'] = source_filename
            item['file_uuid'] = source_id
            item['kb_uuid'] = kb_uuid

        output_file = os.path.join(vecs_path, "vecs.json")
        with open(output_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
        content.extend(result)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
        logging.info(f"Processed content saved to {output_file}")

# 示例使用
if __name__ == "__main__":
    file_paths = [
        r"D:\xz\大创\矿大智慧助手\代码\langchain-graph-builder\assets\README.MD",
        # "example.csv",
        # "example.xlsx",
        # "example.html",
        # "example.json",
        # "example.pdf",
        # "example.docx"
    ]

    vector_library_path = r"D:\xz\大创\矿大智慧助手\代码\langchain-graph-builder\assets\README_processed.json"

    for file_path in file_paths:
        processor = DocumentProcessor(file_path)
        try:
            result = processor.process_document()
            output_file = f"{os.path.splitext(file_path)[0]}_processed.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            logging.info(f"Processed content saved to {output_file}")
        except ValueError as e:
            logging.error(e)

    user_query = "如何使用这个工具？"
    top_k_matches = processor.find_top_k_matches(user_query, vector_library_path, k=5)
    logging.info(f"Top 5 matches for the query '{user_query}':")
    for match in top_k_matches:
        logging.info(f"ID: {match[0]}, Text: {match[1]}, Similarity: {match[2]}")


