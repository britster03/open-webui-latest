
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from config import DATA_DIR
from dotenv import load_dotenv
import torch
from langchain.llms import HuggingFaceHub


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

MODEL_PATH = "/home/ubuntu/open-webui-main/backend/apps/caseprediction/"
llm_client = HuggingFaceHub(repo_id="NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO", model_kwargs={"temperature": 0.2, "max_length": 10000})

# Load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

class CaseQuery(BaseModel):
    query: str

class PredictionResult(BaseModel):
    prediction: int
    reasoning: str

@app.post("/caseprediction", response_model=PredictionResult)
async def case_prediction(query_data: CaseQuery):
    try:

        inputs = tokenizer(query_data.query, return_tensors="pt", padding=True, truncation=True, max_length=512)

        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=-1)
            prediction = predictions.numpy()[0]


        label = "accepted" if prediction == 1 else "rejected"


        reasoning_prompt = f"The following case was {label} based on the analysis: {query_data.query}"
        reasoning = llm_client.generate(
            prompts=[reasoning_prompt],
            max_new_tokens=2048,
            temperature=0.2,
            repitition_penalty=1.5
        )
        reasoning_text = reasoning.generations[0][0].text.strip() if reasoning.generations else "No reasoning generated."

        response_content = {
            "prediction": int(prediction),
            "reasoning": reasoning_text
        }

        return jsonable_encoder(response_content)


    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

