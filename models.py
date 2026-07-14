from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Project(Base):
    __tablename__="projects"

    id=Column(Integer, primary_key=True, index=True)
    ## acts as a unique identifier for each project
    ## it is indexed to allow for faster lookups

    name=Column(String, nullable=False) 
    ## important to set nullable=False for name, as it is a required field

    desc=Column(String, nullable=True)
    ## desc is optional, so nullable=True

    created_at=Column(DateTime(timezone=True), server_default=func.now())
    ## automatically set the field to the current project creation time

    experiments=relationship("Experiment", back_populates="project")
    ## establishes relationship with experiment model
    ## it allows to access experiments associate with a project

class Experiment(Base):
    __tablename__="experiments"

    id=Column(Integer, primary_key=True, index=True)
    project_id=Column(Integer, ForeignKey("projects.id"), nullable=False)
    ## establishes a foreign key relationship with the projects table

    title = Column(String, nullable=False)
    instrument = Column(String, nullable=True)
    freq = Column(Float, nullable=True)
    voltage = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="experiments")
    ## establishes relationship with project model

    datasets = relationship("Dataset", back_populates="experiment")
    ## establishes relationship with dataset model

class Dataset(Base):
    __tablename__="datasets"

    id=Column(Integer, primary_key=True, index=True)
    experiment_id=Column(Integer, ForeignKey("exeriments.id"),nullable=False)

    filename=Column(String, nullable=False)
    filepath = Column(String, nullable=False) ## actual location of file on disk
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    experiment = relationship("Experiment", back_populates="datasets")
    ## establishes relationship with experiment model

    analysis = relationship("Analysis", back_populates="dataset", uselist=False)
    ## establishes relationship with analysis model

class Analysis(Base):
    __tablename__="analysis"

    id=Column(Integer, primary_key=True, index= True)
    dataset_id=Column(Integer, ForeignKey("datasets.id"), nullable=False)
    mean_cp=Column(Float, nullable=False)
    std_dev=Column(Float, nullable=False)
    mean_loss=Column(Float, nullable=False)
    correlation=Column(Float, nullable=False)
    expanded_u=Column(Float, nullable=False) ## expanded uncertainty (GUM-style)
    created_at=Column(DateTime(timezone=True), server_default=func.now())

    dataset=relationship("Dataset", back_populates="analysis")
    ## establishes relationship with dataset model
