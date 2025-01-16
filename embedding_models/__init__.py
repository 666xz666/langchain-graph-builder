from langchain.embeddings import HuggingFaceBgeEmbeddings
from config import EMBEDDING_MODEL_PATH, DEVICE


class EmbeddingLoader:
    def __init__(self):
        self.embedding = None

    def load_embedding_models(self):
        if self.embedding is None:
            self.embedding = HuggingFaceBgeEmbeddings(
                model_name=EMBEDDING_MODEL_PATH,
                model_kwargs={'device': DEVICE}
            )

    def get_embedding_model(self):
        if self.embedding is None:
            self.load_embedding_models()
        return self.embedding


embedding_loader = EmbeddingLoader()
