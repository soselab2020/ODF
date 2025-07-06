from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
import os, json

from .models import DynamicAssignmentInput
from .odf_utils import create_dynamic_assignment_odt, extract_field_answers_and_images

app = FastAPI()

@app.post("/generate")
def generate_assignment(input_data: DynamicAssignmentInput):
    output_path = os.path.join("D:\\temp", "學生作業.odt")
    create_dynamic_assignment_odt(output_path, input_data)
    return FileResponse(output_path, filename="學生作業.odt", media_type="application/vnd.oasis.opendocument.text")

@app.post("/extract")
def extract_uploaded_file(file: UploadFile = File(...), fields_json: str = Form("[]")):
    try:
        print("收到欄位設定文字：", fields_json)
        fields = json.loads(fields_json)
        if not isinstance(fields, list):
            return JSONResponse(content={"error": "欄位格式錯誤，應為 list[str]"}, status_code=400)
    except json.JSONDecodeError:
        return JSONResponse(content={"error": "欄位 JSON 解析失敗"}, status_code=400)

    tmp_path = f"D:\\temp\\D-{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(file.file.read())

    answers, images = extract_field_answers_and_images(tmp_path, fields)

    return JSONResponse(content={
        "answers": answers,
        "images": images
    })
