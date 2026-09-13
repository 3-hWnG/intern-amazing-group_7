from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
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
<html data-theme="dark">
<head>
    <title>Trợ Lý Pháp Lý - Nhóm 7</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --bg-color: #ffffff;
            --text-color: #0f0f0f;
            --chat-bg: #ffffff;
            --user-msg: #f4f4f4;
            --bot-msg: #ffffff;
            --border: #e5e5e5;
            --accent: #10a37f;
            --router-color: #888;
        }
        [data-theme="dark"] {
            --bg-color: #212121;
            --text-color: #ececec;
            --chat-bg: #212121;
            --user-msg: #2f2f2f;
            --bot-msg: #212121;
            --border: #333;
            --accent: #10a37f;
            --router-color: #aaa;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: var(--bg-color); color: var(--text-color); height: 100vh; display: flex; flex-direction: column; transition: background-color 0.3s, color 0.3s; }
        .header { padding: 15px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--chat-bg); }
        .theme-toggle { background: none; border: 1px solid var(--border); border-radius: 8px; padding: 5px 10px; font-size: 14px; cursor: pointer; color: var(--text-color); transition: 0.2s; }
        .theme-toggle:hover { background: var(--user-msg); }
        .chat-container { flex: 1; overflow-y: auto; display: flex; flex-direction: column; align-items: center; background: var(--chat-bg); scroll-behavior: smooth; }
        .msg-wrapper { width: 100%; display: flex; justify-content: center; padding: 25px 20px; border-bottom: 1px solid var(--border); }
        .msg-wrapper.user { background: var(--user-msg); }
        .msg-wrapper.bot { background: var(--bot-msg); }
        .msg-content { max-width: 800px; width: 100%; display: flex; gap: 20px; line-height: 1.6; font-size: 15px; }
        .avatar { width: 36px; height: 36px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; }
        .avatar.user-av { background: #5436da; color: white; }
        .avatar.bot-av { background: var(--accent); color: white; }
        .text { flex: 1; white-space: pre-wrap; margin-top: 5px; }
        .router-log { font-size: 0.8em; color: var(--router-color); margin-bottom: 10px; font-family: monospace; background: rgba(0,0,0,0.05); padding: 5px 10px; border-radius: 4px; display: inline-block; }
        [data-theme="dark"] .router-log { background: rgba(255,255,255,0.05); }
        .input-area { padding: 25px 20px; display: flex; justify-content: center; background: var(--bg-color); }
        .input-box { max-width: 800px; width: 100%; display: flex; background: var(--chat-bg); border: 1px solid var(--border); border-radius: 24px; padding: 8px 12px; box-shadow: 0 0 15px rgba(0,0,0,0.05); }
        [data-theme="dark"] .input-box { box-shadow: 0 0 15px rgba(0,0,0,0.2); }
        input { flex: 1; background: transparent; border: none; outline: none; color: var(--text-color); font-size: 15px; padding: 10px; }
        button.send-btn { background: var(--accent); color: white; border: none; border-radius: 50%; width: 35px; height: 35px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; margin-top: 3px; }
        button.send-btn:hover { opacity: 0.8; }
        .typing { animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0.5; } }
    </style>
</head>
<body>
    <div class="header">
        <h3 style="font-weight: 600;">Legal AI - Nhóm 7</h3>
        <button class="theme-toggle" onclick="toggleTheme()">🌓 Đổi nền</button>
    </div>
    
    <div class="chat-container" id="chat">
        <div class="msg-wrapper bot">
            <div class="msg-content">
                <div class="avatar bot-av">AI</div>
                <div class="text">Xin chào! Tôi là Trợ lý Ảo Pháp lý do Nhóm 7 phát triển. Bạn cần tư vấn thủ tục hành chính hay tra cứu luật gì hôm nay?</div>
            </div>
        </div>
    </div>

    <div class="input-area">
        <div class="input-box">
            <input type="text" id="query" placeholder="Nhập câu hỏi pháp lý của bạn..." onkeypress="if(event.key === 'Enter') send()">
            <button class="send-btn" onclick="send()">➤</button>
        </div>
    </div>

    <script>
        function toggleTheme() {
            let html = document.documentElement;
            html.setAttribute('data-theme', html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
        }

        async function send() {
            let query = document.getElementById('query').value;
            if (!query.trim()) return;
            
            let chat = document.getElementById('chat');
            chat.innerHTML += `
                <div class="msg-wrapper user">
                    <div class="msg-content">
                        <div class="avatar user-av">U</div>
                        <div class="text">${query}</div>
                    </div>
                </div>`;
            document.getElementById('query').value = '';
            
            let botMsgId = "msg-" + Date.now();
            chat.innerHTML += `
                <div class="msg-wrapper bot">
                    <div class="msg-content">
                        <div class="avatar bot-av">AI</div>
                        <div class="text" id="${botMsgId}">
                            <span class="typing">Đang kết nối não AI...</span>
                        </div>
                    </div>
                </div>`;
            chat.scrollTop = chat.scrollHeight;

            try {
                let response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: query})
                });

                if (!response.ok) throw new Error("Server trả về lỗi");

                let intent = response.headers.get("X-Intent") || "UNKNOWN";
                let score = response.headers.get("X-Score") || "0.0";
                
                let textContainer = document.getElementById(botMsgId);
                let logHtml = `<div class="router-log">[Router: ${intent} | Độ tin cậy: ${score}]</div><br>`;
                textContainer.innerHTML = logHtml;

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    let chunkText = decoder.decode(value, {stream: true});
                    textContainer.innerHTML += chunkText;
                    chat.scrollTop = chat.scrollHeight;
                }

            } catch (err) {
                document.getElementById(botMsgId).innerHTML = `<span style="color:red">Lỗi hệ thống: ${err}</span>`;
            }
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

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "..", "data", "chromadb")

