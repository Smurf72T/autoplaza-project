#!/bin/bash

echo "Setting up Autoplaza project..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file
cp .env.example .env

echo "Please update .env file with your settings"
echo "Then run: python manage.py migrate"