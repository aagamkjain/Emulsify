#!/usr/bin/env python3
"""
Production-ready PDF Policy Query System
Startup and test script
"""

import subprocess
import sys
import os
import time
import requests
import json

def print_banner():
    """Print system banner"""
    print("🏛️" + "=" * 60)
    print("    PDF POLICY QUERY SYSTEM")
    print("    OCR + Weaviate + Gemini 2.5 Pro")
    print("    Production Ready v1.0")
    print("=" * 60)

def check_dependencies():
    """Check if all dependencies are available"""
    print("\n🔍 Checking dependencies...")
    
    try:
        import fastapi
        import google.generativeai
        import weaviate
        import fitz  # PyMuPDF
        import cv2
        import numpy
        print("✅ Core dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists and has required keys"""
    print("\n🔍 Checking environment configuration...")
    
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        with open(".env", "w") as f:
            f.write("GOOGLE_API_KEY=your_google_api_key_here\n")
        print("📝 Created .env template")
        print("💡 Please add your Google API key to the .env file")
        return False
    
    with open(".env", "r") as f:
        env_content = f.read()
        if "your_google_api_key_here" in env_content:
            print("❌ Google API key not configured")
            print("💡 Please add your real Google API key to the .env file")
            return False
    
    print("✅ Environment configuration looks good")
    return True

def check_weaviate():
    """Check if Weaviate is running"""
    print("\n🔍 Checking Weaviate database...")
    
    try:
        response = requests.get("http://localhost:8080/v1/.well-known/ready", timeout=5)
        if response.status_code == 200:
            print("✅ Weaviate is running")
            return True
        else:
            print(f"❌ Weaviate returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Weaviate is not running")
        return False

def start_weaviate():
    """Start Weaviate using Docker Compose"""
    print("\n🚀 Starting Weaviate...")
    
    if not os.path.exists("docker-compose.yml"):
        print("❌ docker-compose.yml not found")
        return False
    
    try:
        subprocess.run(["docker-compose", "up", "-d"], check=True, capture_output=True)
        print("✅ Weaviate started with Docker Compose")
        
        # Wait for Weaviate to be ready
        print("⏳ Waiting for Weaviate to be ready...")
        for i in range(30):
            if check_weaviate():
                return True
            time.sleep(1)
            print(f"   Waiting... ({i+1}/30)")
        
        print("❌ Weaviate failed to start in time")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Weaviate: {e}")
        return False
    except FileNotFoundError:
        print("❌ Docker Compose not found. Please install Docker.")
        return False

def start_backend():
    """Start the FastAPI backend"""
    print("\n🚀 Starting backend server...")
    
    try:
        process = subprocess.Popen([sys.executable, "backend.py"])
        
        # Wait for backend to be ready
        print("⏳ Waiting for backend to start...")
        for i in range(15):
            try:
                response = requests.get("http://localhost:8000/", timeout=2)
                if response.status_code == 200:
                    print("✅ Backend is ready")
                    return process
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            print(f"   Waiting... ({i+1}/15)")
        
        print("❌ Backend failed to start in time")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def test_system():
    """Test the system with a health check"""
    print("\n🧪 Testing system...")
    
    try:
        # Test health endpoint
        health_response = requests.get("http://localhost:8000/")
        health_data = health_response.json()
        
        print(f"   System Status: {health_data.get('status', 'unknown')}")
        print(f"   Weaviate: {health_data.get('weaviate', 'unknown')}")
        
        return health_data.get('status') == 'running'
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def show_usage_instructions():
    """Show usage instructions"""
    print("\n📋 SYSTEM READY!")
    print("=" * 40)
    print("🌐 Backend API: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("\n🚀 To start the frontend:")
    print("   cd frontend")
    print("   npm install  # (if not done already)")
    print("   npm start")
    print("   Open http://localhost:3000")
    print("\n📝 Usage:")
    print("   1. Upload a PDF policy document")
    print("   2. Ask questions in plain English")
    print("   3. Get simple, clear answers")
    print("\n🛑 Press Ctrl+C to stop the backend")
    print("=" * 40)

def main():
    """Main function"""
    print_banner()
    
    # Check all prerequisites
    if not check_dependencies():
        return False
    
    if not check_env_file():
        return False
    
    # Start Weaviate if needed
    if not check_weaviate():
        if not start_weaviate():
            print("\n💡 Manual Weaviate start:")
            print("   docker-compose up -d")
            return False
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return False
    
    # Test system
    if not test_system():
        backend_process.terminate()
        return False
    
    # Show instructions
    show_usage_instructions()
    
    try:
        # Keep the backend running
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        backend_process.terminate()
        print("✅ Backend stopped")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
