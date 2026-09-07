"""
test_new_features.py — Unit tests for Title-Only Projects, Error Solver, Code Generator, and PDF Summarizer.
"""

import pytest
from backend.app.models.schemas import ErrorSolverRequest, CodeGeneratorRequest, DoubtRequest
from backend.app.services.error_solver_service import error_solver_service
from backend.app.services.code_generator_service import code_generator_service
from backend.app.services.pdf_summary_service import pdf_summary_service
from backend.app.services.doubt_agent_service import doubt_agent_service


def test_error_solver_service():
    req = ErrorSolverRequest(
        code="def divide(a, b):\n    return a / 0",
        error_log="ZeroDivisionError: division by zero",
        language="python"
    )
    res = error_solver_service.solve_error(req)
    assert res.error_summary is not None
    assert "corrected_code" in res.model_dump()
    assert res.corrected_code != ""


def test_code_generator_service():
    req = CodeGeneratorRequest(
        prompt="Write a function to check if a string is a palindrome",
        language="python"
    )
    res = code_generator_service.generate_code(req)
    assert res.title is not None
    assert res.generated_code != ""
    assert res.explanation != ""


def test_pdf_summary_service_fallback():
    # Test processing with empty/mock pdf input list
    mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    pdf_list = [("test_notes.pdf", mock_pdf_content)]
    res = pdf_summary_service.process_pdf_bundle(pdf_list)
    assert res.total_pdfs_processed == 1
    assert res.executive_summary != ""
    assert len(res.high_yield_topics) > 0


def test_doubt_agent_service():
    req = DoubtRequest(
        query="What is the difference between recursion and iteration?"
    )
    res = doubt_agent_service.resolve_doubt(req)
    assert res.answer != ""
    assert len(res.key_takeaways) > 0

