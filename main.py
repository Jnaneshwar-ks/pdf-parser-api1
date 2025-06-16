from fastapi import FastAPI
from pydantic import BaseModel
import base64
from io import BytesIO
import PyPDF2
import re

app = FastAPI()

class FileInput(BaseModel):
    filename: str
    fileContent: str
    docType: str  # "offer" or "resume"

@app.post("/parse")
def parse_pdf(data: FileInput):
    try:
        # Decode PDF content
        content = base64.b64decode(data.fileContent)
        reader = PyPDF2.PdfReader(BytesIO(content))
        text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])

        result = {"raw_text_excerpt": text[:500]}

        if data.docType.lower() == "offer":
            # Offer Letter Parsing
            name = re.search(r"Name\s*[:\-]\s*(.+?)(?:\n|Designation|Start)", text, re.IGNORECASE)
            role = re.search(r"Designation\s*[:\-]\s*(.+?)(?:\n|Start)", text, re.IGNORECASE)
            doj = re.search(r"Start Date\s*[:\-]\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", text, re.IGNORECASE)
            basic_salary = re.search(r"Basic\s+([\d,]+)\s+([\d,]+)", text)
            gross_salary = re.search(r"Gross Salary.*?\s([\d,]+)\s+([\d,]+)", text)
            ctc = re.search(r"Cost to Company.*?\s([\d,]+)\s+([\d,]+)", text)

            result.update({
                "name": name.group(1).strip() if name else "Not found",
                "designation": role.group(1).strip() if role else "Not found",
                "start_date": doj.group(1).strip() if doj else "Not found",
                "basic_salary_monthly": basic_salary.group(1) if basic_salary else "Not found",
                "basic_salary_annual": basic_salary.group(2) if basic_salary else "Not found",
                "gross_salary_monthly": gross_salary.group(1) if gross_salary else "Not found",
                "gross_salary_annual": gross_salary.group(2) if gross_salary else "Not found",
                "ctc_monthly": ctc.group(1) if ctc else "Not found",
                "ctc_annual": ctc.group(2) if ctc else "Not found"
            })

        elif data.docType.lower() == "resume":
            # Resume Parsing
            email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
            phone = re.search(r"(\+91[-\s]?)?[6-9]\d{9}", text)
            skills_section = re.search(r"(Skills|Technical Skills|Technologies Known)\s*[:\-]?\s*(.*)", text, re.IGNORECASE)
            name = re.search(r"^\s*([A-Z][a-z]+\s+[A-Z][a-z]+)", text)

            result.update({
                "name": name.group(1).strip() if name else "Not found",
                "email": email.group(0) if email else "Not found",
                "phone": phone.group(0) if phone else "Not found",
                "skills": skills_section.group(2).strip() if skills_section else "Not found"
            })
        else:
            return {"error": "Invalid document type. Use 'offer' or 'resume'."}

        return result

    except Exception as e:
        return {"error": str(e)}
