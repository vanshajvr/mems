from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Project Schemas
class ProjectBase(BaseModel):
## base schema for project, used for both creation and retrieval
    name: str
    desc: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass
    ## inherits from ProjectBase

class Project(ProjectBase):
    id: int
    created_at: datetime
    ## inherits from ProjectBase and adds id and created_at fields
 
    class Config:
        from_attributes=True
        ### allows Pydantic to read data from ORM models
        ### to convert SQLAlchemy models to Pydantic models for output responses

# Experiment Schemas
class ExperimentBase(BaseModel):
    title: str
    instrument: Optional[str] = None
    freq: Optional[float] = None
    voltage: Optional[float] = None
    notes: Optional[str] = None
    ### optional fields if any, can be left empty if not provided

class ExperimentCreate(ExperimentBase):
    project_id: int
    ### project_id is required here, unlike the DB-generated fields
    ### client has to tell us which project this experiment belongs to.

class Experiment(ExperimentBase):
    id: int
    project_id: int
    created_at: datetime
 
    class Config:
        from_attributes = True

# Dataset Schemas
class DatasetBase(BaseModel):
    filename: str
    filepath: str
 
 
class DatasetCreate(DatasetBase):
    experiment_id: int
 
 
class Dataset(DatasetBase):
    id: int
    experiment_id: int
    uploaded_at: datetime
 
    class Config:
        from_attributes = True

# Analysis Schemas
class AnalysisBase(BaseModel):
    mean_cp: Optional[float] = None
    std_cp: Optional[float] = None
    correlation: Optional[float] = None
    expanded_u: Optional[float] = None
 
class AnalysisCreate(AnalysisBase):
    dataset_id: int
 
 
class Analysis(AnalysisBase):
    id: int
    dataset_id: int
    created_at: datetime
 
    class Config:
        from_attributes = True
 