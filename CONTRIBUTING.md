# Contribuindo para a Orquestra de Agentes

Obrigado pelo interesse em contribuir! Este documento fornece diretrizes para contribuições.

## 🚀 Como Contribuir

### 1. Configuração do Ambiente

```bash
# Clone o repositório
git clone <repo-url>
cd orquestra-agentes-financeiros

# Execute o setup
./scripts/setup.sh

# Configure as API keys no .env
cp env.example .env
# Edite .env com suas chaves
```

### 2. Desenvolvimento

#### Estrutura do Projeto
```
src/
├── agents/           # Agentes especializados
├── tools/            # Ferramentas e APIs
├── graph/            # Orquestração LangGraph
├── models/           # Modelos Pydantic
└── main.py           # API FastAPI
```

#### Standards de Código

- **Python 3.11+**
- **Type hints** obrigatórios
- **Docstrings** em português para classes e métodos públicos
- **Black** para formatação
- **isort** para organização de imports
- **flake8** para linting
- **pytest** para testes

#### Executar Testes

```bash
# Testes completos
./scripts/run_tests.sh

# Apenas testes
poetry run pytest

# Com cobertura
poetry run pytest --cov=src
```

### 3. Tipos de Contribuição

#### 🐛 Bug Reports
- Use os templates de issue
- Inclua logs relevantes
- Descreva o comportamento esperado vs atual

#### ✨ Novas Features
- Abra uma issue primeiro para discussão
- Siga o padrão de agentes existentes
- Inclua testes e documentação

#### 📚 Documentação
- Notebooks Jupyter para demonstrações
- Docstrings em português
- README e arquivos de configuração

#### 🧪 Testes
- Testes unitários para cada agente
- Testes de integração para fluxos completos
- Mocks para APIs externas

## 🔧 Padrões de Desenvolvimento

### Criando um Novo Agente

```python
from src.agents.base_agent import BaseAgent
from src.models.schemas import AgentState

class MeuNovoAgent(BaseAgent):
    def __init__(self):
        super().__init__("MeuNovo")
    
    async def execute(self, state: AgentState) -> AgentState:
        try:
            self.add_processing_note(state, "Iniciando processamento")
            
            # Sua lógica aqui
            
            return state
        except Exception as e:
            return await self.handle_error(state, e)
```

### Adicionando uma Nova Tool

```python
class MinhaNovaFerramenta:
    async def processar(self, dados):
        # Implementação
        pass

# Singleton
minha_ferramenta = MinhaNovaFerramenta()
```

### Padrões de Teste

```python
import pytest
from unittest.mock import patch, AsyncMock

class TestMeuAgent:
    @pytest.fixture
    def agent(self):
        return MeuAgent()
    
    @pytest.mark.asyncio
    async def test_execute_success(self, agent, sample_state):
        result = await agent.execute(sample_state)
        assert result is not None
```

## 📝 Commit Guidelines

### Formato
```
<tipo>(<escopo>): <descrição>

<corpo opcional>

<footer opcional>
```

### Tipos
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação
- `refactor`: Refatoração
- `test`: Testes
- `chore`: Manutenção

### Exemplos
```bash
feat(agents): adicionar agente de análise setorial
fix(api): corrigir validação de CNPJ
docs(readme): atualizar instruções de instalação
test(tools): adicionar testes para vector store
```

## 🔍 Code Review

### Checklist do Reviewer
- [ ] Código segue os padrões estabelecidos
- [ ] Testes adequados incluídos
- [ ] Documentação atualizada
- [ ] Performance considerada
- [ ] Tratamento de erros apropriado
- [ ] Compatibilidade com APIs existentes

### Checklist do Autor
- [ ] Testes passando localmente
- [ ] Linting sem erros
- [ ] Documentação atualizada
- [ ] Commit messages claros
- [ ] Branch atualizada com main

## 🚦 CI/CD

O pipeline inclui:
- Linting (black, isort, flake8)
- Type checking (mypy)
- Testes unitários e integração
- Build Docker
- Deploy automático (main branch)

## 📋 Roadmap

### Próximas Features
- [ ] Suporte a mais tipos de documento
- [ ] Cache distribuído para embeddings
- [ ] Dashboard de monitoramento
- [ ] API de webhooks
- [ ] Análise de séries temporais

### Melhorias Técnicas
- [ ] Otimização de performance
- [ ] Monitoring avançado
- [ ] Testes de carga
- [ ] Documentação OpenAPI

## 🆘 Precisa de Ajuda?

- 📖 Leia a documentação completa
- 🧪 Execute os notebooks de exemplo
- 💬 Abra uma issue para discussão
- 📧 Entre em contato com a equipe

## 📜 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a mesma licença do projeto.

---

**Obrigado por contribuir! 🎉**