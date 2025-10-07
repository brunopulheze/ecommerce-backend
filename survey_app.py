from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
surveys_collection = db["surveys"]

router = APIRouter()

class SurveySubmission(BaseModel):
    preferredLayout: str  # "A" or "B"
    shoppingFrequency: str
    favoriteDevice: str
    influencingFactors: List[str]
    satisfactionLevel: str
    comments: Optional[str] = ""

@router.post("/survey")
def submit_survey(survey: SurveySubmission):
    survey_dict = survey.dict()
    survey_dict["submittedAt"] = datetime.utcnow().isoformat()
    result = surveys_collection.insert_one(survey_dict)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to save survey")
    return {"message": "Survey saved successfully"}