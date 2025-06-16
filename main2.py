from fastapi import FastAPI
from pydantic import BaseModel
import base64
from io import BytesIO
import PyPDF2
import re

app = FastAPI()

class FileInput(BaseModel):
    filename: str
    fileContent: str  # Base64-encoded PDF content
    fileType: str     # "resume" or "offer_letter"

@app.post("/parse")
def parse_pdf(data: FileInput):
    try:
        # Decode base64 string to bytes
        content = base64.b64decode(data.fileContent)
        reader = PyPDF2.PdfReader(BytesIO(content))
        text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])

        if data.fileType.lower() == "offer_letter":
            # Offer Letter Parsing
            name = re.search(r"Name\s*[:\-]\s*(.+?)(?:\n|Designation|Start)", text, re.IGNORECASE)
            role = re.search(r"Designation\s*[:\-]\s*(.+?)(?:\n|Start)", text, re.IGNORECASE)
            doj = re.search(r"Start Date\s*[:\-]\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", text, re.IGNORECASE)
            basic_salary = re.search(r"Basic\s+([\d,]+)\s+([\d,]+)", text)
            gross_salary = re.search(r"Gross Salary.*?\s([\d,]+)\s+([\d,]+)", text)
            ctc = re.search(r"Cost to Company.*?\s([\d,]+)\s+([\d,]+)", text)

            return {
                "document_type": "Offer Letter",
                "name": name.group(1).strip() if name else "Not found",
                "designation": role.group(1).strip() if role else "Not found",
                "start_date": doj.group(1).strip() if doj else "Not found",
                "basic_salary_monthly": basic_salary.group(1) if basic_salary else "Not found",
                "basic_salary_annual": basic_salary.group(2) if basic_salary else "Not found",
                "gross_salary_monthly": gross_salary.group(1) if gross_salary else "Not found",
                "gross_salary_annual": gross_salary.group(2) if gross_salary else "Not found",
                "ctc_monthly": ctc.group(1) if ctc else "Not found",
                "ctc_annual": ctc.group(2) if ctc else "Not found",
                "raw_text_excerpt": text[:500]
            }

        elif data.fileType.lower() == "resume":
            # Resume Parsing
            email = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
            phone = re.search(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b", text)
            skills_match = re.search(r"Skills\s*[:\-]?\s*(.+?)(?:\n|Experience|Projects)", text, re.IGNORECASE)
            experience = re.search(r"Experience\s*[:\-]?\s*(.+?)(?:\n|Skills|Projects)", text, re.IGNORECASE)

            return {
                "document_type": "Resume",
                "email": email.group(0) if email else "Not found",
                "phone": phone.group(0) if phone else "Not found",
                "skills": skills_match.group(1).strip() if skills_match else "Not found",
                "experience": experience.group(1).strip() if experience else "Not found",
                "raw_text_excerpt": text[:500]
            }

        else:
            return {"error": "Unsupported fileType. Use 'resume' or 'offer_letter'."}

    except Exception as e:
        return {"error": str(e)}
