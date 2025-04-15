from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

import ast

import os

from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_codebase(path):
    docs=[]
    for root, _,files in os.walk(path):
        for file in files:
            if file.endswith(".py") or file.endswith("ipynb"):
                with open(os.path.join(root,file),"r") as f:
                    content= f.read()
                    docs.append(Document(page_content=content,metadata={"source":file,"code_metadata":extract_code_info(content)}))
    return docs


def generate_and_store_embeddings(code_path:str,index_path:str="faiss_index"):
    docs = load_codebase(code_path) ## "/Users/gaurav/python-codebot/codebase"
    print(f"Loaded {len(docs)} documents from codebase")

    splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=150)
    splits=splitter.split_documents(docs)
    print(f"Total chunks created: {len(splits)}")


    embedding_model=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore= FAISS.from_documents(splits,embedding=embedding_model) 
    vectorstore.save_local(index_path)
    return {"message":f"embedding created with {len(splits)} chunks"}


def extract_code_info(code_text: str):
    tree=ast.parse(code_text)
    summary ={"Class":[],
              "Function":[],
              "Variable":[],
              "Annotated Variable":[]}

    for node in ast.walk(tree):
        if  isinstance(node,ast.ClassDef):
            summary["Class"].append(node.name)
        elif isinstance(node,ast.FunctionDef):
            args= [arg.arg for arg in node.args.args]
            # summary.append(f"Function: {node.name} ({','.join(args)})")
            summary["Function"].append(f"{node.name} ({','.join(args)})")
        elif isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name):
                    # summary.append(f"Variable: {target.id}")
                    summary["Variable"].append(target.id)
        elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name):
                # summary.append(f"Annotated Variable: {node.target.id}")
                summary["Annotated Variable"].append(node.target.id)
    
    return summary


