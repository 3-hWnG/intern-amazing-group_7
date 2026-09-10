from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import chromadb
from sentence_transformers import SentenceTransformer
import ollama
from pydantic import BaseModel
import uvicorn
from duckduckgo_search import DDGS
import numpy as np

app = FastAPI()

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Trợ Lý Pháp Lý - Demo</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; background-color: #1e1e1e; color: #fff;}
        #chat { height: 500px; border: 1px solid #444; overflow-y: auto; padding: 10px; background: #2d2d2d; border-radius: 5px; margin-bottom: 10px;}
        .msg { margin: 10px 0; padding: 10px; border-radius: 5px; white-space: pre-wrap;}
        .user { background: #005A9C; text-align: right;}
        .bot { background: #444; }
        .router-log { color: #f39c12; font-size: 0.8em; font-style: italic; margin-bottom: 5px;}
        input { width: 80%; padding: 10px; border: none; border-radius: 5px; outline: none;}
        button { width: 15%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;}
    </style>
</head>
<body>
    <h2>🤖 Trợ Lý Ảo (Semantic Router) - Nhóm 7</h2>
    <div id="chat"></div>
    <div style="display:flex; justify-content:space-between;">
        <input type="text" id="query" placeholder="Hỏi bất cứ thứ gì..." onkeypress="if(event.key === 'Enter') send()">
        <button onclick="send()">Gửi</button>
    </div>

    <script>
        async function send() {
            let query = document.getElementById('query').value;
            if (!query) return;
            
            let chat = document.getElementById('chat');
            chat.innerHTML += `<div class="msg user"><b>Bạn:</b> ${query}</div>`;
            document.getElementById('query').value = '';
            
            let botMsgId = "msg-" + Date.now();
            chat.innerHTML += `<div class="msg bot" id="${botMsgId}"><b>Đang dùng Vector tính toán ngữ nghĩa...</b></div>`;
            chat.scrollTop = chat.scrollHeight;

            try {
                let response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: query})
                });
                let data = await response.json();
                
                let logHtml = `<div class="router-log">[Semantic Router] Chế độ: ${data.intent} (Độ tin cậy: ${data.score})</div>`;
                document.getElementById(botMsgId).innerHTML = logHtml + `<b>Trợ lý:</b>\n${data.answer}`;
            } catch (err) {
                document.getElementById(botMsgId).innerHTML = `<b>Lỗi hệ thống:</b>\n${err}`;
            }
            chat.scrollTop = chat.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return html_content

class Query(BaseModel):
    text: str

print("Loading Database & Semantic Router...")
try:
    embed_model = SentenceTransformer("keepitreal/vietnamese-sbert")
    client = chromadb.PersistentClient(path="../data/chromadb")
    collection = client.get_or_create_collection(name="legal_docs")
    
    # Định nghĩa Cụm Vector Nhận diện Ngữ nghĩa (Không học vẹt từ khóa)
    luat_emb = embed_model.encode("hỏi đáp thủ tục hành chính, quy định pháp luật, hồ sơ, giấy tờ, đăng ký, lệ phí, nhà nước, công dân, thẻ căn cước công dân, cấp đổi cccd, hộ chiếu passport, kết hôn, ly hôn, khai sinh, khai tử, cấp giấy chứng sinh, hộ khẩu thường trú, thủ tục sang tên sổ đỏ, cấp giấy phép xây dựng, nhà đất, hộ kinh doanh")
    ngoai_emb = embed_model.encode("tin tức thời sự, giá cả thị trường, chứng khoán, thời tiết, bão lũ, hôm nay, kiến thức ngoài lề, sự kiện")
    xagiao_emb = embed_model.encode("xin chào, bạn tên gì, cảm ơn, khỏe không, trò chuyện, tâm sự, giao tiếp cơ bản")
except Exception as e:
    print("LỖI KHỞI TẠO:", e)

def classify_intent_semantic(text: str):

    clean_text = text.strip().lower()
    greetings = ["xin chào", "chào", "chào bạn", "hello", "hi", "alo", "ê", "bạn là ai", "cảm ơn", "tạm biệt", "bye"]
    if clean_text in greetings or (len(clean_text.split()) <= 3 and any(w in clean_text for w in greetings)):
        return "XAGIAO", 1.0
    law_keywords = ["thủ tục", "hồ sơ", "giấy tờ", "lệ phí", "kết hôn", "khai sinh", "khai tử", "căn cước", "cccd", "sổ đỏ", "xây dựng", "liệt sĩ", "hỏa táng", "học bổng", "chuyển trường", "hộ kinh doanh"]
    if any(kw in clean_text for kw in law_keywords):
        return "LUAT", 0.95
    
    q_emb = embed_model.encode(text)

    
    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
    scores = {
        "LUAT": cosine_sim(q_emb, luat_emb),
        "NGOAI": cosine_sim(q_emb, ngoai_emb),
        "XAGIAO": cosine_sim(q_emb, xagiao_emb)
    }
    
    best_intent = max(scores, key=scores.get)
    best_score = round(float(scores[best_intent]), 2)
    return best_intent, best_score

