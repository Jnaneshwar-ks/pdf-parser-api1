from fastapi import FastAPI
from pydantic import BaseModel
import base64
from io import BytesIO
import PyPDF2
import re

app = FastAPI()

class FileInput(BaseModel):
    filename: str
    fileContent: str  # base64-encoded string of the PDF

@app.post("/extract-emails")
def extract_emails(data: FileInput):
    try:
        # Decode base64 content
        content = base64.b64decode(data.fileContent)
        reader = PyPDF2.PdfReader(BytesIO(content))
        text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])

        # Regex pattern to extract email(s)
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

        return {
            "email_addresses": list(set(emails)) if emails else [],
            "raw_text_excerpt": text[:500]
        }

    except Exception as e:
        return {"error": str(e)}
