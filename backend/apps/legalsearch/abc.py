from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse  
import openai
from sentence_transformers import SentenceTransformer
from fastapi.encoders import jsonable_encoder
from langchain.llms import OpenAI  # Import LangChain's OpenAI wrapper
from config import DATA_DIR, LEGAL_EMBEDDING_MODEL, LEGAL_EMBEDDING_MODEL_DEVICE_TYPE, CHROMA_CLI

# initializing FastAPI app and CORS middleware
app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# load configurations and models
app.state.LEGAL_EMBEDDING_MODEL = LEGAL_EMBEDDING_MODEL
app.state.LEGAL_EMBEDDING_MODEL_DEVICE_TYPE = LEGAL_EMBEDDING_MODEL_DEVICE_TYPE
app.state.CHROMA_CLI = CHROMA_CLI
model = SentenceTransformer('all-MiniLM-L6-v2')

# OpenAI API key
llm_client = OpenAI(api_key="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")
# defining pydantic models for the requests and responses
class LegalQuery(BaseModel):
    query: str

class AnswerResult(BaseModel):
    answer: str
    source_document_text: str
    reference: str  # including reference in the response model

@app.post("/legalsearch", response_model=AnswerResult)
async def legal_search(query_data: LegalQuery):
    try:
        query_embedding = model.encode(query_data.query)
        collection_name = "judgemasterdb"
        collection = app.state.CHROMA_CLI.get_collection(collection_name)
        results = collection.query(query_texts=[query_data.query], n_results=5)

        if not results['documents']:
            raise HTTPException(status_code=404, detail="No documents found.")

        # extracting the most relevant document's text and reference
        document_texts = [doc for doc in results['documents'][0][:5]]  #top 5 documents
        document_references = [meta['reference'] for meta in results['metadatas'][0][:5]]

        # assuming each document requires a separate prompt for LLM generation
        # and concatenating results for simplicity (Note: This might not be efficient for large texts or many documents)
        concatenated_texts = "\n\n".join(document_texts)
        concatenated_references = "\n\n".join(document_references)

        llm_result= llm_client.generate(
            prompts=[f"Based on the following document, answer the question: '{query_data.query}'\n\n{concatenated_texts}"],
            max_tokens=1500,
            temperature=0.2
        )

        if llm_result.generations:
            # accessing the first Generation object and then its text attribute
            generated_text = llm_result.generations[0][0].text.strip()
        else:
            generated_text = "No answer generated."

        # prepare the response content
        response_content = {
            "answer": generated_text,
            "source_document_text": concatenated_texts,  
	    "reference": concatenated_references
        }

        # returning the response content in a JSONResponse, ensuring it can be displayed on the client side
        return jsonable_encoder(response_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
