#!/bin/bash

# Script para executar todos os testes

echo "🧪 Executando Suite de Testes"
echo "=============================="

# Verificar se está no ambiente Poetry
if ! poetry env info &> /dev/null; then
    echo "❌ Ambiente Poetry não encontrado. Execute 'poetry install' primeiro."
    exit 1
fi

echo "🔍 Verificando linting..."
echo "-------------------------"

# Verificar formatação com black
echo "📝 Verificando formatação (black)..."
poetry run black --check src tests
if [ $? -ne 0 ]; then
    echo "❌ Problemas de formatação encontrados. Execute: poetry run black src tests"
    exit 1
fi

# Verificar imports com isort
echo "📦 Verificando imports (isort)..."
poetry run isort --check-only src tests
if [ $? -ne 0 ]; then
    echo "❌ Problemas de import encontrados. Execute: poetry run isort src tests"
    exit 1
fi

# Verificar com flake8
echo "🔧 Verificando código (flake8)..."
poetry run flake8 src tests --max-line-length=88 --extend-ignore=E203,W503
if [ $? -ne 0 ]; then
    echo "❌ Problemas de código encontrados"
    exit 1
fi

# Verificar tipos com mypy
echo "🔍 Verificando tipos (mypy)..."
poetry run mypy src --ignore-missing-imports
if [ $? -ne 0 ]; then
    echo "⚠️ Problemas de tipagem encontrados (não bloqueante)"
fi

echo ""
echo "🧪 Executando testes..."
echo "----------------------"

# Executar testes com coverage
poetry run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test_exit_code=$?

echo ""
if [ $test_exit_code -eq 0 ]; then
    echo "✅ Todos os testes passaram!"
    echo ""
    echo "📊 Relatório de cobertura gerado em htmlcov/index.html"
else
    echo "❌ Alguns testes falharam"
    exit $test_exit_code
fi

echo ""
echo "🎉 Suite de testes concluída com sucesso!"