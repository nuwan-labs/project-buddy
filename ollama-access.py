"""
Ollama Accessibility Test Script
Tests connectivity, model availability, and inference from Windows laptop to workstation

Usage:
    python test_ollama_access.py --host 192.168.x.x --model deepseek-r1
    
    Or edit DEFAULT_HOST and DEFAULT_MODEL below to match your setup, then:
    python test_ollama_access.py
"""

import requests
import json
import sys
import argparse
from typing import Dict, Tuple
import time

# EDIT THESE TO MATCH YOUR SETUP
DEFAULT_HOST = "192.168.200.5"  # Workstation IP - change to your workstation's actual IP
DEFAULT_PORT = 11434
DEFAULT_MODEL = "deepseek-r1:7b"

class OllamaTestRunner:
    def __init__(self, host: str, port: int, model: str):
        self.host = host
        self.port = port
        self.model = model
        self.base_url = f"http://{host}:{port}"
        self.results = []
        self.passed = 0
        self.failed = 0

    def log_result(self, test_name: str, passed: bool, message: str, details: str = ""):
        """Log test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.results.append({
            "test": test_name,
            "status": status,
            "message": message,
            "details": details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        print(f"\n{status}: {test_name}")
        print(f"  → {message}")
        if details:
            print(f"  → Details: {details}")

    def test_connection(self) -> bool:
        """Test 1: Basic TCP connectivity"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                self.log_result(
                    "TCP Connection",
                    True,
                    f"Successfully connected to {self.base_url}",
                    f"Status code: {response.status_code}"
                )
                return True
            else:
                self.log_result(
                    "TCP Connection",
                    False,
                    f"Connected but received status {response.status_code}",
                    response.text[:200]
                )
                return False
        except requests.exceptions.ConnectionError as e:
            self.log_result(
                "TCP Connection",
                False,
                f"Failed to connect to {self.base_url}",
                f"Error: {str(e)}"
            )
            return False
        except Exception as e:
            self.log_result(
                "TCP Connection",
                False,
                f"Unexpected error during connection test",
                f"Error: {str(e)}"
            )
            return False

    def test_ollama_version(self) -> bool:
        """Test 2: Verify Ollama is running"""
        try:
            response = requests.get(
                f"{self.base_url}/api/version",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                version = data.get("version", "unknown")
                self.log_result(
                    "Ollama Service",
                    True,
                    "Ollama service is running",
                    f"Version: {version}"
                )
                return True
            else:
                self.log_result(
                    "Ollama Service",
                    False,
                    f"Received status {response.status_code}",
                    response.text[:200]
                )
                return False
        except Exception as e:
            self.log_result(
                "Ollama Service",
                False,
                "Failed to check Ollama version",
                f"Error: {str(e)}"
            )
            return False

    def test_model_available(self) -> bool:
        """Test 3: Check if DeepSeek R1 model is loaded"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]
                
                model_available = any(self.model.lower() in name.lower() for name in model_names)
                
                if model_available:
                    self.log_result(
                        "Model Availability",
                        True,
                        f"Model '{self.model}' is available",
                        f"Loaded models: {', '.join(model_names) if model_names else 'None'}"
                    )
                    return True
                else:
                    self.log_result(
                        "Model Availability",
                        False,
                        f"Model '{self.model}' not found on workstation",
                        f"Available models: {', '.join(model_names) if model_names else 'No models loaded'}"
                    )
                    return False
            else:
                self.log_result(
                    "Model Availability",
                    False,
                    f"Failed to list models (status {response.status_code})",
                    response.text[:200]
                )
                return False
        except Exception as e:
            self.log_result(
                "Model Availability",
                False,
                f"Failed to check for model '{self.model}'",
                f"Error: {str(e)}"
            )
            return False

    def test_inference(self) -> bool:
        """Test 4: Simple inference - test generation"""
        try:
            prompt = "List the capital of France in one word."
            
            print(f"\n  → Sending test prompt to {self.model}...")
            print(f"     Prompt: '{prompt}'")
            print(f"     (This may take 30-60 seconds on first run...)")
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120  # 2 minute timeout for inference
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                generated_text = data.get("response", "").strip()
                
                if generated_text:
                    self.log_result(
                        "Inference Test",
                        True,
                        f"Model generated response in {elapsed:.1f}s",
                        f"Response: '{generated_text[:100]}...'" if len(generated_text) > 100 else f"Response: '{generated_text}'"
                    )
                    return True
                else:
                    self.log_result(
                        "Inference Test",
                        False,
                        "Model returned empty response",
                        json.dumps(data, indent=2)[:300]
                    )
                    return False
            else:
                self.log_result(
                    "Inference Test",
                    False,
                    f"Received status {response.status_code}",
                    response.text[:300]
                )
                return False
        except requests.exceptions.Timeout:
            self.log_result(
                "Inference Test",
                False,
                "Request timed out (>120 seconds)",
                "Model may be slow or not responding"
            )
            return False
        except Exception as e:
            self.log_result(
                "Inference Test",
                False,
                "Failed to run inference",
                f"Error: {str(e)}"
            )
            return False

    def test_streaming_inference(self) -> bool:
        """Test 5: Streaming inference (alternative to simple generation)"""
        try:
            prompt = "What is the scientific method? Explain in 2 sentences."
            
            print(f"\n  → Testing streaming inference...")
            print(f"     Prompt: '{prompt}'")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True
                },
                timeout=120,
                stream=True
            )
            
            if response.status_code == 200:
                # Collect streamed response
                full_response = ""
                chunk_count = 0
                
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get("response", "")
                            full_response += chunk
                            chunk_count += 1
                        except json.JSONDecodeError:
                            pass
                
                if full_response:
                    self.log_result(
                        "Streaming Inference",
                        True,
                        f"Streaming works ({chunk_count} chunks received)",
                        f"Generated: '{full_response[:80]}...'" if len(full_response) > 80 else f"Generated: '{full_response}'"
                    )
                    return True
                else:
                    self.log_result(
                        "Streaming Inference",
                        False,
                        "Stream returned no data",
                        ""
                    )
                    return False
            else:
                self.log_result(
                    "Streaming Inference",
                    False,
                    f"Received status {response.status_code}",
                    response.text[:200]
                )
                return False
        except Exception as e:
            self.log_result(
                "Streaming Inference",
                False,
                "Streaming inference failed",
                f"Error: {str(e)}"
            )
            return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("=" * 70)
        print("OLLAMA ACCESSIBILITY TEST SUITE")
        print("=" * 70)
        print(f"\nConfiguration:")
        print(f"  Workstation Host: {self.host}:{self.port}")
        print(f"  Model: {self.model}")
        print(f"  Base URL: {self.base_url}")
        print("\n" + "-" * 70)

        # Run tests
        self.test_connection()
        if self.passed == 0:  # Stop early if no connection
            print("\n⚠️  Cannot proceed without connection. Check workstation IP and Ollama service.")
            return
        
        self.test_ollama_version()
        self.test_model_available()
        self.test_inference()
        self.test_streaming_inference()

        # Summary
        print("\n" + "=" * 70)
        print(f"TEST SUMMARY: {self.passed} passed, {self.failed} failed")
        print("=" * 70)

        if self.failed == 0:
            print("\n✓ All tests passed! Ollama is accessible and working correctly.")
            print(f"\nReady to deploy Lab Notebook application.")
            return True
        else:
            print(f"\n✗ {self.failed} test(s) failed. See details above.")
            print("\nTroubleshooting tips:")
            print("  1. Verify workstation IP is correct (check ipconfig on workstation)")
            print("  2. Check Ollama is running: ollama serve")
            print("  3. Check firewall allows port 11434 from laptop")
            print("  4. Verify model is loaded: ollama list")
            print("  5. Try pulling model: ollama pull deepseek-r1")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Test Ollama accessibility from Windows laptop to workstation"
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Workstation IP (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Ollama port (default: {DEFAULT_PORT})")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    
    args = parser.parse_args()
    
    tester = OllamaTestRunner(args.host, args.port, args.model)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()