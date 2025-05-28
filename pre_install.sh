#!/bin/bash
# Pre-install script for Streamlit Cloud
echo "Python version:"
python --version

# Try to install ifcopenshell from conda-forge
pip install --upgrade pip
pip install conda
conda install -c conda-forge ifcopenshell python=3.11 -y || echo "Conda install failed, trying pip..."