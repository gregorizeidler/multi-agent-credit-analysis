#!/bin/bash

# Script de deploy para produção

echo "🚀 Deploy da Orquestra de Agentes"
echo "================================="

# Verificar se está na branch main
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo "⚠️ Você não está na branch main. Branch atual: $current_branch"
    read -p "Deseja continuar? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deploy cancelado."
        exit 1
    fi
fi

# Verificar se há mudanças não commitadas
if ! git diff-index --quiet HEAD --; then
    echo "❌ Há mudanças não commitadas. Faça commit antes do deploy."
    exit 1
fi

# Executar testes
echo "🧪 Executando testes..."
./scripts/run_tests.sh
if [ $? -ne 0 ]; then
    echo "❌ Testes falharam. Deploy cancelado."
    exit 1
fi

# Build da imagem Docker
echo "🐳 Building imagem Docker..."
docker build -t orquestra-agentes:latest .
if [ $? -ne 0 ]; then
    echo "❌ Build do Docker falhou."
    exit 1
fi

# Tag da versão
VERSION=$(date +%Y%m%d-%H%M%S)
docker tag orquestra-agentes:latest orquestra-agentes:$VERSION

echo "✅ Imagem Docker criada:"
echo "  • orquestra-agentes:latest"
echo "  • orquestra-agentes:$VERSION"

# Verificar se arquivo .env.prod existe
if [ ! -f .env.prod ]; then
    echo "⚠️ Arquivo .env.prod não encontrado."
    echo "Crie um arquivo .env.prod com as configurações de produção."
    exit 1
fi

# Deploy usando docker-compose
echo "🚀 Fazendo deploy..."
docker-compose --env-file .env.prod up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deploy concluído com sucesso!"
    echo ""
    echo "📋 Informações do deploy:"
    echo "  • Versão: $VERSION"
    echo "  • Timestamp: $(date)"
    echo "  • Branch: $current_branch"
    echo "  • Commit: $(git rev-parse --short HEAD)"
    echo ""
    echo "🔍 Para verificar logs:"
    echo "  docker-compose logs -f orquestra-api"
    echo ""
    echo "🩺 Health check:"
    echo "  curl http://localhost:8000/health"
else
    echo "❌ Deploy falhou."
    exit 1
fi