print("Loading Database & Semantic Router...")
try:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embed_model = SentenceTransformer("keepitreal/vietnamese-sbert", device=device)
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name="legal_docs")
    
    luat_anchors = ["đăng ký kết hôn", "thủ tục ly hôn", "làm giấy khai sinh", "đăng ký khai tử",
    "xác nhận độc thân", "xác nhận tình trạng hôn nhân", "trích lục khai sinh",
    "nhận cha mẹ con", "thay đổi họ tên", "cải chính hộ tịch",
    "mất căn cước công dân", "làm lại cccd", "đổi thẻ căn cước", "căn cước gắn chip",
    "đăng ký tạm trú", "đăng ký thường trú", "giấy xác nhận cư trú ct07", "hộ khẩu",
    "làm hộ chiếu", "passport", "tài khoản vneid", "định danh điện tử",
    "sang tên sổ đỏ", "làm sổ hồng", "cấp giấy phép xây dựng", "sửa chữa nhà",
    "trích lục địa chính", "đo đạc đất đai", "chuyển mục đích sử dụng đất",
    "xác nhận tình trạng quy hoạch", "tranh chấp đất đai",
    "công chứng giấy tờ", "chứng thực bản sao", "sao y bản chính",
    "chứng thực chữ ký", "chứng thực hợp đồng ủy quyền", "giấy ủy quyền",
    "trợ cấp mai táng", "tiền hỗ trợ hỏa táng", "chế độ liệt sĩ", "thương binh",
    "hỗ trợ hộ nghèo", "trợ cấp bảo trợ xã hội", "làm thẻ bảo hiểm y tế miễn phí",
    "đăng ký hộ kinh doanh", "mở cửa hàng buôn bán", "tạm ngừng kinh doanh",
    "thủ tục hành chính", "hồ sơ cần giấy tờ gì", "thời gian giải quyết bao lâu",
    "lệ phí bao nhiêu tiền", "nộp hồ sơ một cửa", "cổng dịch vụ công trực tuyến"]

    luat_emb = np.mean(embed_model.encode(luat_anchors, device=device), axis=0)

    xagiao_anchors = ["xin chào", "chào bạn", "hello", "helo", "hế lô", "hê lô", "hi", "alo",
    "chào buổi sáng", "bạn là ai", "bạn tên gì", "cảm ơn bạn", "tạm biệt",
    "chúc bạn một ngày tốt lành", "tư vấn giúp tôi với"]
    xagiao_emb = np.mean(embed_model.encode(xagiao_anchors, device=device), axis=0)

    ngoai_anchors = ["vượt đèn đỏ phạt bao nhiêu tiền", "lỗi không đội mũ bảo hiểm",
    "uống rượu lái xe phạt bao nhiêu", "nồng độ cồn xe máy", "bị bắn tốc độ", 
    "giá vàng hôm nay", "thời tiết", "chứng khoán", "tin tức thời sự", "bão lũ"]
    ngoai_emb = np.mean(embed_model.encode(ngoai_anchors, device=device), axis=0)

except Exception as e:
    print("LỖI KHỞI TẠO:", e)

try:
    ollama.chat(
        model='qwen2.5:1.5b',
        messages=[{'role': 'user', 'content': 'hi'}],
        options={'num_predict': 1},
        keep_alive='30m'
    )
except Exception as e:
    print("Warm-up Ollama:", e)

