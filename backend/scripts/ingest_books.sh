#!/bin/bash

# Script to ingest all books from Livres folder into knowledge base

set -e  # Exit on error

BOOKS_DIR="/Users/maximedousset/Documents/Projets_Claude/projet-C/Livres"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INGEST_SCRIPT="$SCRIPT_DIR/ingest_knowledge.py"
PYTHON_BIN="python"  # Use conda python instead of system $PYTHON_BIN

echo "========================================="
echo "Ingesting books into knowledge base"
echo "========================================="
echo ""

# Book 1: Data Science for Supply Chain Forecasting
echo "[1/5] Ingesting: Data Science for Supply Chain Forecasting..."
$PYTHON_BIN "$INGEST_SCRIPT" \
  --file "$BOOKS_DIR/Data Science for Supply Chain Forecasting (Nicolas Vandeput) (Z-Library).pdf" \
  --title "Data Science for Supply Chain Forecasting" \
  --category "forecasting" \
  --subcategory "data_science" \
  --tags data_science machine_learning supply_chain
echo "✓ Done"
echo ""

# Book 2: Demand Forecasting Best Practices
echo "[2/5] Ingesting: Demand Forecasting Best Practices..."
$PYTHON_BIN "$INGEST_SCRIPT" \
  --file "$BOOKS_DIR/Demand Forecasting Best Practices (Nicolas Vandeput) (Z-Library).pdf" \
  --title "Demand Forecasting Best Practices" \
  --category "forecasting" \
  --subcategory "best_practices" \
  --tags forecasting best_practices demand_planning
echo "✓ Done"
echo ""

# Book 3: Demand Forecasting for Executives and Professionals
echo "[3/5] Ingesting: Demand Forecasting for Executives and Professionals..."
$PYTHON_BIN "$INGEST_SCRIPT" \
  --file "$BOOKS_DIR/Demand Forecasting for Executives and Professionals (Stephan Kolassa, Bahman Rostami-Tabar etc.) (Z-Library).pdf" \
  --title "Demand Forecasting for Executives and Professionals" \
  --category "forecasting" \
  --subcategory "management" \
  --tags forecasting executives management strategic
echo "✓ Done"
echo ""

# Book 4: Forecasting Principles and Practice
echo "[4/5] Ingesting: Forecasting Principles and Practice..."
$PYTHON_BIN "$INGEST_SCRIPT" \
  --file "$BOOKS_DIR/Forecasting Principles and Practice (Rob J. Hyndman George Athanasopoulos) (Z-Library).pdf" \
  --title "Forecasting Principles and Practice" \
  --category "forecasting" \
  --subcategory "principles" \
  --tags forecasting statistical_methods time_series
echo "✓ Done"
echo ""

# Book 5: Supply Chain Network Design
echo "[5/5] Ingesting: Supply Chain Network Design..."
$PYTHON_BIN "$INGEST_SCRIPT" \
  --file "$BOOKS_DIR/Supply Chain Network Design How to Create Resilient, Agile and Sustainable Supply Chains (Das Dasgupta, Greys Sošić, Nick Vyas) (Z-Library).pdf" \
  --title "Supply Chain Network Design" \
  --category "supply_chain" \
  --subcategory "network_design" \
  --tags supply_chain network_design resilience agility sustainability
echo "✓ Done"
echo ""

echo "========================================="
echo "All books ingested successfully!"
echo "========================================="
echo ""
echo "To verify, run:"
echo "  $PYTHON_BIN $INGEST_SCRIPT --list-categories"
