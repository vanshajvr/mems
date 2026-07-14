from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router=APIRouter(
    prefix='/projects',
    tags=['projects']
)

@router.post("", response_model=schemas.Project)

def create_project(project:schemas.ProjectCreate, db:Session=Depends(get_db)):
    db_project=models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("", response_model=list[schemas.Project])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Project).offset(skip).limit(limit).all()

@router.get("/{project_id}", response_model=schemas.Project)

def get_project(project_id: int, db: Session=Depends(get_db)):
    project=db.query(models.Project).filter(models.Project.id==project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=schemas.Project)
def update_project(project_id: int, updated: schemas.ProjectCreate, db: Session=Depends(get_db)):
    project=db.query(models.Project).filter(models.Project.id==project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
        project.name = updated.name  # type: ignore
    project.desc = updated.desc  # type: ignore
    db.commit()
    db.refresh(project)
    return project
 
 
@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"detail": f"Project {project_id} deleted"}

@router.get("/{project_id}/report", response_model=schemas.ProjectReport)
def get_project_report(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project