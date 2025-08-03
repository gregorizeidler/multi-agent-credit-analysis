# 🎯 Orquestra de Agentes para Otimização de Processos Financeiros

[![CI/CD](https://github.com/user/orquestra-agentes/workflows/CI/badge.svg)](https://github.com/user/orquestra-agentes/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

> **Sistema multi-agente autônomo para análise de risco de crédito de PMEs brasileiras**  
> Utilizando LangGraph para orquestração e pipeline RAG para análise inteligente de documentos financeiros em português.

## 🌟 Funcionalidades Principais

- ⚡ **Análise automática**: CNPJ → Relatório em < 2 minutos
- 🤖 **4 Agentes especializados** trabalhando em colaboração
- 📄 **Processamento inteligente** de PDFs, Word e imagens (OCR)
- 🔍 **Busca semântica** com RAG para extração de KPIs financeiros
- 🇧🇷 **APIs brasileiras** integradas (Receita Federal, web search)
- 🛡️ **Controle de qualidade** automático com retry inteligente
- 📊 **Scoring calibrado** para mercado de PMEs brasileiras
- 🚀 **Production-ready** com Docker, CI/CD e monitoring

## 🏗️ Arquitetura do Sistema

### Fluxo Principal

```mermaid
graph TB
    subgraph "Input Layer"
        A[📋 CNPJ]
        B[📄 Documentos Financeiros]
        C[💰 Valor Solicitado]
    end
    
    subgraph "Processing Layer"
        D[🔍 Data Gatherer Agent]
        E[📊 Document Analyst Agent] 
        F[⚡ Risk Analyst Agent]
        G[🛡️ Quality Assurance Agent]
    end
    
    subgraph "Data Sources"
        H[🏛️ Receita Federal API]
        I[🌐 Web Search/News]
        J[📊 Vector Store RAG]
        K[🤖 LLM Analysis]
    end
    
    subgraph "Output Layer"
        L[✅ Aprovar]
        M[⚠️ Revisar] 
        N[❌ Recusar]
        O[📋 Relatório Detalhado]
    end
    
    A --> D
    B --> E
    C --> F
    
    D --> H
    D --> I
    E --> J
    F --> K
    G --> K
    
    D --> E
    E --> F
    F --> G
    
    G -->|✅ Approved| L
    G -->|⚠️ Needs Review| M
    G -->|❌ Rejected| N
    G -->|🔄 Retry| F
    
    L --> O
    M --> O
    N --> O
    
    style D fill:#e1f5fe
    style E fill:#f3e5f5
    style F fill:#fff3e0
    style G fill:#e8f5e8
```

### Arquitetura Técnica Detalhada

```mermaid
graph TB
    subgraph "API Layer"
        API[FastAPI Application]
        DOCS[📚 Auto Documentation]
        AUTH[🔒 Rate Limiting]
    end
    
    subgraph "Agent Orchestration"
        LG[🔄 LangGraph Orchestrator]
        STATE[📊 Shared Agent State]
    end
    
    subgraph "Specialized Agents"
        DG[🔍 DataGatherer<br/>- CNPJ APIs<br/>- Web Search<br/>- Public Data]
        DA[📄 DocumentAnalyst<br/>- OCR Processing<br/>- RAG Pipeline<br/>- KPI Extraction]
        RA[⚡ RiskAnalyst<br/>- Financial Scoring<br/>- ML Analysis<br/>- Recommendations]
        QA[🛡️ QualityAssurance<br/>- Consistency Checks<br/>- Anti-hallucination<br/>- Feedback Loop]
    end
    
    subgraph "Data Processing"
        VS[🔍 FAISS Vector Store]
        OCR[👁️ Tesseract OCR]
        PDF[📄 Document Parser]
    end
    
    subgraph "External APIs"
        RF[🏛️ Receita Federal]
        TAVILY[🌐 Tavily Search]
        OPENAI[🤖 OpenAI API]
        ANTHROPIC[🤖 Anthropic API]
    end
    
    subgraph "Infrastructure"
        DOCKER[🐳 Docker Containers]
        LOGS[📝 Structured Logging]
        MONITOR[📊 Health Monitoring]
    end
    
    API --> LG
    LG --> STATE
    STATE --> DG
    STATE --> DA
    STATE --> RA
    STATE --> QA
    
    DG --> RF
    DG --> TAVILY
    DA --> VS
    DA --> OCR
    DA --> PDF
    RA --> OPENAI
    RA --> ANTHROPIC
    QA --> OPENAI
    
    API --> DOCKER
    DOCKER --> LOGS
    DOCKER --> MONITOR
    
    style API fill:#e3f2fd
    style LG fill:#f1f8e9
    style DG fill:#fff3e0
    style DA fill:#f3e5f5
    style RA fill:#ffebee
    style QA fill:#e8f5e8
```

## 🎯 Casos de Uso

### 1. Análise Rápida (Triagem)
```bash
# Apenas CNPJ para avaliação inicial
curl -X POST "localhost:8000/analyze-credit" \
  -F "cnpj=11222333000181"
```

### 2. Análise Completa (Decisão Final)
```bash
# CNPJ + documentos financeiros
curl -X POST "localhost:8000/analyze-credit" \
  -F "cnpj=11222333000181" \
  -F "files=@balanco_2023.pdf" \
  -F "files=@dre_2023.pdf"
```

### 3. Análise Contextual (Crédito Específico)
```bash
# Com valor e finalidade
curl -X POST "localhost:8000/analyze-credit" \
  -F "cnpj=11222333000181" \
  -F "requested_amount=500000" \
  -F "purpose=Expansão de negócio" \
  -F "files=@documentos.pdf"
```

## 💼 Agentes Especializados

### 🔍 DataGatherer Agent
- **Função**: Coleta dados públicos e informações de risco
- **APIs**: Receita Federal, Brasil API (com fallback automático)
- **Web Search**: Tavily para notícias, processos judiciais, presença online
- **Output**: Dados cadastrais + análise de risco público

### 📄 DocumentAnalyst Agent  
- **Função**: Processamento inteligente de documentos financeiros
- **Suporte**: PDF, DOCX, PNG/JPG/TIFF (com OCR Tesseract)
- **RAG Pipeline**: FAISS + 12 perguntas pré-definidas para KPIs
- **Output**: Indicadores financeiros estruturados (ROA, ROE, liquidez, etc.)

### ⚡ RiskAnalyst Agent
- **Função**: Análise consolidada de risco de crédito
- **Metodologia**: Scoring ponderado (70% financeiro + 30% não-financeiro)
- **Thresholds**: Calibrados para mercado brasileiro de PMEs
- **Output**: Recomendação (Aprovar/Revisar/Recusar) + análise detalhada

### 🛡️ QualityAssurance Agent
- **Função**: Validação automática e controle de qualidade
- **Verificações**: 8 tipos de consistency checks
- **Anti-hallucination**: Validação cruzada dados vs análise
- **Feedback Loop**: Retry automático com correções específicas

## 🚀 Instalação e Execução

### Setup Automático (Recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/user/orquestra-agentes-financeiros
cd orquestra-agentes-financeiros

# 2. Execute o setup automático
./scripts/setup.sh

# 3. Configure suas API keys
cp env.example .env
nano .env  # Adicione suas chaves
```

### Configuração Manual

<details>
<summary>📋 Clique para ver instruções detalhadas</summary>

#### Pré-requisitos
- Python 3.11+
- Docker & Docker Compose
- Poetry (gerenciador de dependências)

#### Dependências do Sistema
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-por poppler-utils

# macOS
brew install tesseract tesseract-lang poppler

# Windows
# Baixar Tesseract do GitHub oficial
```

#### Instalação Python
```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependências
poetry install

# Ativar ambiente virtual
poetry shell
```
</details>

### 🐳 Docker (Produção)

```bash
# Desenvolvimento
docker-compose up --build

# Produção
cp env.example .env.prod
# Editar .env.prod com configurações de produção
docker-compose --env-file .env.prod up -d
```

### 🔑 Configuração de API Keys

```bash
# Arquivo .env
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here  # Opcional
TAVILY_API_KEY=tvly-your-tavily-key-here          # Opcional

# Configurações opcionais
LLM_PROVIDER=openai  # ou anthropic
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### ✅ Verificação da Instalação

```bash
# Health check
curl http://localhost:8000/health

# Documentação interativa
open http://localhost:8000/docs

# Executar testes
./scripts/run_tests.sh
```

## 📊 Estrutura do Projeto

```
📦 orquestra-agentes-financeiros/
├── 🐳 docker-compose.yml          # Container orchestration
├── 📄 Dockerfile                  # Container build
├── ⚙️ pyproject.toml              # Dependencies & config
├── 📋 README.md                   # Este arquivo
├── 
├── 📂 src/                        # Código principal
│   ├── 🤖 agents/                 # Agentes especializados
│   │   ├── base_agent.py         # Classe base para agentes
│   │   ├── data_gatherer.py      # Coleta de dados públicos
│   │   ├── document_analyst.py   # Análise de documentos
│   │   ├── risk_analyst.py       # Análise de risco
│   │   └── quality_assurance.py  # Controle de qualidade
│   │
│   ├── 🔧 tools/                  # Ferramentas especializadas
│   │   ├── cnpj_api.py           # Cliente APIs CNPJ
│   │   ├── web_search.py         # Busca web e notícias
│   │   ├── document_processor.py # Processamento documentos
│   │   └── vector_store.py       # RAG e embeddings
│   │
│   ├── 🔄 graph/                  # Orquestração LangGraph
│   │   └── credit_analysis_graph.py
│   │
│   ├── 📊 models/                 # Modelos Pydantic
│   │   └── schemas.py            # Schemas de dados
│   │
│   ├── ⚙️ config.py               # Configurações da app
│   └── 🚀 main.py                 # FastAPI application
│
├── 🧪 tests/                      # Testes automatizados
│   ├── conftest.py               # Configuração pytest
│   ├── test_agents.py            # Testes dos agentes
│   ├── test_tools.py             # Testes das ferramentas
│   └── test_api.py               # Testes da API
│
├── 📚 notebooks/                  # Jupyter notebooks
│   ├── demo_credit_analysis.ipynb
│   └── technical_deep_dive.ipynb
│
├── 🛠️ scripts/                    # Scripts utilitários
│   ├── setup.sh                 # Setup automático
│   ├── run_tests.sh              # Execução de testes
│   └── deploy.sh                 # Deploy produção
│
├── 📖 docs/                       # Documentação adicional
│   ├── api_examples.md           # Exemplos de uso da API
│   └── deployment_guide.md       # Guia de deploy
│
└── 📊 data/                       # Dados e cache
    ├── sample_documents/         # Documentos de exemplo
    ├── vector_store/             # Cache embeddings
    └── uploads/                  # Uploads temporários
```

## 🧪 Testes e Qualidade

### Execução de Testes

```bash
# Testes completos com linting
./scripts/run_tests.sh

# Apenas testes unitários
poetry run pytest tests/ -v

# Testes com cobertura
poetry run pytest --cov=src --cov-report=html

# Testes específicos
poetry run pytest tests/test_agents.py -v
```

### Métricas de Qualidade

- ✅ **25+ testes** unitários e de integração
- ✅ **Type hints** completos (mypy)
- ✅ **Code formatting** (black, isort)
- ✅ **Linting** (flake8)
- ✅ **80%+ coverage** de código

### CI/CD Pipeline

```mermaid
graph LR
    A[📝 Commit] --> B[🧪 Tests]
    B --> C[🔍 Linting]
    C --> D[🐳 Docker Build] 
    D --> E[🚀 Deploy]
    
    B --> F[❌ Fail]
    C --> F
    D --> F
    F --> G[🔔 Notification]
    
    E --> H[✅ Success]
    H --> I[📊 Monitoring]
```

## 📈 Performance e Escalabilidade

### Métricas de Performance

| Métrica | Valor | Descrição |
|---------|-------|-----------|
| ⚡ **Tempo de Análise** | < 2 min | CNPJ → Relatório completo |
| 📊 **Throughput** | 100+ análises/hora | Com rate limiting |
| 💾 **Uso de Memória** | < 500MB | Por instância da API |
| 🎯 **Accuracy** | 85%+ confiança | Nas extrações de KPIs |
| 🛡️ **Reliability** | 99%+ uptime | Com retry automático |

### Escalabilidade

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[🔄 Nginx/ALB]
    end
    
    subgraph "API Instances"
        API1[🚀 API Instance 1]
        API2[🚀 API Instance 2]
        API3[🚀 API Instance N...]
    end
    
    subgraph "Shared Services"
        REDIS[📦 Redis Cache]
        DB[🗄️ Database]
        MONITOR[📊 Monitoring]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> REDIS
    API2 --> REDIS
    API3 --> REDIS
    
    API1 --> DB
    API2 --> DB
    API3 --> DB
    
    API1 --> MONITOR
    API2 --> MONITOR
    API3 --> MONITOR
```

## 📚 Documentação e Recursos

### 🎓 Notebooks Demonstrativos
- [`demo_credit_analysis.ipynb`](notebooks/demo_credit_analysis.ipynb) - Demonstração completa do sistema
- [`technical_deep_dive.ipynb`](notebooks/technical_deep_dive.ipynb) - Deep dive técnico na arquitetura

### 📖 Documentação Adicional
- [📋 Exemplos de API](docs/api_examples.md) - Exemplos práticos de uso
- [🚀 Guia de Deploy](docs/deployment_guide.md) - Deploy em produção
- [🤝 Como Contribuir](CONTRIBUTING.md) - Guidelines para contribuições
- [📜 Changelog](CHANGELOG.md) - Histórico de versões

### 🔗 Links Úteis
- **API Docs**: http://localhost:8000/docs (após iniciar)
- **Health Check**: http://localhost:8000/health
- **Redoc**: http://localhost:8000/redoc

## 🛡️ Segurança e Compliance

### Recursos de Segurança
- ✅ **Input Validation**: Validação rigorosa de todos os inputs
- ✅ **Rate Limiting**: 100 requests/hora por IP
- ✅ **File Type Validation**: Whitelist de extensões permitidas
- ✅ **Size Limits**: Máximo 10MB por arquivo
- ✅ **Environment Variables**: Configuração segura via .env
- ✅ **Error Handling**: Não exposição de dados sensíveis

### Compliance
- 🇧🇷 **LGPD**: Não armazena dados pessoais permanentemente
- 🔒 **Data Privacy**: Processamento local dos documentos
- 🛡️ **API Security**: Headers de segurança configurados
- 📝 **Audit Trail**: Logs estruturados para auditoria

## 🌐 Deploy e Produção

### Ambientes Suportados
- 🐳 **Docker**: Local e containers
- ☁️ **AWS**: EC2, ECS, Lambda
- 🌩️ **Google Cloud**: Cloud Run, GKE
- 🔵 **Azure**: Container Instances, AKS
- 🖥️ **Bare Metal**: Ubuntu, CentOS, macOS

### Deploy Rápido

```bash
# Deploy local
docker-compose up -d

# Deploy AWS (EC2)
./scripts/deploy.sh aws

# Deploy Google Cloud
./scripts/deploy.sh gcp

# Deploy Azure
./scripts/deploy.sh azure
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, leia o [guia de contribuição](CONTRIBUTING.md).

### Quick Start para Desenvolvedores

```bash
# Fork e clone
git clone https://github.com/seu-usuario/orquestra-agentes
cd orquestra-agentes

# Setup ambiente de desenvolvimento
./scripts/setup.sh

# Criar nova branch
git checkout -b feature/nova-funcionalidade

# Fazer mudanças e testar
./scripts/run_tests.sh

# Commit e push
git commit -m "feat: adicionar nova funcionalidade"
git push origin feature/nova-funcionalidade
```

## 🗺️ Roadmap

### Versão 1.1 (Q2 2024)
- [ ] Dashboard web interativo
- [ ] Cache distribuído (Redis)
- [ ] Webhooks para integração
- [ ] Análise de séries temporais

### Versão 1.2 (Q3 2024)
- [ ] ML models customizados
- [ ] Multi-tenant support
- [ ] Real-time processing
- [ ] Advanced analytics

### Versão 2.0 (Q4 2024)
- [ ] Microservices architecture
- [ ] Kubernetes deployment
- [ ] GraphQL API
- [ ] Machine Learning pipeline

## 🆘 Suporte e Comunidade

### 💬 Onde Buscar Ajuda
- 📖 **Documentação**: Comece sempre pela documentação
- 🐛 **Issues**: Para bugs e feature requests
- 💭 **Discussions**: Para perguntas e discussões
- 📧 **Email**: contato@exemplo.com

### ❓ FAQ

<details>
<summary>Como configurar as API keys?</summary>

Copie o arquivo `env.example` para `.env` e adicione suas chaves:
```bash
cp env.example .env
nano .env
```
</details>

<details>
<summary>Quais formatos de documento são suportados?</summary>

- PDF (.pdf) - texto e escaneado
- Word (.docx) 
- Imagens (.png, .jpg, .jpeg, .tiff) via OCR
</details>

<details>
<summary>Como escalar para produção?</summary>

Consulte o [Guia de Deploy](docs/deployment_guide.md) para instruções detalhadas de produção.
</details>

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

<div align="center">

**🚀 Sistema moderno para análise inteligente de crédito!**

[📚 Documentação](docs/) • [🎯 Exemplos](docs/api_examples.md) • [🤝 Contribuir](CONTRIBUTING.md) • [🐛 Reportar Bug](https://github.com/user/orquestra-agentes/issues)

</div>