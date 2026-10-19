"""Train independent CDC lifestyle ensemble. Run: python -m app.ml.train_lifestyle"""
import hashlib,json,platform
from datetime import UTC,datetime
from pathlib import Path
import joblib,pandas as pd,sklearn
from ucimlrepo import fetch_ucirepo
from sklearn.ensemble import HistGradientBoostingClassifier,RandomForestClassifier,VotingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,balanced_accuracy_score,brier_score_loss,f1_score,precision_score,recall_score,roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
FEATURES=["HighBP","HighChol","CholCheck","BMI","Smoker","Stroke","HeartDiseaseorAttack","PhysActivity","Fruits","Veggies","HvyAlcoholConsump","AnyHealthcare","NoDocbcCost","GenHlth","MentHlth","PhysHlth","DiffWalk","Sex","Age","Education","Income"]
SEED=2026
def main():
 print("Fetching UCI ML Repository dataset 891 (CDC Diabetes Health Indicators)…")
 dataset=fetch_ucirepo(id=891); frame=dataset.data.features.copy(); targets=dataset.data.targets
 target_name="Diabetes_binary" if "Diabetes_binary" in targets.columns else targets.columns[0]
 missing=sorted(set(FEATURES)-set(frame.columns))
 if missing:raise ValueError("UCI schema mismatch; missing: "+", ".join(missing))
 frame=frame.loc[:,FEATURES].apply(pd.to_numeric,errors="raise"); target=pd.to_numeric(targets[target_name],errors="raise").astype(int)
 if set(target.unique())!={0,1}:raise ValueError("Expected binary target values 0 and 1.")
 Xtr,Xte,ytr,yte=train_test_split(frame,target,test_size=.2,random_state=SEED,stratify=target)
 def pipe(est,scale=False):
  steps=[("imputer",SimpleImputer(strategy="median"))]
  if scale:steps.append(("scaler",StandardScaler()))
  steps.append(("model",est));return Pipeline(steps)
 models=[("logistic_regression",pipe(LogisticRegression(max_iter=2000,class_weight="balanced",random_state=SEED),True)),("random_forest",pipe(RandomForestClassifier(n_estimators=250,min_samples_leaf=2,class_weight="balanced_subsample",n_jobs=-1,random_state=SEED))),("xgboost",pipe(XGBClassifier(n_estimators=250,max_depth=5,learning_rate=.05,subsample=.85,colsample_bytree=.85,eval_metric="logloss",n_jobs=-1,random_state=SEED))),("hist_gradient_boosting",pipe(HistGradientBoostingClassifier(max_iter=200,learning_rate=.08,random_state=SEED)))]
 model=VotingClassifier(estimators=models,voting="soft",n_jobs=1);model.fit(Xtr,ytr);probs=model.predict_proba(Xte)[:,1];preds=(probs>=.5).astype(int)
 metrics={"accuracy":round(float(accuracy_score(yte,preds)),6),"balanced_accuracy":round(float(balanced_accuracy_score(yte,preds)),6),"precision":round(float(precision_score(yte,preds,zero_division=0)),6),"recall":round(float(recall_score(yte,preds,zero_division=0)),6),"f1":round(float(f1_score(yte,preds,zero_division=0)),6),"roc_auc":round(float(roc_auc_score(yte,probs)),6),"brier_score":round(float(brier_score_loss(yte,probs)),6),"threshold":.5,"test_rows":int(len(yte)),"positive_prevalence":round(float(yte.mean()),6)}
 root=Path(__file__).resolve().parents[3]; artifact=root/"models"/"lifestyle"/"active-model.joblib";artifact.parent.mkdir(parents=True,exist_ok=True)
 digest=hashlib.sha256(pd.concat([frame,target.rename(target_name)],axis=1).to_csv(index=False).encode()).hexdigest()
 metadata={"name":"cdc_lifestyle_ensemble","version":datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),"algorithm":"soft-voting ensemble","feature_schema":FEATURES,"schema_version":"uci-cdc-diabetes-health-indicators-v1","dataset_id":891,"dataset_name":"CDC Diabetes Health Indicators","target_name":target_name,"target_semantics":"1 combines prediabetes and diabetes; 0 indicates no diabetes in source survey.","dataset_sha256":digest,"training_rows":int(len(Xtr)),"test_metrics":metrics,"python_version":platform.python_version(),"scikit_learn_version":sklearn.__version__,"trained_at_utc":datetime.now(UTC).isoformat()}
 temp=artifact.with_suffix(".tmp");joblib.dump({"pipeline":model,"metadata":metadata},temp);temp.replace(artifact)
 metadata["artifact_sha256"]=hashlib.sha256(artifact.read_bytes()).hexdigest();artifact.with_suffix(".metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
 print(json.dumps({"artifact":str(artifact),"metadata":metadata},indent=2))
if __name__=="__main__":main()
