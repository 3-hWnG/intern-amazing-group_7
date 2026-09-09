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
    luat_emb = embed_model.encode("hỏi đáp thủ tục hành chính, quy định pháp luật, hồ sơ, giấy tờ, đăng ký, lệ phí, nhà nước, công dân")
    ngoai_emb = embed_model.encode("tin tức thời sự, giá cả thị trường, chứng khoán, thời tiết, bão lũ, hôm nay, kiến thức ngoài lề, sự kiện")
    xagiao_emb = embed_model.encode("xin chào, bạn tên gì, cảm ơn, khỏe không, trò chuyện, tâm sự, giao tiếp cơ bản")
except:
    pass

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
    return best_intent, best_score

@app.post("/chat")
async def chat_endpoint(query: Query):
    try:
        intent, score = classify_intent_semantic(query.text)
        
        if intent == "LUAT":
            query_embed = embed_model.encode(query.text).tolist()
            results = collection.query(query_embeddings=[query_embed], n_results=2)
            context = "\\n\\n".join(results['documents'][0])
            prompt = f"Trả lời CÂU HỎI dựa vào TÀI LIỆU RAG sau:\n{context}\nCÂU HỎI: {query.text}"
            
        elif intent == "NGOAI":
            search_res = DDGS().text(query.text, max_results=3)
            context = "\\n".join([r['body'] for r in search_res]) if search_res else "Không tìm thấy trên mạng."
            prompt = f"Trả lời CÂU HỎI dựa vào TIN TỨC TỪ MCP (DUCKDUCKGO) sau:\n{context}\nCÂU HỎI: {query.text}"
            
        else: # XAGIAO
            prompt = f"Bạn là trợ lý ảo. Trò chuyện thân thiện với người dùng: {query.text}"

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
