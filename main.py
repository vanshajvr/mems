from fastapi import FastAPI

import models
from database import engine
from routers import projects, experiments

# Creates mems.db and any missing tables. Safe to run every startup.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MEMS - Metrology Experiment Management System")

# Plugs each router's routes into the main app. Because projects.router
# already has prefix="/projects", its routes show up at /projects,
# /projects/{id}, etc. -- exactly as before, just organized by file now.
app.include_router(projects.router)
app.include_router(experiments.router)