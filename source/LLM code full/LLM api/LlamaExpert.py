from langchain_core.prompts.chat import ChatPromptTemplate
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
import torch

class LlamaExpert():
    '''Llama answering based on the text provided input(article+question)'''
    def __init__(self, model,verbose:bool=True):
        self.model = model
        self.llm = model.model
        self.verbose = verbose
        prompt = """Answer the question below using the context:
                    Context: {context}
                    Question: {question}
                    Answer: """
        self.prompt_lcel = ChatPromptTemplate.from_template(prompt)

    def delete_spaces(self, text):
        return ' '.join(text.splitlines())

    
    def create_vectore_store(self, article):
        if self.verbose:
            print("Creating the vectore store please wait...")
        embedding_model = "sentence-transformers/all-mpnet-base-v2" 
        embeddings = HuggingFaceEmbeddings(model_name=embedding_model, multi_process=True)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=20)
        ready_article = self.delete_spaces(article)
        document = [Document(page_content=ready_article)]
        chunks = text_splitter.split_documents(document)
        vectore_store = FAISS.from_documents(chunks, embeddings)
        retriever = vectore_store.as_retriever()
        return retriever
    
    def create_chain(self, article):
        retriever = self.create_vectore_store(article)
        if retriever:
            setup_and_retrieval = RunnableParallel({"question":RunnablePassthrough(), "context":retriever})
            output_parser = StrOutputParser()
            self.retrieval_chain = setup_and_retrieval | self.prompt_lcel | self.llm | output_parser
            return self.retrieval_chain
        else:
            return None
        
    def ask_question(self, question, article):
        chain = self.create_chain(article)
        if chain:
            result = chain.invoke(question)
            if self.model.device is int and self.model.device < 0:
                pass
            else:
                torch.cuda.empty_cache()
            return result
        else:
            raise RuntimeError("Unable to create Llama chain")

        