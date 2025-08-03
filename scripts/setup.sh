#!/bin/bash

# Script de setup para o projeto Orquestra de Agentes

echo "🚀 Configurando Orquestra de Agentes para Análise de Crédito"
echo "============================================================"

# Verificar se Python 3.11+ está instalado
echo "🐍 Verificando Python..."
python_version=$(python3 --version 2>&1 | grep -oP 'Python \K[0-9]+\.[0-9]+')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version encontrado"
else
    echo "❌ Python 3.11+ é necessário. Versão atual: $python_version"
    exit 1
fi

# Instalar Poetry se não estiver instalado
if ! command -v poetry &> /dev/null; then
    echo "📦 Instalando Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "✅ Poetry já está instalado"
fi

# Instalar dependências
echo "📦 Instalando dependências..."
poetry install

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "⚙️ Criando arquivo .env..."
    cp env.example .env
    echo "✅ Arquivo .env criado. Configure suas API keys!"
else
    echo "✅ Arquivo .env já existe"
fi

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p data/vector_store
mkdir -p data/uploads
mkdir -p logs

# Instalar dependências do sistema (Ubuntu/Debian)
if command -v apt-get &> /dev/null; then
    echo "🔧 Instalando dependências do sistema..."
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-por poppler-utils
fi

# Instalar dependências do sistema (macOS)
if command -v brew &> /dev/null; then
    echo "🔧 Instalando dependências do sistema (macOS)..."
    brew install tesseract tesseract-lang poppler
fi

echo ""
echo "✅ Setup concluído!"
echo ""
echo "📋 Próximos passos:"
echo "1. Configure suas API keys no arquivo .env:"
echo "   - OPENAI_API_KEY=sua_chave_aqui"
echo "   - ANTHROPIC_API_KEY=sua_chave_aqui (opcional)"
echo "   - TAVILY_API_KEY=sua_chave_aqui (opcional)"
echo ""
echo "2. Execute os testes:"
echo "   poetry run pytest"
echo ""
echo "3. Inicie a aplicação:"
echo "   poetry run uvicorn src.main:app --reload"
echo ""
echo "4. Acesse a documentação da API:"
echo "   http://localhost:8000/docs"
echo ""
echo "🎉 Pronto para usar!"