import os

from config.config import LAYOUT_DETECTION_PROMPT
from dashscope import MultiModalConversation
from dotenv import load_dotenv

load_dotenv()

def detect_excel_layout(file_path: str) -> dict:
    messages = [
        {
            "role": "user",
            "content": [{"image": file_path}, {"text": LAYOUT_DETECTION_PROMPT}],
        }
    ]
    response = MultiModalConversation.call(
        api_key=os.getenv("DASHSCOPE_API_KEY2"),
        model="qwen3-vl-plus",
        messages=messages,
    )
    return response.get("output").choices[0].get("message").get("content")[0].get("text")

if __name__ == "__main__":
    file_path = "./output_images/布局2_主表+子表布局.png"
    res = detect_excel_layout(file_path)
    print(res)
