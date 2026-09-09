import ollama
text = 'Tin tức bão Yagi'
prompt = f"""Phân loại câu hỏi vào 1 trong 3 nhóm: XAGIAO, LUAT, NGOAI.
Ví dụ:
- 'Chào bạn', 'Khỏe không' -> XAGIAO
- 'Thủ tục kết hôn', 'Rút BHXH' -> LUAT
- 'Giá vàng hôm nay', 'Tin tức bão' -> NGOAI
- 'Cấp lại thẻ căn cước' -> LUAT

Câu hỏi: {text}
Kết quả (chỉ in đúng 1 từ):"""
resp = ollama.chat(model='qwen2.5:1.5b', messages=[{'role': 'user', 'content': prompt}])
print('LLM OUTPUT:', resp['message']['content'])