def classify_intent_semantic(text: str): 
    q_emb = embed_model.encode(text, device=device)

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
            results = collection.query(query_embeddings=[q_emb.tolist()], n_results=3)
            context_blocks = []
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                updated_date = meta.get('updated_at', 'Mới nhất')
                context_blocks.append(
                    f"--- {meta.get('title', 'Thủ tục')} (Lĩnh vực: {meta.get('field', 'Hành chính công')} | Cập nhật ngày: {updated_date}) ---\n"
                    f"Hình thức nộp: {meta.get('submission', 'Trực tiếp / Trực tuyến')}\n"
                    f"{doc}"
                )
            context = "\n\n".join(context_blocks)
            prompt = (
                f"Bạn là Trợ lý ảo tư vấn thủ tục hành chính công Việt Nam.\n"
                f"DƯỚI ĐÂY LÀ DỮ LIỆU THỦ TỤC CHÍNH THỨC:\n"
                f"---------------------\n"
                f"{context}\n"
                f"---------------------\n\n"
                f"CÂU HỎI CỦA CÔNG DÂN: \"{query.text}\"\n\n"
                f"Hãy hướng dẫn ngắn gọn cho công dân theo đúng cấu trúc gạch đầu dòng sau:\n"
                f"- Tên thủ tục:\n"
                f"- Lĩnh vực:\n"
                f"- Hồ sơ cần chuẩn bị:\n"
                f"- Thời gian giải quyết & Lệ phí:\n"
                f"- Hình thức & Nơi tiếp nhận:\n\n"
                f"NGUYÊN TẮC BẮT BUỘC:\n"
                f"1. VĂN PHONG CỰC KỲ NGẮN GỌN. TUYỆT ĐỐI KHÔNG DÔNG DÀI. TUYỆT ĐỐI KHÔNG NHẠI LẠI CÂU HỎI. ĐI THẲNG VÀO VẤN ĐỀ.\n"
                f"2. NƠI TIẾP NHẬN: Nêu rõ nếu nộp trực tuyến thì nộp qua Cổng Dịch vụ công Quốc gia (dichvucong.gov.vn) hoặc Cổng DVC cấp tỉnh; nếu nộp trực tiếp thì nộp tại Bộ phận Một cửa của UBND Xã/Phường nơi cư trú (hoặc cơ quan có thẩm quyền theo quy định). Tuyệt đối KHÔNG nêu tên riêng của bất kỳ phường/xã cụ thể nào.\n"
                f"3. NẾU THỦ TỤC CÓ TRONG TÀI LIỆU TRÊN: Chỉ liệt kê Thành phần hồ sơ, Thời gian và Lệ phí dưới dạng gạch đầu dòng ngắn gọn.\n"
                f"4. NẾU THỦ TỤC KHÔNG CÓ TRONG TÀI LIỆU: Chỉ hướng dẫn người dân liên hệ Công an xã/phường/quận hoặc truy cập Cổng Dịch vụ công Quốc gia để tra cứu. CẤM BỊA ĐẶT THỦ TỤC.\n\n"
                f"TRẢ LỜI NGAY VÀO TRỌNG TÂM:"
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
                f"THÔNG TIN TRA CỨU MỚI NHẤT TỪ INTERNET:\n"
                f"---------------------\n"
                f"{context}\n"
                f"---------------------\n\n"
                f"CÂU HỎI: \"{clean_q}\"\n\n"
                f"NGUYÊN TẮC TRẢ LỜI:\n"
                f"1. TUYỆT ĐỐI KHÔNG NHẠI LẠI CÂU HỎI. TRẢ LỜI NGẮN GỌN, VÀO THẲNG VẤN ĐỀ CHÍNH.\n"
                f"2. Dựa vào thông tin tra cứu hoặc quy định pháp luật hiện hành để trả lời.\n\n"
                f"TRẢ LỜI NGAY VÀO TRỌNG TÂM:"
            )
            
        else: 
            prompt = (
                f"Bạn là Trợ lý tư vấn pháp lý.\n"
                f"Công dân đang giao tiếp với bạn: \"{query.text}\"\n\n"
                f"TUYỆT ĐỐI KHÔNG NHẠI LẠI CÂU HỎI. Hãy phản hồi thân thiện, NGẮN GỌN TRONG 1 CÂU DUY NHẤT, báo rằng bạn sẵn sàng hỗ trợ thủ tục hành chính (Sổ đỏ, hộ khẩu, đăng ký kết hôn...)."
            )

        def generate():
            try:
                stream = ollama.chat(model='qwen2.5:1.5b', messages=[
                    {'role': 'user', 'content': prompt}
                ], stream=True, options={
                    'repeat_penalty': 1.2,   
                    'temperature': 0.2,      
                    'num_predict': 350
                })
                for chunk in stream:
                    yield chunk['message']['content']
            except Exception as e:
                yield f"\n[Lỗi kết nối Ollama]: {str(e)}"
        
        headers = {"X-Intent": intent, "X-Score": str(score)}
        return StreamingResponse(generate(), media_type="text/plain", headers=headers)
        
    except Exception as e:
        headers = {"X-Intent": "ERROR", "X-Score": "0.0"}
        def error_gen():
            yield str(e)
        return StreamingResponse(error_gen(), media_type="text/plain", headers=headers)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
