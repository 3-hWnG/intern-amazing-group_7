import numpy as np
from sentence_transformers import SentenceTransformer

embed_model = SentenceTransformer("keepitreal/vietnamese-sbert")

luat_emb = embed_model.encode("hỏi đáp thủ tục hành chính, quy định pháp luật, hồ sơ, giấy tờ, đăng ký, lệ phí")
ngoai_emb = embed_model.encode("tin tức thời sự, giá vàng, thị trường, chứng khoán, thời tiết, bão lũ, hôm nay")
xagiao_emb = embed_model.encode("xin chào, bạn tên gì, cảm ơn, khỏe không, trò chuyện")

def classify(text):
    q_emb = embed_model.encode(text)
    scores = {
        "LUAT": np.dot(q_emb, luat_emb) / (np.linalg.norm(q_emb)*np.linalg.norm(luat_emb)),
        "NGOAI": np.dot(q_emb, ngoai_emb) / (np.linalg.norm(q_emb)*np.linalg.norm(ngoai_emb)),
        "XAGIAO": np.dot(q_emb, xagiao_emb) / (np.linalg.norm(q_emb)*np.linalg.norm(xagiao_emb))
    }
    return max(scores, key=scores.get), scores

print(classify("Giá vàng SJC hôm nay là bao nhiêu?"))
print(classify("Thủ tục đăng ký khai sinh gồm những gì?"))
print(classify("Chào bạn, bạn có thể giúp gì cho tôi?"))
