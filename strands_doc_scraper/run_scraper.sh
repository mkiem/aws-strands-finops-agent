#!/bin/bash

# Strands Documentation Scraper Runner
echo "Setting up Strands Documentation Scraper..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Run the scraper
echo "Starting documentation scraping..."
python scraper.py

echo "Scraping completed! Check the generated files:"
echo "- STRANDS_SDK_README.md"
echo "- strands_documentation_raw.json"
