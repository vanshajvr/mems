from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/experiments",
    tags=["experiments"]
)


@router.post("", response_model=schemas.Experiment)
def create_experiment(experiment: schemas.ExperimentCreate, db: Session = Depends(get_db)):
    # Before creating the experiment, confirm the project it claims to
    # belong to actually exists. The database-level ForeignKey would
    # eventually catch this too, but it would surface as an ugly
    # IntegrityError instead of a clean 404 -- checking here lets us
    # fail with a proper, intentional HTTP error message.
    project = db.query(models.Project).filter(models.Project.id == experiment.project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    db_experiment = models.Experiment(**experiment.model_dump())
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment


@router.get("", response_model=list[schemas.Experiment])
def list_experiments(db: Session = Depends(get_db)):
    return db.query(models.Experiment).all()


# A second, more useful "list" endpoint: give me only the experiments
# belonging to ONE project. This is where relationship() earns its
# keep -- instead of a manual filter query, you could also write
# `project.experiments` once you've fetched the project object.
@router.get("/by-project/{project_id}", response_model=list[schemas.Experiment])
def list_experiments_for_project(project_id: int, db: Session = Depends(get_db)):
    return db.query(models.Experiment).filter(models.Experiment.project_id == project_id).all()


@router.get("/{experiment_id}", response_model=schemas.Experiment)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    experiment = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@router.put("/{experiment_id}", response_model=schemas.Experiment)
def update_experiment(experiment_id: int, updated: schemas.ExperimentBase, db: Session = Depends(get_db)):
    experiment = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    # Notice: we use ExperimentBase here, not ExperimentCreate --
    # deliberately, you don't want to allow re-parenting an experiment
    # to a different project through a plain update. project_id stays fixed.
    experiment.title = updated.title  # type: ignore
    experiment.instrument = updated.instrument  # type: ignore
    experiment.freq = updated.freq  # type: ignore
    experiment.voltage = updated.voltage  # type: ignore
    experiment.notes = updated.notes  # type: ignore
    db.commit()
    db.refresh(experiment)
    return experiment


@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: int, db: Session = Depends(get_db)):
    experiment = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    db.delete(experiment)
    db.commit()
    return {"detail": f"Experiment {experiment_id} deleted"}