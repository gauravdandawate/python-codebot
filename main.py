from fastapi import FastAPI, Query

from embed_store import generate_and_store_embeddings
from retriever import get_answer

#export GROQ_API_KEY="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" 
app=FastAPI()


#uvicorn main:app --reload

@app.post("/embed")
def embed(code_path:str=Query(...,description="path to codebase")):
    return generate_and_store_embeddings(code_path)

@app.post("/ask")
def ask(query:str=Query(...,description="qeury for codebase")):
    return get_answer(query)