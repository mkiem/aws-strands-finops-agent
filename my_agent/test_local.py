#!/usr/bin/env python3
import sys
import os
import json

# Add the virtual environment to the path
venv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv/lib/python3.11/site-packages')
sys.path.insert(0, venv_path)

# Import the lambda handler
from lambda_handler import handler

# Test the handler
event = {"query": "What is 2+2?"}
context = {}

try:
    print("Testing lambda handler...")
    response = handler(event, context)
    print("Response:")
    print(json.dumps(response, indent=2))
    print("Test successful!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
