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

# ── Matched to your real AH2700A CSV headers ────────────────────────
CP_COLUMN = "Cp (pF)"
RH_COLUMN = "Humidity (%)"
# ─────────────────────────────────────────────────────────────────────


@router.post("/run/{dataset_id}", response_model=schemas.Analysis)
def run_analysis(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Same logic your AH2700A suite already runs -- just called from
    # an endpoint now instead of a Tkinter button handler.
    filepath = str(dataset.filepath)
    df = pd.read_csv(filepath)

    if CP_COLUMN not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Expected column '{CP_COLUMN}' not found in CSV. Columns present: {list(df.columns)}"
        )

    # Cleaning step: drop the instrument warm-up row(s). On the AH2700A
    # suite's output, the very first observation reads Humidity == 0.0
    # (and Temperature == 0.0) before the sensor has actually settled --
    # not a real measurement. Left in, it skews mean/std and especially
    # the Cp-vs-RH correlation, since RH=0.0 is a genuine outlier.
    rows_before = len(df)
    if RH_COLUMN in df.columns:
        df = df[df[RH_COLUMN] != 0.0]
    rows_dropped = rows_before - len(df)

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="No valid rows remaining after cleaning (all rows had Humidity == 0)"
        )

    mean_cp = float(df[CP_COLUMN].mean())
    std_cp = float(df[CP_COLUMN].std())

    correlation = None
    if RH_COLUMN in df.columns:
        correlation = float(df[CP_COLUMN].corr(df[RH_COLUMN]))

    # Expanded uncertainty, k=2 (~95% confidence) -- standard GUM-style
    # convention. Swap this out if your AH2700A suite already computes
    # expanded_u differently (e.g. combining Type A + Type B terms).
    expanded_u = std_cp * 2

    # If this dataset already has an Analysis row, overwrite it rather
    # than creating a duplicate -- re-running analysis should update
    # the existing result, not pile up multiple rows for one dataset.
    existing = db.query(models.Analysis).filter(models.Analysis.dataset_id == dataset_id).first()
    if existing:
        existing.mean_cp = mean_cp        # type: ignore
        existing.std_cp = std_cp          # type: ignore
        existing.correlation = correlation  # type: ignore
        existing.expanded_u = expanded_u  # type: ignore
        db.commit()
        db.refresh(existing)
        return existing

    db_analysis = models.Analysis(
        dataset_id=dataset_id,
        mean_cp=mean_cp,
        std_cp=std_cp,
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
def list_analyses(db: Session = Depends(get_db)):
    return db.query(models.Analysis).all()