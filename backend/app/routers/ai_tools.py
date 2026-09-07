"""
ai_tools.py — API Router for AI Tools (Error Detector & Solver, Code Generator, AI Tutor)
"""

import logging
from fastapi import APIRouter, Depends, status
from backend.app.models.schemas import (
    APIResponse,
    ErrorSolverRequest,
    ErrorSolverResponse,
    CodeGeneratorRequest,
    CodeGeneratorResponse,
    DoubtRequest,
    DoubtResponse
)
from backend.app.routers.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.services.error_solver_service import error_solver_service
from backend.app.services.code_generator_service import code_generator_service
from backend.app.services.doubt_agent_service import doubt_agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-tools", tags=["AI Developer & Educator Tools"])


@router.post(
    "/detect-and-solve-errors",
    response_model=APIResponse[ErrorSolverResponse],
    status_code=status.HTTP_200_OK,
    summary="Detect errors in code & stack traces and generate step-by-step solutions"
)
def detect_and_solve_errors(
    req: ErrorSolverRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Analyze code snippet and error log, return root cause, explanation, and fixed code."""
    try:
        res = error_solver_service.solve_error(req)
        return APIResponse(
            message="Code error analysis and automated solution generated successfully",
            data=res
        )
    except Exception as e:
        logger.error(f"Error solver failed: {e}")
        # Return structured fallback instead of crashing
        fallback = ErrorSolverResponse(
            error_summary="AI analysis temporarily unavailable.",
            root_cause=f"The AI service encountered an issue: {str(e)[:200]}",
            corrected_code=req.code,
            explanation="Please ensure your GEMINI_API_KEY is configured and try again.",
            prevention_tips=["Verify GEMINI_API_KEY in your .env file", "Check your internet connection"]
        )
        return APIResponse(
            success=True,
            message="Error analysis (fallback mode)",
            data=fallback
        )


@router.post(
    "/generate-code",
    response_model=APIResponse[CodeGeneratorResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate custom code based on requirements or prompts"
)
def generate_code(
    req: CodeGeneratorRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Generate production-ready working code from user requirement prompt."""
    try:
        res = code_generator_service.generate_code(req)
        return APIResponse(
            message="Code generated successfully based on requirement prompt",
            data=res
        )
    except Exception as e:
        logger.error(f"Code generator failed: {e}")
        fallback = CodeGeneratorResponse(
            title=req.title or "Generated Code",
            language=req.language or "python",
            generated_code=f"# AI code generation temporarily unavailable.\n# Error: {str(e)[:200]}\n# Please check GEMINI_API_KEY in your .env file.\n\npass",
            explanation="The AI service is temporarily unavailable. Please try again shortly.",
            file_name="solution.py"
        )
        return APIResponse(
            success=True,
            message="Code generation (fallback mode)",
            data=fallback
        )


@router.post(
    "/clear-doubt",
    response_model=APIResponse[DoubtResponse],
    status_code=status.HTTP_200_OK,
    summary="24/7 Instant AI Tutor for clearing computer science and programming doubts"
)
def clear_doubt(
    req: DoubtRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Resolve programming doubt, concept question, or code clarification instantly."""
    try:
        res = doubt_agent_service.resolve_doubt(req)
        return APIResponse(
            message="AI Tutor explanation generated successfully",
            data=res
        )
    except Exception as e:
        logger.error(f"Doubt agent failed: {e}")
        # Always return a helpful response instead of crashing with 500
        fallback = DoubtResponse(
            answer=(
                f"I'm having trouble reaching the AI right now. Your question was:\n\n"
                f"**\"{req.query[:200]}\"**\n\n"
                f"Please try again in a moment. If this keeps happening, ensure your "
                f"`GEMINI_API_KEY` is set correctly in the `.env` file."
            ),
            key_takeaways=[
                "Ensure GEMINI_API_KEY is set in your .env file",
                "Check your internet connection and try again"
            ],
            related_topics=[]
        )
        return APIResponse(
            success=True,
            message="AI Tutor response (fallback mode — AI temporarily unavailable)",
            data=fallback
        )
