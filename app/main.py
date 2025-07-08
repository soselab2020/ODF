from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List

import os, json, tempfile, zipfile

from .models import DynamicAssignmentInput
from .odf_utils import create_dynamic_assignment_odt, extract_field_answers_and_images
from .config_utils import load_config

CONFIG = load_config()
BASE_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), CONFIG.get("OUTPUT_DIR")))
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)  # 確保目錄存在

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

@app.post("/generate")
def generate_assignment(input_data: DynamicAssignmentInput):
    if not input_data.student_id:
        input_data.student_id = "請輸入學號"
    if not input_data.student_name:
        input_data.student_name = "請輸入姓名"
    output_path = os.path.join(BASE_OUTPUT_DIR, "Exercise.odt")
    create_dynamic_assignment_odt(output_path, input_data)
    download_url = "/download-generated"
    return JSONResponse(content={"download_url": download_url})

@app.get("/download-generated")
def download_generated():
    output_path = os.path.join(BASE_OUTPUT_DIR, "Exercise.odt")
    return FileResponse(output_path, filename="Exercise.odt", media_type="application/vnd.oasis.opendocument.text")

@app.post("/extract")
def extract_uploaded_file(file: UploadFile = File(...), fields_json: str = Form("[]")):
    try:
        fields = json.loads(fields_json)
        if not isinstance(fields, list):
            return JSONResponse(content={"error": "欄位格式錯誤，應為 list[str]"}, status_code=400)
    except json.JSONDecodeError:
        return JSONResponse(content={"error": "欄位 JSON 解析失敗"}, status_code=400)

    tmp_path = os.path.join(BASE_OUTPUT_DIR, f"D-{file.filename}")
    with open(tmp_path, "wb") as f:
        f.write(file.file.read())

    answers, images = extract_field_answers_and_images(tmp_path, fields)

    return JSONResponse(content={
        "answers": answers,
        "images": images  # base64 編碼格式，key 為含欄位名的圖片檔名
    })

@app.post("/extract-folder")
def extract_folder(files: List[UploadFile] = File(...), fields_json: str = Form("[]")):
    try:
        fields = json.loads(fields_json)
        if not isinstance(fields, list):
            return JSONResponse(content={"error": "欄位格式錯誤，應為 list[str]"}, status_code=400)
    except json.JSONDecodeError:
        return JSONResponse(content={"error": "欄位 JSON 解析失敗"}, status_code=400)

    all_results = {}

    for file in files:
        tmp_path = os.path.join(BASE_OUTPUT_DIR, file.filename)
        os.makedirs(os.path.dirname(tmp_path), exist_ok=True)  # ✅ 確保目錄存在
        
        with open(tmp_path, "wb") as f:
            f.write(file.file.read())

        answers, images = extract_field_answers_and_images(tmp_path, fields)
        all_results[file.filename] = {
            "answers": answers,
            "images": images
        }

    return JSONResponse(content=all_results)

# ----------- 下載指定目錄壓縮檔 ----------- #
@app.get("/download-folder")
def download_folder():
    zip_name = os.path.join(BASE_OUTPUT_DIR, "output_archive.zip")

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(BASE_OUTPUT_DIR):
            for filename in filenames:
                if filename != os.path.basename(zip_name):
                    filepath = os.path.join(foldername, filename)
                    arcname = os.path.relpath(filepath, BASE_OUTPUT_DIR)
                    zipf.write(filepath, arcname)

    return FileResponse(zip_name, filename="output_archive.zip", media_type="application/zip")

@app.get("/{page_name}")
def get_page(page_name: str):
    return FileResponse(f"static/{page_name}")