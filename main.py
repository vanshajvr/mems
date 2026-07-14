from fastapi import FastAPI

from database import engine, Base
from routers import projects, experiments, datasets, analysis

# Creates all tables defined in models.py if they don't already exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MEMS - Metrology Experiment Management System",
    description="Backend for managing projects, experiments, datasets, and analysis for impedance metrology data",
    version="0.1.0"
)

app.include_router(projects.router)
app.include_router(experiments.router)
app.include_router(datasets.router)
app.include_router(analysis.router)


@app.get("/")
def root():
    return {"status": "MEMS API running"}