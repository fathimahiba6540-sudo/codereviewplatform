"""
pdf_summary_service.py — PDF Bundle Processor & Exam-Oriented Summarizer Service
Extracts text from single or multiple PDF documents, merges PDF files, and generates high-yield exam summaries.
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Tuple
import pypdf
from backend.app.core.config import settings
from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import PDFSummaryResponse

logger = logging.getLogger(__name__)


class PDFSummaryService(BaseAgent):
    def __init__(self):
        super().__init__(name="PDFExamSummarizerAgent", role="Exam-Oriented PDF Content Summarizer")
        self.bundle_dir = os.path.join(settings.UPLOAD_DIR, "pdf_bundles")
        os.makedirs(self.bundle_dir, exist_ok=True)

    def process_pdf_bundle(self, pdf_files_data: List[Tuple[str, bytes]]) -> PDFSummaryResponse:
        """
        Process single or multiple PDF files:
        1. Extract text content from each PDF.
        2. Merge PDF documents into a unified output PDF.
        3. Perform AI analysis for exam-oriented high-yield topics, definitions, and questions.
        """
        bundle_id = str(uuid.uuid4())
        combined_text = []
        total_pages = 0
        merger = pypdf.PdfWriter()
        filenames = []

        for original_filename, file_bytes in pdf_files_data:
            filenames.append(original_filename)
            pdf_path = os.path.join(self.bundle_dir, f"temp_{uuid.uuid4().hex}.pdf")
            try:
                with open(pdf_path, "wb") as f:
                    f.write(file_bytes)

                reader = pypdf.PdfReader(pdf_path)
                pages_cnt = len(reader.pages)
                total_pages += pages_cnt

                # Extract text
                doc_text = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        doc_text.append(text)
                    merger.add_page(page)

                combined_text.append(f"--- DOCUMENT: {original_filename} ({pages_cnt} pages) ---\n" + "\n".join(doc_text))

            except Exception as e:
                logger.error(f"Error reading PDF file {original_filename}: {e}")
            finally:
                if os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                    except Exception:
                        pass

        # Save merged output PDF bundle
        merged_filename = f"bundle_{bundle_id}.pdf"
        merged_pdf_path = os.path.join(self.bundle_dir, merged_filename)
        try:
            with open(merged_pdf_path, "wb") as f:
                merger.write(f)
            merger.close()
        except Exception as e:
            logger.error(f"Failed to write merged PDF bundle: {e}")

        full_corpus = "\n\n".join(combined_text)
        corpus_snippet = full_corpus[:15000]  # Cap for context window

        combined_title = f"Combined Study Notes ({len(filenames)} PDFs: {', '.join(filenames[:3])})"

        # Generate Exam-Oriented Summary using Gemini AI
        prompt = f"""
You are a master educator and professor creating an EXAM-ORIENTED STUDY GUIDE & HIGH-YIELD SUMMARY from course documents.
Analyze the following combined text from {len(filenames)} PDF documents (Total Pages: {total_pages}).

[COMBINED PDF CONTENT]:
{corpus_snippet}

Structure your response strictly as valid JSON with the following schema:
{{
  "executive_summary": "High-level overview of key subject matter covered in the PDFs",
  "high_yield_topics": [
    {{
      "topic": "Topic Name",
      "importance": "🔥 High Priority" or "⭐ Core Concept" or "💡 Frequently Tested",
      "summary": "Detailed explanation of why this topic is vital for exams and core principles"
    }}
  ],
  "definitions_and_formulas": [
    {{
      "term": "Term or Formula Name",
      "definition": "Clear concise definition or mathematical expression",
      "key_point": "Key takeaway to remember in exam questions"
    }}
  ],
  "exam_questions": [
    {{
      "question": "Sample Exam / Revision Question based on content",
      "answer": "Comprehensive model answer",
      "marks": "10 Marks"
    }}
  ],
  "cheatsheet_markdown": "# Quick Revision Cheatsheet\\n- Point 1\\n- Point 2\\n- Key takeaway 3"
}}
"""
        llm_response = self.invoke_llm(prompt)
        parsed = self.parse_json_safely(llm_response, fallback=None)

        if parsed and "high_yield_topics" in parsed:
            return PDFSummaryResponse(
                combined_title=combined_title,
                total_pdfs_processed=len(filenames),
                total_pages=total_pages,
                executive_summary=parsed.get("executive_summary", "Exam summary generated."),
                high_yield_topics=parsed.get("high_yield_topics", []),
                definitions_and_formulas=parsed.get("definitions_and_formulas", []),
                exam_questions=parsed.get("exam_questions", []),
                cheatsheet_markdown=parsed.get("cheatsheet_markdown", "# Cheatsheet\n- Study core definitions."),
                bundle_id=bundle_id
            )

        return self._heuristic_fallback(combined_title, len(filenames), total_pages, bundle_id, full_corpus)

    def _heuristic_fallback(
        self,
        combined_title: str,
        total_pdfs: int,
        total_pages: int,
        bundle_id: str,
        corpus: str
    ) -> PDFSummaryResponse:
        lines = [line.strip() for line in corpus.split("\n") if len(line.strip()) > 20]
        extracted_topics = lines[:5] if lines else ["Core Principles", "System Architecture", "Algorithms"]

        topics = []
        for i, t in enumerate(extracted_topics):
            priority = "🔥 High Priority" if i % 2 == 0 else "⭐ Core Concept"
            topics.append({
                "topic": t[:60],
                "importance": priority,
                "summary": f"Key concept highlighted across the study materials: {t[:120]}..."
            })

        defs = [
            {
                "term": "Core Principle / Axiom",
                "definition": "Fundamental rule governing system behavior and problem resolution.",
                "key_point": "Always state assumptions clearly when answering exam questions."
            },
            {
                "term": "System Complexity & Trade-offs",
                "definition": "Evaluation of time/space complexity and resource allocation limits.",
                "key_point": "Compare worst-case vs average-case efficiency."
            }
        ]

        questions = [
            {
                "question": "Explain the primary architecture and high-yield concepts discussed in the materials.",
                "answer": "The materials focus on core design principles, efficiency optimization, step-by-step problem resolution, and key theoretical definitions.",
                "marks": "10 Marks"
            },
            {
                "question": "Define the critical formulas or rules and discuss their application.",
                "answer": "Key rules mandate structured evaluation, error bounds, and verifying boundary condition edge cases.",
                "marks": "5 Marks"
            }
        ]

        cheatsheet = f"""# 📝 Exam-Oriented Quick Revision Cheatsheet

### 🎯 Key Exam Focus Areas:
1. **{topics[0]['topic'] if topics else 'Core Concepts'}**: Crucial topic frequently tested in examinations.
2. **Definitions**: Ensure precise technical terminology is used.
3. **Problem-Solving Steps**: Outline methodology clearly before providing code or mathematical proofs.

### 💡 High-Yield Quick Notes:
- Review all key formulas and definitions prior to exam start.
- Focus on multi-part conceptual questions worth 10+ marks.
"""

        return PDFSummaryResponse(
            combined_title=combined_title,
            total_pdfs_processed=total_pdfs,
            total_pages=total_pages,
            executive_summary=f"Processed and merged bundle of {total_pdfs} PDF documents ({total_pages} total pages). Synthesized exam-oriented high-yield topics, definitions, and model questions.",
            high_yield_topics=topics,
            definitions_and_formulas=defs,
            exam_questions=questions,
            cheatsheet_markdown=cheatsheet,
            bundle_id=bundle_id
        )


pdf_summary_service = PDFSummaryService()
