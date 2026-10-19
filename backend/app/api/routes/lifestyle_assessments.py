"""Separate CDC lifestyle model prediction endpoint."""
from pathlib import Path
from typing import Any
import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
router=APIRouter(prefix="/lifestyle-assessments",tags=["lifestyle-assessments"])
FEATURES=["HighBP","HighChol","CholCheck","BMI","Smoker","Stroke","HeartDiseaseorAttack","PhysActivity","Fruits","Veggies","HvyAlcoholConsump","AnyHealthcare","NoDocbcCost","GenHlth","MentHlth","PhysHlth","DiffWalk","Sex","Age","Education","Income"]
KEYS=["high_bp","high_chol","chol_check","bmi","smoker","stroke","heart_disease_or_attack","phys_activity","fruits","veggies","hvy_alcohol_consump","any_healthcare","no_docbc_cost","gen_hlth","ment_hlth","phys_hlth","diff_walk","sex","age","education","income"]
DISCLAIMER="Research prototype only. This output is not a diagnosis, does not rule out diabetes, and should not guide treatment."
class LifestyleAssessmentInput(BaseModel):
 model_config=ConfigDict(extra="forbid")
 high_bp:int=Field(ge=0,le=1); high_chol:int=Field(ge=0,le=1); chol_check:int=Field(ge=0,le=1); bmi:float=Field(ge=10,le=100)
 smoker:int=Field(ge=0,le=1); stroke:int=Field(ge=0,le=1); heart_disease_or_attack:int=Field(ge=0,le=1); phys_activity:int=Field(ge=0,le=1)
 fruits:int=Field(ge=0,le=1); veggies:int=Field(ge=0,le=1); hvy_alcohol_consump:int=Field(ge=0,le=1); any_healthcare:int=Field(ge=0,le=1)
 no_docbc_cost:int=Field(ge=0,le=1); gen_hlth:int=Field(ge=1,le=5); ment_hlth:int=Field(ge=0,le=30); phys_hlth:int=Field(ge=0,le=30)
 diff_walk:int=Field(ge=0,le=1); sex:int=Field(ge=0,le=1); age:int=Field(ge=1,le=13); education:int=Field(ge=1,le=6); income:int=Field(ge=1,le=8)
 def feature_frame(self):
  values=self.model_dump()
  return pd.DataFrame([{col:values[key] for col,key in zip(FEATURES,KEYS)}],columns=FEATURES)
def artifact_path():
 return Path(__file__).resolve().parents[4]/"models"/"lifestyle"/"active-model.joblib"
@router.get("/status")
def status_lifestyle()->dict[str,Any]:
 path=artifact_path()
 if not path.is_file(): return {"available":False,"reason":"Run python -m app.ml.train_lifestyle from the backend directory."}
 try:
  package=joblib.load(path); metadata=package.get("metadata",{})
  if metadata.get("feature_schema")!=FEATURES:return {"available":False,"reason":"Lifestyle artifact schema mismatch."}
  return {"available":True,"metadata":metadata}
 except Exception:return {"available":False,"reason":"Lifestyle artifact could not be loaded."}
@router.post("/predict")
def predict_lifestyle(inputs:LifestyleAssessmentInput):
 path=artifact_path()
 if not path.is_file():raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Lifestyle model is not trained. Run python -m app.ml.train_lifestyle.")
 try:
  package=joblib.load(path); metadata=package["metadata"]
  if metadata.get("feature_schema")!=FEATURES:raise ValueError("Schema mismatch")
  probability=float(package["pipeline"].predict_proba(inputs.feature_frame())[0,1]); predicted=int(probability>=float(metadata.get("threshold",0.5)))
  return {"prediction":predicted,"prediction_label":"Survey profile is in the dataset's prediabetes/diabetes positive class" if predicted else "Survey profile is in the dataset's no-diabetes class","probability":probability,"model":{"name":metadata.get("name","cdc_lifestyle_ensemble"),"version":metadata.get("version","unknown")},"target_definition":"UCI CDC Diabetes Health Indicators target: 1 combines prediabetes and diabetes; 0 indicates no diabetes in the source survey.","disclaimer":DISCLAIMER}
 except HTTPException:raise
 except Exception as exc:raise HTTPException(status_code=503,detail="Lifestyle artifact is invalid or incompatible.") from exc
