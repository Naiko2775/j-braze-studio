"""Tests pour l'analyseur Data Model (mode demo sans API)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.data_model.analyzer import analyze_use_cases_demo, format_results_text, extract_mermaid


def test_analyze_demo_returns_valid_structure():
    result = analyze_use_cases_demo()
    assert "use_case_analysis" in result
    assert "data_hierarchy" in result
    assert "mermaid_diagram" in result
    assert len(result["use_case_analysis"]) > 0


def test_format_results_text():
    result = analyze_use_cases_demo()
    text = format_results_text(result)
    assert "USE CASE:" in text
    assert "DONNEES REQUISES:" in text


def test_format_results_text_with_error():
    text = format_results_text({"error": "Test error", "raw_response": "raw"})
    assert "Erreur" in text


def test_extract_mermaid():
    result = analyze_use_cases_demo()
    mermaid = extract_mermaid(result)
    assert "graph TD" in mermaid


def test_extract_mermaid_with_error():
    mermaid = extract_mermaid({"error": "Test"})
    assert "Error" in mermaid or "Erreur" in mermaid
