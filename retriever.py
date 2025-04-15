from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

import re
import os

from langchain_text_splitters import RecursiveCharacterTextSplitter



def get_answer(query:str,index_path:str="faiss_index"):
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local(index_path, embedding_model,allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever()
    llm= ChatGroq(model="llama3-70b-8192")


    # Define the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Use the given context to answer the question.\n\n{context} \n\n Also include relevant code snippets {code_context}
        If you find relevant functions, classes, or code examples in the context or code_context, include them in the answer.

         """),
        ("human", "{input}")
    ])

    # Create the document chain
    document_chain= create_stuff_documents_chain(llm=llm,prompt=prompt)

    # Create the retrieval chain
    retrieval_chain = create_retrieval_chain(retriever, document_chain)


    docs = retriever.get_relevant_documents(query)
    
    code_context="\n\n".join(doc.page_content for doc in docs)
    response = retrieval_chain.invoke({"input": query,"code_context":code_context})
    print(response["answer"])
    return {"answer":response["answer"]}