"""Testes para as ferramentas do sistema."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import aiohttp

from src.models.schemas import DocumentType


class TestCNPJApiClient:
    """Testes para o cliente de API de CNPJ."""
    
    @pytest.fixture
    def cnpj_client(self):
        from src.tools.cnpj_api import CNPJApiClient
        return CNPJApiClient()
    
    def test_clean_cnpj(self, cnpj_client):
        """Testa limpeza de CNPJ."""
        assert cnpj_client._clean_cnpj("11.222.333/0001-81") == "11222333000181"
        assert cnpj_client._clean_cnpj("11222333000181") == "11222333000181"
        assert cnpj_client._clean_cnpj("11.222.333/0001-81abc") == "11222333000181"
    
    @pytest.mark.asyncio
    async def test_get_company_data_success(self, cnpj_client):
        """Testa busca bem-sucedida de dados da empresa."""
        mock_response_data = {
            "cnpj": "11.222.333/0001-81",
            "nome": "Empresa Teste LTDA",
            "situacao": "ATIVA",
            "abertura": "01/01/2020",
            "capital_social": "100.000,00"
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await cnpj_client._get_from_receitaws("11222333000181")
            
            assert result is not None
            assert result.cnpj == "11.222.333/0001-81"
            assert result.corporate_name == "Empresa Teste LTDA"
    
    @pytest.mark.asyncio
    async def test_get_company_data_api_error(self, cnpj_client):
        """Testa tratamento de erro da API."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await cnpj_client._get_from_receitaws("11222333000181")
            
            assert result is None


class TestWebSearchTool:
    """Testes para a ferramenta de busca web."""
    
    @pytest.fixture
    def web_search_tool(self):
        from src.tools.web_search import WebSearchTool
        return WebSearchTool()
    
    @pytest.mark.asyncio
    async def test_search_company_news_no_api_key(self, web_search_tool):
        """Testa busca sem API key configurada."""
        # Simular ausência de API key
        web_search_tool.tavily_client = None
        
        results = await web_search_tool.search_company_news("11222333000181", "Empresa Teste")
        
        assert isinstance(results, list)
        assert len(results) == 0  # Sem API key, deve retornar lista vazia
    
    @pytest.mark.asyncio
    async def test_search_with_tavily_success(self, web_search_tool):
        """Testa busca bem-sucedida com Tavily."""
        mock_tavily_response = {
            "results": [
                {
                    "url": "https://example.com/news1",
                    "title": "Empresa em destaque",
                    "content": "Conteúdo da notícia sobre a empresa",
                    "score": 0.9
                }
            ]
        }
        
        mock_client = Mock()
        mock_client.search.return_value = mock_tavily_response
        web_search_tool.tavily_client = mock_client
        
        results = await web_search_tool._search_with_tavily("test query", "news")
        
        assert len(results) == 1
        assert results[0].url == "https://example.com/news1"
        assert results[0].search_type == "news"


class TestDocumentProcessor:
    """Testes para o processador de documentos."""
    
    @pytest.fixture
    def document_processor(self):
        from src.tools.document_processor import DocumentProcessor
        return DocumentProcessor()
    
    def test_get_file_extension(self, document_processor):
        """Testa extração de extensão de arquivo."""
        assert document_processor._get_file_extension("test.pdf") == ".pdf"
        assert document_processor._get_file_extension("document.DOCX") == ".docx"
        assert document_processor._get_file_extension("image.PNG") == ".png"
    
    def test_identify_document_type(self, document_processor):
        """Testa identificação de tipo de documento."""
        balance_text = "BALANÇO PATRIMONIAL ATIVO CIRCULANTE PASSIVO PATRIMÔNIO LÍQUIDO"
        assert document_processor._identify_document_type(balance_text) == DocumentType.BALANCE_SHEET
        
        dre_text = "DEMONSTRAÇÃO DO RESULTADO RECEITA LÍQUIDA LUCRO LÍQUIDO"
        assert document_processor._identify_document_type(dre_text) == DocumentType.INCOME_STATEMENT
        
        random_text = "Texto qualquer sem palavras-chave financeiras específicas"
        assert document_processor._identify_document_type(random_text) == DocumentType.OTHER
    
    def test_extract_values_with_patterns(self, document_processor):
        """Testa extração de valores com regex."""
        text = "RECEITA LÍQUIDA: 1.500.000,00 LUCRO BRUTO: 450.000,50"
        patterns = {
            "revenue": r"receita\s+líquida\s*[:\-]?\s*([\d\.,]+)",
            "gross_profit": r"lucro\s+bruto\s*[:\-]?\s*([\d\.,]+)"
        }
        
        results = document_processor._extract_values_with_patterns(text, patterns)
        
        assert results["revenue"] == 1500000.0
        assert results["gross_profit"] == 450000.5
    
    @pytest.mark.asyncio
    async def test_process_document_unsupported_format(self, document_processor):
        """Testa processamento de formato não suportado."""
        with pytest.raises(ValueError, match="não suportado"):
            await document_processor.process_document(b"content", "test.xyz")


class TestVectorStore:
    """Testes para o vector store."""
    
    @pytest.fixture
    def vector_store(self):
        import tempfile
        from src.tools.vector_store import VectorStore
        
        with patch("src.tools.vector_store.OpenAIEmbeddings"):
            store_path = tempfile.mkdtemp()
            return VectorStore(store_path)
    
    def test_initialization(self, vector_store):
        """Testa inicialização do vector store."""
        assert vector_store.documents == []
        assert vector_store.metadata == []
        assert vector_store.index is None
    
    def test_add_document(self, vector_store):
        """Testa adição de documento."""
        # Mock embeddings
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        vector_store.embeddings_model.embed_documents = Mock(return_value=mock_embeddings)
        
        text = "Este é um documento de teste com conteúdo financeiro relevante."
        metadata = {"filename": "test.pdf", "type": "balance_sheet"}
        
        vector_store.add_document(text, metadata)
        
        assert len(vector_store.documents) > 0
        assert len(vector_store.metadata) > 0
        assert vector_store.index is not None
    
    def test_search_empty_store(self, vector_store):
        """Testa busca em vector store vazio."""
        results = vector_store.search("test query")
        assert results == []
    
    def test_clear(self, vector_store):
        """Testa limpeza do vector store."""
        # Adicionar alguns dados primeiro
        vector_store.documents = ["doc1", "doc2"]
        vector_store.metadata = [{"id": 1}, {"id": 2}]
        
        vector_store.clear()
        
        assert vector_store.documents == []
        assert vector_store.metadata == []
        assert vector_store.index is None