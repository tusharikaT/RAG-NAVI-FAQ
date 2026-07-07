"""
verify_setup.py
Phase 1 exit criteria verification script.

Checks:
  1. All required packages are importable
  2. GROQ_API_KEY is present in .env
  3. Groq API connection is successful

Usage:
    python verify_setup.py
"""

import sys


def check_imports():
    """Verify all required packages are installed."""
    required = [
        ("langchain", "langchain"),
        ("langchain_community", "langchain-community"),
        ("langchain_groq", "langchain-groq"),
        ("groq", "groq"),
        ("sentence_transformers", "sentence-transformers"),
        ("chromadb", "chromadb"),
        ("bs4", "beautifulsoup4"),
        ("httpx", "httpx"),
        ("playwright", "playwright"),
        ("streamlit", "streamlit"),
        ("dotenv", "python-dotenv"),
    ]

    print("-- Checking package imports ----------------------------------")
    all_ok = True
    for module, package in required:
        try:
            __import__(module)
            print(f"  [OK]    {package}")
        except ImportError:
            print(f"  [FAIL]  {package}  -->  pip install {package}")
            all_ok = False
    return all_ok


def check_env():
    """Verify .env exists and GROQ_API_KEY is set."""
    import os
    from dotenv import load_dotenv

    print("\n-- Checking .env ---------------------------------------------")
    load_dotenv()
    key = os.getenv("GROQ_API_KEY")
    if not key or key == "your_groq_api_key_here":
        print("  [FAIL]  GROQ_API_KEY not set -- copy .env.example to .env and add your key")
        return False
    print(f"  [OK]    GROQ_API_KEY found ({key[:8]}...)")
    return True


def check_groq():
    """Make a minimal Groq API call to verify authentication."""
    import os
    from dotenv import load_dotenv

    load_dotenv()
    print("\n-- Verifying Groq API connection -----------------------------")
    try:
        from groq import Groq

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Reply with: OK"}],
            max_tokens=5,
            temperature=0.0,
        )
        reply = response.choices[0].message.content.strip()
        print(f"  [OK]    Groq API responded: '{reply}'")
        return True
    except Exception as e:
        print(f"  [FAIL]  Groq API error: {e}")
        return False


def main():
    print("\nRAG-GROWW Phase 1 -- Setup Verification\n")

    imports_ok = check_imports()
    env_ok = check_env()
    groq_ok = check_groq() if env_ok else False

    print("\n-- Summary ---------------------------------------------------")
    print(f"  Packages : {'All OK' if imports_ok else 'FAILED -- some packages missing'}")
    print(f"  Env file : {'OK' if env_ok else 'FAILED -- GROQ_API_KEY missing'}")
    print(f"  Groq API : {'Connected' if groq_ok else 'FAILED -- not connected'}")

    if imports_ok and env_ok and groq_ok:
        print("\nPhase 1 COMPLETE -- ready for Phase 2!\n")
        sys.exit(0)
    else:
        print("\nFix the issues above before proceeding to Phase 2.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
