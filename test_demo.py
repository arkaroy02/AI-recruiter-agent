#!/usr/bin/env python3
"""
Test & Demo Script for Talent Scout Studio.
Validates the core agent modules and the current FastAPI-based app workflow.
"""

import sys
import json
import time
import os
from pathlib import Path

# Add agent to path
sys.path.insert(0, str(Path(__file__).parent / "agent"))

# Avoid UnicodeEncodeError on Windows terminals using cp1252.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_step(step_num, text):
    """Print step indicator"""
    print(f"[{step_num}] {text}")

def test_imports():
    """Test all required imports"""
    print_header("TESTING IMPORTS")
    
    try:
        print_step(1, "Testing Ollama...")
        import ollama
        print(f"   ✅ Ollama imported")
        
        print_step(2, "Testing ChromaDB...")
        import chromadb
        print(f"   ✅ ChromaDB imported")
        
        print_step(3, "Testing FastAPI stack...")
        import fastapi
        import jinja2
        print(f"   ✅ FastAPI and Jinja2 imported")
        
        print_step(4, "Testing Pandas...")
        import pandas
        print(f"   ✅ Pandas imported")
        
        print_step(5, "Testing agent modules...")
        from jd_parser import parse_jd
        from embedder import embed_text, index_candidates
        from match_scorer import score_match
        from covo_simulator import simulate_conversation
        from interest_scorer import score_interest
        from ranker import rank_candidates
        print(f"   ✅ All agent modules imported")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_ollama_connection():
    """Test Ollama connectivity and models"""
    print_header("TESTING OLLAMA CONNECTION")
    
    try:
        import ollama

        chat_model = os.getenv("OLLAMA_CHAT_MODEL", "tinyllama:latest")
        embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        ollama_host = os.getenv("OLLAMA_HOST") or os.getenv("OLLAMA_BASE_URL")
        client = ollama.Client(host=ollama_host) if ollama_host else ollama.Client()
        
        print_step(1, "Testing Ollama connection...")
        try:
            response = client.list()
            print(f"   ✅ Ollama connection successful")
        except Exception as e:
            print(f"   ❌ Ollama not running: {str(e)}")
            print(f"   💡 Start Ollama with: ollama serve")
            return False
        
        print_step(2, "Checking required models...")
        models = response.models if hasattr(response, "models") else response["models"]
        model_names = []
        for m in models:
            if hasattr(m, "model"):
                model_names.append(m.model)
            elif isinstance(m, dict):
                model_names.append(m.get("name") or m.get("model") or "")
        
        required = [chat_model, embed_model]
        found = []
        missing = []
        
        for req in required:
            if any(req in name for name in model_names):
                found.append(req)
                print(f"   ✅ {req} available")
            else:
                missing.append(req)
                print(f"   ⚠️  {req} not found")
        
        if missing:
            print(f"\n   💡 Download missing models:")
            for model in missing:
                print(f"      ollama pull {model}")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_data_files():
    """Test data file availability"""
    print_header("TESTING DATA FILES")
    
    try:
        print_step(1, "Checking candidates.json...")
        candidates_path = Path("data/candidates.json")
        if candidates_path.exists():
            with open(candidates_path) as f:
                candidates = json.load(f)
            print(f"   ✅ Found {len(candidates)} candidates")
        else:
            print(f"   ❌ candidates.json not found")
            return False
        
        print_step(2, "Checking sample_jd.txt...")
        jd_path = Path("tests/sample_jd.txt")
        if jd_path.exists():
            with open(jd_path) as f:
                jd = f.read()
            print(f"   ✅ Sample JD loaded ({len(jd)} chars)")
        else:
            print(f"   ❌ sample_jd.txt not found")
            return False
        
        return True, candidates, jd
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False, None, None

def test_jd_parsing(jd_text):
    """Test JD parsing"""
    print_header("TESTING JD PARSING")
    
    try:
        from jd_parser import parse_jd
        
        print_step(1, "Parsing sample JD...")
        result = parse_jd(jd_text)
        
        print(f"   ✅ Parsed successfully")
        print(f"   Role: {result.get('role')}")
        print(f"   Required Skills: {', '.join(result.get('required_skills', [])[:3])}...")
        print(f"   Min Experience: {result.get('min_years_exp')} years")
        print(f"   Seniority: {result.get('seniority')}")
        print(f"   Domain: {result.get('domain')}")
        
        return True, result
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False, None

