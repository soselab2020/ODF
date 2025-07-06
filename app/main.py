from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
from fastapi.responses import FileResponse, JSONResponse
from odf.opendocument import OpenDocumentText, load
from odf.text import P, H
import tempfile, os, json, zipfile, base64

app = FastAPI()

# ----------- 資料模型：動態欄位定義 ----------- #
class DynamicAssignmentInput(BaseModel):
    course_name: str
    unit_name: str
    fields: list[str]  # 欄位標題清單

# ----------- 功能：產出 ODF 作業表單 ----------- #
def create_dynamic_assignment_odt(path: str, data: DynamicAssignmentInput):
    doc = OpenDocumentText()

    doc.text.addElement(H(outlinelevel=1, text="學生作業表單"))
    doc.text.addElement(P(text=f"課程名稱：{data.course_name}"))
    doc.text.addElement(P(text=f"單元名稱：{data.unit_name}"))
    doc.text.addElement(P(text=""))

    doc.text.addElement(P(text="【請依下列欄位作答】"))
    doc.text.addElement(P(text=""))

    for i, field in enumerate(data.fields, start=1):
        doc.text.addElement(P(text=f"📝 {field}"))
        doc.text.addElement(P(text="===================="))
        doc.text.addElement(P(text=""))

    doc.save(path)

@app.post("/generate")
def generate_assignment(input_data: DynamicAssignmentInput):
    output_path = os.path.join("D:\\temp", "學生作業.odt")
    create_dynamic_assignment_odt(output_path, input_data)
    return FileResponse(output_path, filename="學生作業.odt", media_type="application/vnd.oasis.opendocument.text")

# ----------- 功能：擷取學生作答內容與圖片 ----------- #
def extract_field_answers_and_images(path: str, fields: list[str]):
    doc = load(path)
    paragraphs = doc.getElementsByType(P)
    print("收到欄位設定：", fields)

    results = {}
    images = {}
    current_field = None
    image_counter = {}
    buffer = []

    for p in paragraphs:
        text = "".join([n.data for n in p.childNodes if hasattr(n, 'data')])
        if text.startswith("📝"):
            if current_field and buffer:
                results[current_field] = "\n".join(buffer).strip()
                buffer = []
            for field in fields:
                if field in text:
                    current_field = field
                    break
        elif current_field:
            if text.strip() and text.strip() != "====================":
                buffer.append(text.strip())

    if current_field and buffer:
        results[current_field] = "\n".join(buffer).strip()

    # 圖片處理
    with tempfile.TemporaryDirectory() as extract_dir:
        try:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipFile:
            print(f"⚠️ 無法解壓縮 ODT：{path}")
            return results, images

        pic_dir = os.path.join(extract_dir, "Pictures")
        if os.path.isdir(pic_dir):
            for fname in os.listdir(pic_dir):
                if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    field_name = current_field or "未指定欄位"
                    image_counter[field_name] = image_counter.get(field_name, 0) + 1
                    new_name = f"{field_name}_圖片{image_counter[field_name]}{os.path.splitext(fname)[1]}"
                    fpath = os.path.join(pic_dir, fname)
                    with open(fpath, "rb") as img_file:
                        encoded = base64.b64encode(img_file.read()).decode('utf-8')
                        images[new_name] = encoded

    return results, images

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
        "images": images  # base64 編碼格式，key 為含欄位名的圖片檔名
    })