@app.post("/chat")
async def chat_endpoint(query: Query):
    try:
        intent, score = classify_intent_semantic(query.text)
        
        if intent == "LUAT":
            query_embed = embed_model.encode(query.text).tolist()
            results = collection.query(query_embeddings=[query_embed], n_results=2)
            context = "\\n\\n".join(results['documents'][0])
            prompt = (
                f"Bạn là Trợ lý ảo tư vấn thủ tục hành chính công của UBND Phường (Bộ phận Một cửa).\n"
                f"DƯỚI ĐÂY LÀ CƠ SỞ DỮ LIỆU THỦ TỤC CỦA PHƯỜNG:\n"
                f"---------------------\n"
                f"{context}\n"
                f"---------------------\n\n"
                f"CÂU HỎI CỦA CÔNG DÂN: \"{query.text}\"\n\n"
                f"HÃY TUÂN THỦ NGHIÊM NGẶT CÁC NGUYÊN TẮC SAU:\n"
                f"1. NẾU THỦ TỤC CÓ TRONG TÀI LIỆU TRÊN (như kết hôn, khai sinh, khai tử, hỏa táng, liệt sĩ, xây dựng...):\n"
                f"   - Hãy hướng dẫn đúng theo tài liệu gồm: Thành phần hồ sơ cần có, Thời gian giải quyết và Lệ phí chuẩn.\n"
                f"   - Trình bày dạng gạch đầu dòng rõ ràng, mạch lạc, dễ hiểu cho người dân.\n\n"
                f"2. NẾU THỦ TỤC KHÔNG CÓ TRONG TÀI LIỆU (hoặc thuộc cơ quan khác):\n"
                f"   - Ví dụ: Làm lại thẻ Căn cước/CCCD bị mất, Cấp hộ chiếu... là thủ tục thuộc thẩm quyền của CÔNG AN cấp quận/huyện hoặc Cổng Dịch vụ công Bộ Công an, KHÔNG thuộc thẩm quyền UBND Phường.\n"
                f"   - Hãy giải thích rõ điều này cho công dân và hướng dẫn họ mang giấy tờ đến Công an quận/huyện hoặc làm trực tuyến qua app VNeID / Cổng DVC Bộ Công an.\n"
                f"   - TUYỆT ĐỐI KHÔNG TỰ BỊA ĐẶT các bước kỳ quặc (như quay video, thủ tục lạ lùng) không có thật.\n\n"
                f"3. VĂN PHONG: Trang trọng, lịch sự, ân cần, đúng chuẩn mực cán bộ hành chính công vụ Việt Nam.\n\n"
                f"CÂU TRẢ LỜI CỦA BẠN:"
            )
            
        elif intent == "NGOAI":
            clean_q = query.text.replace("\\", "").strip()
            context = ""
            try:
                search_res = DDGS().text(clean_q, max_results=3)
                if search_res:
                    context = "\n".join([r.get('body', '') for r in search_res])
            except Exception as search_err:
                print("Lỗi tìm kiếm mạng:", search_err)
                context = "Không thể kết nối Internet thời gian thực. Hãy dùng kiến thức pháp luật chung để trả lời."
            prompt = (
                f"Bạn là Trợ lý tư vấn pháp lý và kiến thức xã hội Việt Nam.\n"
                f"THÔNG TIN TRA CỨU MỚI NHẤT:\n"
                f"---------------------\n"
                f"{context}\n"
                f"---------------------\n\n"
                f"CÂU HỎI: \"{clean_q}\"\n\n"
                f"NGUYÊN TẮC TRẢ LỜI:\n"
                f"1. Dựa vào thông tin tra cứu hoặc quy định pháp luật hiện hành để trả lời chính xác, đi thẳng vào trọng tâm.\n"
                f"2. Nếu hỏi về mức phạt vi phạm (ví dụ: giao thông, nồng độ cồn, không đội mũ bảo hiểm), hãy nêu rõ mức tiền phạt và viện dẫn số hiệu Nghị định (như Nghị định 100/2019/NĐ-CP hoặc 123/2021/NĐ-CP) nếu có.\n"
                f"3. Trả lời ngắn gọn, chuẩn xác, không dài dòng lan man.\n\n"
                f"CÂU TRẢ LỜI CỦA BẠN:"
            )
            
        else: # XAGIAO
            prompt = (
                f"Bạn là Trợ lý ảo tư vấn thủ tục hành chính công của UBND Phường.\n"
                f"Công dân đang giao tiếp với bạn: \"{query.text}\"\n\n"
                f"Hãy phản hồi lịch sự, thân thiện bằng tiếng Việt (1-2 câu ngắn gọn), giới thiệu bạn có thể hỗ trợ tra cứu các thủ tục hành chính (như Hộ tịch, Đất đai, Xây dựng, Chính sách xã hội...) hoặc giải đáp quy định pháp luật."
            )

        response = ollama.chat(model='qwen2.5:1.5b', messages=[
            {'role': 'user', 'content': prompt}
        ])
        answer = response['message']['content']
        
    except Exception as e:
        answer = str(e)
        intent = "ERROR"
        score = 0.0
        
    return {"answer": answer, "intent": intent, "score": score}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
