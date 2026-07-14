import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"]
)

UPLOAD_DIR = "uploaded_datasets"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=schemas.Dataset)
def upload_dataset(
    exp_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    experiment = db.query(models.Experiment).filter(models.Experiment.id == exp_id).first()
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    filename: str = file.filename

    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_dataset = models.Dataset(
        exp_id=exp_id,
        filename=filename,
        filepath=save_path
    )
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset


@router.get("", response_model=list[schemas.Dataset])
def list_datasets(db: Session = Depends(get_db)):
    return db.query(models.Dataset).all()


@router.get("/by-experiment/{exp_id}", response_model=list[schemas.Dataset])
def list_datasets_for_experiment(exp_id: int, db: Session = Depends(get_db)):
    return db.query(models.Dataset).filter(models.Dataset.exp_id == exp_id).all()


@router.get("/{dataset_id}", response_model=schemas.Dataset)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    filepath = str(dataset.filepath)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.delete(dataset)
    db.commit()
    return {"detail": f"Dataset {dataset_id} deleted"}