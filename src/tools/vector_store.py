"""Vector store para busca semântica em documentos usando FAISS."""

import os
import pickle
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from loguru import logger


class VectorStore:
    """Vector store usando FAISS para busca semântica em documentos."""
    
    def __init__(self, store_path: str = "./data/vector_store"):
        self.store_path = store_path
        self.embeddings_model = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Índice FAISS e metadados
        self.index: Optional[faiss.IndexFlatIP] = None
        self.documents: List[str] = []
        self.metadata: List[Dict[str, Any]] = []
        
        # Criar diretório se não existir
        os.makedirs(store_path, exist_ok=True)
        
        # Carregar índice existente se disponível
        self._load_index()
    
    def add_document(self, text: str, metadata: Dict[str, Any]) -> None:
        """Adiciona um documento ao vector store."""
        try:
            # Dividir o documento em chunks
            chunks = self.text_splitter.split_text(text)
            
            if not chunks:
                logger.warning("Nenhum chunk gerado para o documento")
                return
            
            # Gerar embeddings
            embeddings = self.embeddings_model.embed_documents(chunks)
            
            # Converter para numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Normalizar vetores para usar produto interno
            faiss.normalize_L2(embeddings_array)
            
            # Inicializar índice se necessário
            if self.index is None:
                dimension = embeddings_array.shape[1]
                self.index = faiss.IndexFlatIP(dimension)
            
            # Adicionar ao índice
            self.index.add(embeddings_array)
            
            # Salvar chunks e metadados
            for i, chunk in enumerate(chunks):
                self.documents.append(chunk)
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = i
                chunk_metadata['total_chunks'] = len(chunks)
                self.metadata.append(chunk_metadata)
            
            logger.info(f"Documento adicionado: {len(chunks)} chunks")
            
            # Salvar índice
            self._save_index()
            
        except Exception as e:
            logger.error(f"Erro ao adicionar documento ao vector store: {e}")
            raise
    
    def search(self, query: str, k: int = 5, threshold: float = 0.7) -> List[Tuple[str, Dict[str, Any], float]]:
        """
        Busca documentos similares à query.
        
        Returns:
            Lista de tuplas (chunk_text, metadata, score)
        """
        if self.index is None or len(self.documents) == 0:
            logger.warning("Vector store vazio")
            return []
        
        try:
            # Gerar embedding da query
            query_embedding = self.embeddings_model.embed_query(query)
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # Normalizar
            faiss.normalize_L2(query_vector)
            
            # Buscar
            scores, indices = self.index.search(query_vector, k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1 and score >= threshold:  # -1 indica que não foi encontrado
                    results.append((
                        self.documents[idx],
                        self.metadata[idx],
                        float(score)
                    ))
            
            logger.info(f"Busca retornou {len(results)} resultados para: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca do vector store: {e}")
            return []
    
    def ask_question(self, question: str, context_limit: int = 3) -> List[str]:
        """
        Faz uma pergunta e retorna os chunks mais relevantes.
        
        Args:
            question: Pergunta a ser feita
            context_limit: Número máximo de chunks a retornar
            
        Returns:
            Lista de chunks relevantes
        """
        results = self.search(question, k=context_limit)
        return [chunk for chunk, _, _ in results]
    
    def extract_financial_info(self, questions: List[str]) -> Dict[str, List[str]]:
        """
        Extrai informações financeiras específicas usando múltiplas perguntas.
        
        Args:
            questions: Lista de perguntas sobre dados financeiros
            
        Returns:
            Dicionário com respostas para cada pergunta
        """
        results = {}
        
        for question in questions:
            relevant_chunks = self.ask_question(question, context_limit=2)
            results[question] = relevant_chunks
        
        return results
    
    def clear(self) -> None:
        """Limpa o vector store."""
        self.index = None
        self.documents.clear()
        self.metadata.clear()
        
        # Remove arquivos salvos
        for filename in ['index.faiss', 'documents.pkl', 'metadata.pkl']:
            filepath = os.path.join(self.store_path, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        logger.info("Vector store limpo")
    
    def _save_index(self) -> None:
        """Salva o índice e metadados em disco."""
        try:
            if self.index is not None:
                # Salvar índice FAISS
                faiss.write_index(self.index, os.path.join(self.store_path, 'index.faiss'))
                
                # Salvar documentos e metadados
                with open(os.path.join(self.store_path, 'documents.pkl'), 'wb') as f:
                    pickle.dump(self.documents, f)
                
                with open(os.path.join(self.store_path, 'metadata.pkl'), 'wb') as f:
                    pickle.dump(self.metadata, f)
                
                logger.debug("Índice salvo com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar índice: {e}")
    
    def _load_index(self) -> None:
        """Carrega o índice e metadados do disco."""
        try:
            index_path = os.path.join(self.store_path, 'index.faiss')
            documents_path = os.path.join(self.store_path, 'documents.pkl')
            metadata_path = os.path.join(self.store_path, 'metadata.pkl')
            
            if all(os.path.exists(path) for path in [index_path, documents_path, metadata_path]):
                # Carregar índice FAISS
                self.index = faiss.read_index(index_path)
                
                # Carregar documentos e metadados
                with open(documents_path, 'rb') as f:
                    self.documents = pickle.load(f)
                
                with open(metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                
                logger.info(f"Índice carregado: {len(self.documents)} documentos")
            else:
                logger.info("Nenhum índice existente encontrado")
        except Exception as e:
            logger.warning(f"Erro ao carregar índice existente: {e}")
            # Em caso de erro, inicia com vector store vazio
            self.index = None
            self.documents.clear()
            self.metadata.clear()


# Função helper para criar instância com configuração
def create_vector_store(store_path: Optional[str] = None) -> VectorStore:
    """Cria uma instância do vector store."""
    if store_path is None:
        store_path = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")
    
    return VectorStore(store_path)