from fastapi import FastAPI
from pydantic import BaseModel
import base64
from io import BytesIO
import re
import pdfplumber  # ✅ Replaces PyPDF2

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

        # ✅ Use pdfplumber for better text extraction
        with pdfplumber.open(BytesIO(content)) as pdf:
            text = " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        print("------- Extracted Text Preview --------")
        print(text[:1000])  # limit for safety/log size

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

            # ✅ Improved email and phone matching
            email_match = re.search(r"Email\s*[:\-]?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", text, re.IGNORECASE)
email = email_match.group(1).strip() if email_match else "Not found"

            phone = re.search(r"(?:\+91[\-\s]?)?[6-9]\d{9}", text)

            # ✅ More flexible skill and experience matching
            skills_match = re.search(r"(Skills|Technical Skills)[\s:\-]*([\w\s,]+)", text, re.IGNORECASE)
            experience = re.search(r"(Experience|Work Experience)[\s:\-]*([\w\s.,]+)", text, re.IGNORECASE)

            return {
                "document_type": "Resume",
                "email": email,
                "phone": phone.group(0) if phone else "Not found",
                "skills": skills_match.group(2).strip() if skills_match else "Not found",
                "experience": experience.group(2).strip() if experience else "Not found",
                "raw_text_excerpt": text[:500]
            }

        else:
            return {"error": "Unsupported fileType. Use 'resume' or 'offer_letter'."}

    except Exception as e:
        return {"error": str(e)}
