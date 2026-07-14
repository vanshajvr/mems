import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"]
)

CP_COLUMN = "Cp (pF)"
RH_COLUMN = "Humidity (%)"
LOSS_COLUMN = "Loss"


@router.post("/run/{dataset_id}", response_model=schemas.Analysis)
def run_analysis(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    filepath = str(dataset.filepath)
    df = pd.read_csv(filepath)

    required_columns = [CP_COLUMN, RH_COLUMN, LOSS_COLUMN]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing expected columns {missing}. Columns present: {list(df.columns)}"
        )

    # Drop instrument warm-up row(s) -- Humidity == 0.0 on the first reading
    df = df[df[RH_COLUMN] != 0.0]
    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="No valid rows remaining after cleaning (all rows had Humidity == 0)"
        )

    mean_cp = float(df[CP_COLUMN].mean())
    std_dev = float(df[CP_COLUMN].std())
    mean_loss = float(df[LOSS_COLUMN].mean())
    correlation = float(df[CP_COLUMN].corr(df[RH_COLUMN]))
    expanded_u = std_dev * 2  # k=2 coverage factor -- adjust if your real formula differs

    existing = db.query(models.Analysis).filter(models.Analysis.dataset_id == dataset_id).first()
    if existing:
        existing.mean_cp = mean_cp          # type: ignore
        existing.std_dev = std_dev          # type: ignore
        existing.mean_loss = mean_loss      # type: ignore
        existing.correlation = correlation  # type: ignore
        existing.expanded_u = expanded_u    # type: ignore
        db.commit()
        db.refresh(existing)
        return existing

    db_analysis = models.Analysis(
        dataset_id=dataset_id,
        mean_cp=mean_cp,
        std_dev=std_dev,
        mean_loss=mean_loss,
        correlation=correlation,
        expanded_u=expanded_u
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


@router.get("/{dataset_id}", response_model=schemas.Analysis)
def get_analysis(dataset_id: int, db: Session = Depends(get_db)):
    analysis = db.query(models.Analysis).filter(models.Analysis.dataset_id == dataset_id).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="No analysis found for this dataset")
    return analysis


@router.get("", response_model=list[schemas.Analysis])
def list_analyses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Analysis).offset(skip).limit(limit).all()