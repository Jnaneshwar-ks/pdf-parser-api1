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

@app.post("/parse")
def parse_pdf(data: FileInput):
    try:
        # Decode the base64 content
        content = base64.b64decode(data.fileContent)
        reader = PyPDF2.PdfReader(BytesIO(content))
        text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])

        # Extract Name
        name = re.search(r"Name\s*[:\-]\s*(.+?)(?:\n|Designation|Start)", text, re.IGNORECASE)
        
        # Extract Designation
        role = re.search(r"Designation\s*[:\-]\s*(.+?)(?:\n|Start)", text, re.IGNORECASE)
        
        # Extract Start Date (Date of Joining)
        doj = re.search(r"Start Date\s*[:\-]\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", text, re.IGNORECASE)

        # Extract Basic Salary (Monthly and Annual)
        basic_salary = re.search(r"Basic\s+([\d,]+)\s+([\d,]+)", text)

        # Extract Gross Salary (Monthly and Annual)
        gross_salary = re.search(r"Gross Salary.*?\s([\d,]+)\s+([\d,]+)", text)

        # Extract Cost to Company (Monthly and Annual)
        ctc = re.search(r"Cost to Company.*?\s([\d,]+)\s+([\d,]+)", text)

        return {
            "name": name.group(1).strip() if name else "Not found",
            "designation": role.group(1).strip() if role else "Not found",
            "start_date": doj.group(1).strip() if doj else "Not found",
            "basic_salary_monthly": basic_salary.group(1) if basic_salary else "Not found",
            "basic_salary_annual": basic_salary.group(2) if basic_salary else "Not found",
            "gross_salary_monthly": gross_salary.group(1) if gross_salary else "Not found",
            "gross_salary_annual": gross_salary.group(2) if gross_salary else "Not found",
            "ctc_monthly": ctc.group(1) if ctc else "Not found",
            "ctc_annual": ctc.group(2) if ctc else "Not found",
            "raw_text_excerpt": text[:500]  # optional: to verify parsing
        }

    except Exception as e:
        return {"error": str(e)}