from pydantic import BaseModel

class DynamicAssignmentInput(BaseModel):
    course_name: str
    unit_name: str
    student_id: str
    student_name: str
    fields: list[str]  # 欄位標題清單