def test_embeddings():
    """Test embedding functionality"""
    print_header("TESTING EMBEDDINGS")
    
    try:
        from embedder import embed_text
        
        print_step(1, "Creating test embedding...")
        test_text = "Senior Python Engineer with AWS experience"
        embedding = embed_text(test_text)
        
        print(f"   ✅ Embedding created")
        print(f"   Dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_matching(candidates, jd_parsed):
    """Test candidate matching"""
    print_header("TESTING CANDIDATE MATCHING")
    
    try:
        from embedder import index_candidates, find_top_candidates
        from match_scorer import score_match
        
        print_step(1, "Indexing candidates...")
        index_candidates(candidates)
        print(f"   ✅ Indexed {len(candidates)} candidates")
        
        print_step(2, "Searching for matches...")
        matched = find_top_candidates(jd_parsed, top_k=3)
        print(f"   ✅ Found {len(matched)} top matches")
        for i, c in enumerate(matched, 1):
            print(f"      {i}. {c.get('name')} ({c.get('title')})")
        
        print_step(3, "Scoring matches...")
        first_match = matched[0]
        score = score_match(first_match, jd_parsed)
        print(f"   ✅ Match score for {first_match['name']}: {score['match_score']}/100")
        
        return True, matched
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False, None

def test_conversation(candidate, jd_parsed):
    """Test conversation simulation"""
    print_header("TESTING CONVERSATION SIMULATION")
    
    try:
        from covo_simulator import simulate_conversation
        
        print_step(1, f"Simulating conversation with {candidate['name']}...")
        conversation = simulate_conversation(candidate, jd_parsed, turns=2)
        
        print(f"   ✅ Conversation simulated ({len(conversation)} messages)")
        print(f"\n   Sample conversation:")
        for i, msg in enumerate(conversation[:2], 1):
            speaker = "👨‍💼 RECRUITER" if msg['speaker'] == 'recruiter' else "💼 CANDIDATE"
            text = msg['text'][:100] + "..." if len(msg['text']) > 100 else msg['text']
            print(f"      {speaker}: {text}")
        
        return True, conversation
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        print(f"   💡 Check if Ollama is running: ollama serve")
        return False, None

def test_interest_scoring(conversation):
    """Test interest scoring"""
    print_header("TESTING INTEREST SCORING")
    
    try:
        from interest_scorer import score_interest
        
        print_step(1, "Scoring candidate interest...")
        result = score_interest(conversation)
        
        print(f"   ✅ Interest scored successfully")
        print(f"   Interest Score: {result.get('interest_score')}/100")
        print(f"   Availability: {result.get('availability')}")
        if result.get('key_signals'):
            print(f"   Key Signals: {result.get('key_signals')[0]}")
        if result.get('red_flags'):
            print(f"   Red Flags: {result.get('red_flags')[0]}")
        
        return True, result
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False, None

def test_ranking(candidates, match_scores, interest_scores):
    """Test ranking logic"""
    print_header("TESTING RANKING LOGIC")
    
    try:
        from ranker import rank_candidates
        
        print_step(1, "Preparing scoring data...")
        combined_data = []
        for i, c in enumerate(candidates[:3]):
            combined_data.append({
                **c,
                'match_score': match_scores.get(c['id'], 75),
                'interest_score': interest_scores.get(c['id'], 80)
            })
        
        print_step(2, "Ranking candidates...")
        ranked = rank_candidates(combined_data)
        
        print(f"   ✅ Ranking completed")
        print(f"   Top candidate: {ranked[0]['name']} ({ranked[0].get('combined_score', 0)}/100)")
        
        return True, ranked
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False, None

def run_full_pipeline_test():
    """Run complete end-to-end test"""
    print_header("RUNNING FULL PIPELINE TEST")
    
    try:
        from orchestrator import run_full_pipeline, load_candidates
        
        print_step(1, "Loading candidates...")
        candidates = load_candidates()
        print(f"   ✅ Loaded {len(candidates)} candidates")
        
        print_step(2, "Loading sample JD...")
        with open("tests/sample_jd.txt") as f:
            jd_text = f.read()
        print(f"   ✅ Loaded JD ({len(jd_text)} chars)")
        
        print_step(3, "Running full pipeline (this may take 30-60 seconds)...")
        start = time.time()
        results = run_full_pipeline(jd_text, candidates, top_k=3)
        elapsed = time.time() - start
        
        print(f"   ✅ Pipeline completed in {elapsed:.1f} seconds")
        print(f"   Candidates processed: {results['total_processed']}")
        print(f"\n   Top ranked candidates:")
        for i, c in enumerate(results['ranked_candidates'][:3], 1):
            score = c.get('combined_score', 0)
            print(f"      {i}. {c['name']}: {score}/100")
        
        return True, results
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def print_summary(results):
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    results_list = []
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        results_list.append(f"{status}  {test_name}")
    
    for line in results_list:
        print(f"  {line}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed! System is ready to use.")
        print("\n  Next steps:")
        print("    1. Run: uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000")
        print("    2. Open: http://127.0.0.1:8000")
        print("    3. Paste or upload a job description")
    else:
        print("\n  ⚠️  Some tests failed. Check the errors above.")
        print("  Make sure:")
        print("    - Ollama is running (ollama serve)")
        print("    - All models are downloaded")
        print("    - All data files are present")

def main():
    """Run all tests"""
    print_header("TALENT SCOUT AGENT - TEST SUITE")
    
    results = {}
    
    # Test 1: Imports
    print("Starting comprehensive tests...\n")
    results['Imports'] = test_imports()
    
    if not results['Imports']:
        print_summary(results)
        sys.exit(1)
    
    # Test 2: Ollama
    results['Ollama Connection'] = test_ollama_connection()
    
    if not results['Ollama Connection']:
        print_summary(results)
        sys.exit(1)
    
    # Test 3: Data Files
    data_result = test_data_files()
    results['Data Files'] = data_result[0]
    if not results['Data Files']:
        print_summary(results)
        sys.exit(1)
    
    candidates, jd_text = data_result[1], data_result[2]
    
    # Test 4: JD Parsing
    parse_result = test_jd_parsing(jd_text)
    results['JD Parsing'] = parse_result[0]
    jd_parsed = parse_result[1]
    
    # Test 5: Embeddings
    results['Embeddings'] = test_embeddings()
    
    # Test 6: Matching
    match_result = test_matching(candidates, jd_parsed)
    results['Candidate Matching'] = match_result[0]
    matched = match_result[1]
    
    if matched:
        # Test 7: Conversation
        conv_result = test_conversation(matched[0], jd_parsed)
        results['Conversation Simulation'] = conv_result[0]
        conversation = conv_result[1]
        
        if conversation:
            # Test 8: Interest Scoring
            interest_result = test_interest_scoring(conversation)
            results['Interest Scoring'] = interest_result[0]
    
    # Test 9: Full Pipeline
    pipeline_result = run_full_pipeline_test()
    results['Full Pipeline'] = pipeline_result[0]
    
    # Print summary
    print_summary(results)

if __name__ == "__main__":
    main()
