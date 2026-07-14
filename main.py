from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
 
import models
import schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine) 
## create all tables in the database if they don't exist

app = FastAPI(title="MEMS - Metrology Experiment Management System")
## create a FastAPI app instance with a title

@app.post("/projects", response_model=schemas.Project)
## define a POST endpoint to create a new project

def create_project(project: schemas.ProjectCreate, db: Session=Depends(get_db)):
    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects", response_model=list[schemas.Project])
## define a GET endpoint to list all projects

def list_projects(db: Session=Depends(get_db)):
    return db.query(models.Project).all()

@app.get("/projects/{project_id}", response_model=schemas.Project)
### define a GET endpoint to get a specific project by its ID

def get_project(project_id: int, db: Session=Depends(get_db)):
    project=db.query(models.Project).filter(models.Project.id==project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
## get a specific project by its ID, return 404 if not found

@app.put("/projects/{project_id}", response_model=schemas.Project)
## define a PUT endpoint to update a specific project by its ID

def update_project(project_id: int, updated: schemas.ProjectCreate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = updated.name
    project.desc = updated.desc
    db.commit()
    db.refresh(project)
    return project
## update a specific project by its ID, return 404 if not found

@app.delete("/projects/{project_id}", response_model=schemas.Project)
## define a DELETE endpoint to delete a specific project by its ID

def delete_project(project_id:int, db:Session=Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return project
## delete a specific project by its ID, return 404 if not found