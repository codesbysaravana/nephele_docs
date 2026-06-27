import asyncio
import os
import sys
import json

# Ensure we can import app
sys.path.insert(0, os.path.abspath('.'))

# This will load dotenv and set up API keys
from app import config
from app.resume.analyzer import ResumeAnalyzer

async def run_test():
    file_path = r"C:\Users\Sithany\Downloads\Ancy.pdf"
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    print(f"Testing ResumeAnalyzer with file: {file_path}")
    analyzer = ResumeAnalyzer()
    try:
        profile = await analyzer.analyze(file_path)
        print("\n--- Analysis Result ---")
        print(profile.model_dump_json(indent=2))
    except Exception as e:
        print(f"\nError during analysis: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
