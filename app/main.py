from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import chromadb
from sentence_transformers import SentenceTransformer
import ollama
from pydantic import BaseModel
import uvicorn
from duckduckgo_search import DDGS
import numpy as np
import torch

app = FastAPI()

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Trợ lý pháp lý - Demo</title>
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
    <h2> LLM Pháp lý  (Semantic Router) - Nhóm 7</h2>
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
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embed_model = SentenceTransformer("keepitreal/vietnamese-sbert", device=device)
    client = chromadb.PersistentClient(path="../data/chromadb")
    collection = client.get_or_create_collection(name="legal_docs")
    
    # Định nghĩa Cụm Vector Nhận diện Ngữ nghĩa (Không học vẹt từ khóa)
    luat_anchors = [
    # Hộ tịch & Gia đình
    "đăng ký kết hôn", "thủ tục ly hôn", "làm giấy khai sinh", "đăng ký khai tử",
    "xác nhận độc thân", "xác nhận tình trạng hôn nhân", "trích lục khai sinh",
    "nhận cha mẹ con", "thay đổi họ tên", "cải chính hộ tịch",
    
    # Giấy tờ tùy thân & Cư trú (Dù ở Phường hay Công an cũng thuộc mảng LUAT)
    "mất căn cước công dân", "làm lại cccd", "đổi thẻ căn cước", "căn cước gắn chip",
    "đăng ký tạm trú", "đăng ký thường trú", "giấy xác nhận cư trú ct07", "hộ khẩu",
    "làm hộ chiếu", "passport", "tài khoản vneid", "định danh điện tử",
    
    # Đất đai, Xây dựng & Nhà ở
    "sang tên sổ đỏ", "làm sổ hồng", "cấp giấy phép xây dựng", "sửa chữa nhà",
    "trích lục địa chính", "đo đạc đất đai", "chuyển mục đích sử dụng đất",
    "xác nhận tình trạng quy hoạch", "tranh chấp đất đai",
    
    # Chứng thực & Sao y
    "công chứng giấy tờ", "chứng thực bản sao", "sao y bản chính",
    "chứng thực chữ ký", "chứng thực hợp đồng ủy quyền", "giấy ủy quyền",
    
    # Chính sách xã hội & Người có công
    "trợ cấp mai táng", "tiền hỗ trợ hỏa táng", "chế độ liệt sĩ", "thương binh",
    "hỗ trợ hộ nghèo", "trợ cấp bảo trợ xã hội", "làm thẻ bảo hiểm y tế miễn phí",
    
    # Hộ kinh doanh & Dịch vụ công
    "đăng ký hộ kinh doanh", "mở cửa hàng buôn bán", "tạm ngừng kinh doanh",
    "thủ tục hành chính", "hồ sơ cần giấy tờ gì", "thời gian giải quyết bao lâu",
    "lệ phí bao nhiêu tiền", "nộp hồ sơ một cửa", "cổng dịch vụ công trực tuyến"]

    luat_emb = np.mean(embed_model.encode(luat_anchors, device=device), axis=0)

    xagiao_anchors = [
    "xin chào", "chào bạn", "hello", "helo", "hế lô", "hê lô", "hi", "alo",
    "chào buổi sáng", "bạn là ai", "bạn tên gì", "cảm ơn bạn", "tạm biệt",
    "chúc bạn một ngày tốt lành", "tư vấn giúp tôi với"]
    xagiao_emb = np.mean(embed_model.encode(xagiao_anchors, device=device), axis=0)

    ngoai_anchors = ["vượt đèn đỏ phạt bao nhiêu tiền", "lỗi không đội mũ bảo hiểm",
    "uống rượu lái xe phạt bao nhiêu", "nồng độ cồn xe máy", "bị bắn tốc độ"]
    ngoai_emb = np.mean(embed_model.encode(ngoai_anchors, device=device), axis=0)

except Exception as e:
    print("LỖI KHỞI TẠO:", e)

def classify_intent_semantic(text: str): 
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
    return best_intent, best_score, q_emb

@app.post("/chat")
async def chat_endpoint(query: Query):
    try:
        intent, score, q_emb = classify_intent_semantic(query.text)
        
        if intent == "LUAT":
            query_embed = embed_model.encode(query.text).tolist()
            results = collection.query(query_embeddings=[q_emb.tolist()], n_results=2)
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
            
        else: 
            prompt = (
                f"Bạn là Trợ lý ảo tư vấn thủ tục hành chính công của UBND Phường.\n"
                f"Công dân đang giao tiếp với bạn: \"{query.text}\"\n\n"
                f"Hãy phản hồi lịch sự, thân thiện bằng tiếng Việt (1-2 câu ngắn gọn), giới thiệu bạn có thể hỗ trợ tra cứu các thủ tục hành chính (như Hộ tịch, Đất đai, Xây dựng, Chính sách xã hội...) hoặc giải đáp quy định pháp luật."
            )

        response = ollama.chat(model='qwen2.5:1.5b', messages=[
            {'role': 'user', 'content': prompt}
        ], options={
                'repeat_penalty': 1.2,   
                'temperature': 0.2,      
                'num_predict': 350}       
        )
        answer = response['message']['content']
        
    except Exception as e:
        answer = str(e)
        intent = "ERROR"
        score = 0.0
        
    return {"answer": answer, "intent": intent, "score": score}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
