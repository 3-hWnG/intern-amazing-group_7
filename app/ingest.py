import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import os

print("Loading dataset...")
df = pd.read_excel("../data/dataset.xlsx")

df = df.dropna(subset=["Tên thủ tục hành chính"])

documents = []
metadatas = []
ids = []

for idx, row in df.iterrows():
    title = str(row.get("Tên thủ tục hành chính", "")).strip()
    reqs = str(row.get("Thành phần hồ sơ", "")).strip()
    time = str(row.get("Thời gian giải quyết", "")).strip()
    fee = str(row.get("Lệ phí", "")).strip()
    
    doc_text = f"Thủ tục: {title}\nThành phần hồ sơ: {reqs}\nThời gian: {time}\nLệ phí: {fee}"
    
    documents.append(doc_text)
    metadatas.append({"title": title})
    ids.append(str(idx))

print(f"Processed {len(documents)} documents. Initializing ChromaDB...")
client = chromadb.PersistentClient(path="../data/chromadb")
collection = client.get_or_create_collection(name="legal_docs")

print("Loading embedding model (this may take a minute)...")
model = SentenceTransformer("keepitreal/vietnamese-sbert")

print("Embedding and adding to DB...")
embeddings = model.encode(documents).tolist()

collection.add(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas
)

print("Done! Database ready.")
