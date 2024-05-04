from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer
from langchain.llms import OpenAI
from langchain.llms import HuggingFaceHub
from config import DATA_DIR, LEGAL_EMBEDDING_MODEL, LEGAL_EMBEDDING_MODEL_DEVICE_TYPE, CHROMA_CLI
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
load_dotenv()


app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from config import DATA_DIR, LEGAL_EMBEDDING_MODEL, LEGAL_EMBEDDING_MODEL_DEVICE_TYPE, CHROMA_CLI
app.state.LEGAL_EMBEDDING_MODEL = LEGAL_EMBEDDING_MODEL
app.state.LEGAL_EMBEDDING_MODEL_DEVICE_TYPE = LEGAL_EMBEDDING_MODEL_DEVICE_TYPE
app.state.CHROMA_CLI = CHROMA_CLI

model = SentenceTransformer('all-MiniLM-L6-v2')
llm_client = HuggingFaceHub(repo_id="NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO", model_kwargs={"temperature": 0.2, "max_length": 10000})

class LegalQuery(BaseModel):
    query: str

class DocumentDescription(BaseModel):
    date_of_judgement: str
    case_title: str
    short_description: str

class AnswerResult(BaseModel):
    answer: str
    documents: List[DocumentDescription]  

def parse_reference(reference: str):
    parts = reference.split('case_title:')
    date_of_judgement = parts[0].strip().replace('date of judgement:', '').strip()
    case_title = parts[1].strip() if len(parts) > 1 else "Unknown Title"
    return date_of_judgement, case_title

@app.post("/legalsearch", response_model=AnswerResult)
async def legal_search(query_data: LegalQuery):
    query_embedding = model.encode(query_data.query)
    collection_name = "judgemasterdb"
    collection = app.state.CHROMA_CLI.get_collection(collection_name)
    results = collection.query(query_texts=[query_data.query], n_results=5)

    if not results['documents']:
        return JSONResponse(status_code=404, content={"detail": "No documents found."})

    documents = []
    for index, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][index]
        date_of_judgement, case_title = parse_reference(meta['reference'])
        prompt = f"Create a short description within 50 words for the legal case given in the context: {doc}"
        description = llm_client.generate(
            prompts=[prompt],
            max_new_tokens=120,
            temperature=0.2
        )
        description_text = description.generations[0][0].text.strip()

        documents.append(DocumentDescription(
            date_of_judgement=date_of_judgement,
            case_title=case_title,
            short_description=description_text
        ))

    answer = llm_client.generate(
        prompts=[f"Based on the following documents, answer the question: '{query_data.query}'"],
        max_new_tokens=1500,
        temperature=0.2
    )
    answer_text = answer.generations[0][0].text.strip() if answer.generations else "No answer generated."

    response_content = {
        "answer": answer_text,
        "documents": documents
    }

    return jsonable_encoder(response_content)
