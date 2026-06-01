import os
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from google import genai
from google.genai import types
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = FastAPI(title="The Personal OS Cloud Engine")

# Initialize the modern client (automatically detects GEMINI_API_KEY from Render)
client = genai.Client()
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
    
    creds_dict = {
        "type": "service_account",
        "project_id": os.environ.get("G_PROJECT_ID"),
        "private_key_id": os.environ.get("G_PRIVATE_KEY_ID"),
        "private_key": os.environ.get("G_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.environ.get("G_CLIENT_EMAIL"),
        "client_id": os.environ.get("G_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
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
async def ingest_thought(
    thought: str = Form(None),
    file: UploadFile = File(None)
):
    try:
        processed_text = ""

        # Step 1: Extract text or audio content
        if file:
            audio_bytes = await file.read()
            file_mime = file.content_type or "audio/mp3"
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type=file_mime
                    ),
                    "Transcribe verbatim, keeping Hebrew and English meshed. No translation."
                ]
            )
            processed_text = response.text

        elif thought:
            processed_text = thought

        else:
            return {"status": "error", "message": "No input payload received."}

        # Step 2: Invoke Dynamic Trivium Engine with system instructions
        trivium_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Process this raw thought:\n\n{processed_text}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION
            )
        )
        
        # Step 3: Build Markdown metadata header and body layout
        now = datetime.now()
        markdown_output = f"""---
date: {now.strftime('%Y-%m-%d')}
time: {now.strftime('%H:%M')}
status: in-quarry
---

# 📝 Raw Extraction
"{processed_text}"

---

{trivium_response.text}
"""
        # Step 4: Dispatch payload directly to your existing Google Drive utility function
        filename = f"{now.strftime('%Y-%m-%d_%H%M')}_quarry_node.md"
        upload_to_google_drive(filename, markdown_output)
        
        return {"status": "success", "filename": filename}

    except Exception as e:
        print(f"Error handling request: {str(e)}")
        return {"status": "error", "detail": str(e)}
