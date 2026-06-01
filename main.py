import os
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
#import google.generativeai as genai
from google import genai
from google.genai import types
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = FastAPI(title="The Personal OS Cloud Engine")

# Configure APIs
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")

# Dynamic System Prompt Frame
SYSTEM_INSTRUCTION = """
You are a linguistic stone-cutter processing raw bilingual thoughts for a high-form personal knowledge vault.
The input text contains a fluid, bilingual blend of Hebrew and English, laced with technical jargon and local Israeli street slang. 

CRITICAL ACTIONS:
1. VERBATIM PRESERVATION: Do not translate the Hebrew to English, and do not translate the English to Hebrew. Leave the "mesh" exactly as it was spoken.
2. CONVERSATIONAL CADENCE PUNCTUATION: Insert punctuation based on conversational pauses.
3. DYNAMIC SYMBOLIC BRIDGES: Analyze the tonal intent of the note. Generate exactly THREE custom frameworks or prompts at the bottom to help the user expand on this thought. 
   - If philosophical/structural: suggest Masonic, Scriptural/Parasha, or Stoic angles.
   - If relational/emotional: suggest Toast/Celebration, Poetry, or Memorial angles.
   - If creative/general: suggest alternative lenses.
Do not hard-code fixed titles; adapt titles dynamically to match the theme of the raw thought.
"""

def upload_to_google_drive(filename: str, content: str):
    """Quietly writes the markdown file directly to your Google Drive Cloud."""
    scopes = ['https://www.googleapis.com/auth/drive.file']
    # Render reads these variables from the secure dashboard dashboard environment
    creds_dict = {
        "type": "service_account",
        "project_id": os.environ.get("G_PROJECT_ID"),
        "private_key_id": os.environ.get("G_PRIVATE_KEY_ID"),
        "private_key": os.environ.get("G_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.environ.get("G_CLIENT_EMAIL"),
        "client_id": os.environ.get("G_CLIENT_ID"),
    }
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    service = build('drive', 'v3', credentials=creds)
    
    # Write temp file locally in the cloud container
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
        
    file_metadata = {'name': filename, 'parents': [GOOGLE_DRIVE_FOLDER_ID]}
    media = MediaFileUpload(filename, mimetype='text/markdown')
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    os.remove(filename)

@app.post("/ingest")
async def ingest_thought(text_payload: str = Form(None), gear: str = Form("text"), file: UploadFile = File(None)):
    now = datetime.now()
    processed_text = text_payload
    
    if file:
        temp_audio = f"temp_{file.filename}"
        with open(temp_audio, "wb") as b: b.write(await file.read())
        audio_cloud = genai.upload_file(path=temp_audio)
        model = genai.GenerativeModel("gemini-1.5-flash")
        transcription = model.generate_content(["Transcribe verbatim, keeping Hebrew and English meshed. No translation.", audio_cloud])
        processed_text = transcription.text
        os.remove(temp_audio)

    # Invoke Dynamic Trivium Engine
    trivium_model = genai.GenerativeModel("models/gemini-2.5-flash")(system_instruction=SYSTEM_INSTRUCTION)
    response = trivium_model.generate_content(f"Process this raw {gear} thought:\n\n{processed_text}")
    
    markdown_output = f"""---
date: {now.strftime('%Y-%m-%d')}
time: {now.strftime('%H:%M')}
gear: {gear}
status: in-quarry
---

# 📝 Raw Extraction
"{processed_text}"

---

{response.text}
"""
    filename = f"{now.strftime('%Y-%m-%d_%H%M')}_quarry_node.md"
    upload_to_google_drive(filename, markdown_output)
    return {"status": "success"}
