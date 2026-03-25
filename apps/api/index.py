"""Vercel serverless entry point.

This file is the entry point for Vercel serverless functions.
It imports the Mangum handler from main.py.

Vercel executes this file in isolation, so we must ensure the
apps/api directory is on sys.path for relative imports to work.
"""
import os
import sys

# Ensure the api directory is on the Python path so that
# imports like "from models.db import ..." resolve correctly.
API_DIR = os.path.dirname(os.path.abspath(__file__))
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

from main import handler  # noqa: E402
