import os
import requests
from dotenv import load_dotenv

# python-dotenv's load_dotenv() walks UP from the current directory
# looking for a .env file -- since gui/ is a subfolder of mems/, this
# finds the SAME .env your backend already uses, without needing a
# second copy inside gui/.
load_dotenv()

# Falls back to localhost if MEMS_API_URL isn't set -- same
# os.getenv(key, default) pattern as database.py's DATABASE_URL.
BASE_URL = os.getenv("MEMS_API_URL", "http://127.0.0.1:8000")


class APIError(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{status_code}: {detail}")
        

def _handle_response(response):
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "Unknown error")
        except Exception:
            detail = response.text
        raise APIError(response.status_code, detail)
    return response.json()


def get_projects(skip=0, limit=100):
    r = requests.get(f"{BASE_URL}/projects", params={"skip": skip, "limit": limit})
    return _handle_response(r)


def create_project(name, desc=None):
    r = requests.post(f"{BASE_URL}/projects", json={"name": name, "desc": desc})
    return _handle_response(r)


def get_experiments_for_project(project_id):
    r = requests.get(f"{BASE_URL}/experiments/by-project/{project_id}")
    return _handle_response(r)


def create_experiment(project_id, title, instrument=None, freq=None, voltage=None, notes=None):
    r = requests.post(f"{BASE_URL}/experiments", json={
        "project_id": project_id,
        "title": title,
        "instrument": instrument,
        "freq": freq,
        "voltage": voltage,
        "notes": notes
    })
    return _handle_response(r)


def upload_dataset(experiment_id, filepath):
    with open(filepath, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/datasets/upload",
            data={"experiment_id": experiment_id},
            files={"file": (filepath.split("/")[-1], f, "text/csv")}
        )
    return _handle_response(r)


def run_analysis(dataset_id):
    r = requests.post(f"{BASE_URL}/analysis/run/{dataset_id}")
    return _handle_response(r)


def get_project_report(project_id):
    r = requests.get(f"{BASE_URL}/projects/{project_id}/report")
    return _handle_response(r)

def get_experiments():
    r = requests.get(f"{BASE_URL}/experiments")
    return _handle_response(r)


def get_datasets():
    r = requests.get(f"{BASE_URL}/datasets")
    return _handle_response(r)


def get_datasets_for_experiment(experiment_id):
    r = requests.get(f"{BASE_URL}/datasets/by-experiment/{experiment_id}")
    return _handle_response(r)

def update_project(project_id, name, desc=None):
    r = requests.put(f"{BASE_URL}/projects/{project_id}", json={"name": name, "desc": desc})
    return _handle_response(r)


def delete_project(project_id):
    r = requests.delete(f"{BASE_URL}/projects/{project_id}")
    return _handle_response(r)


def update_experiment(experiment_id, title, instrument=None, freq=None, voltage=None, notes=None):
    r = requests.put(f"{BASE_URL}/experiments/{experiment_id}", json={
        "title": title, "instrument": instrument, "freq": freq,
        "voltage": voltage, "notes": notes
    })
    return _handle_response(r)


def delete_experiment(experiment_id):
    r = requests.delete(f"{BASE_URL}/experiments/{experiment_id}")
    return _handle_response(r)


def delete_dataset(dataset_id):
    r = requests.delete(f"{BASE_URL}/datasets/{dataset_id}")
    return _handle_response(r)

def delete_analysis(dataset_id):
    r = requests.delete(f"{BASE_URL}/analysis/{dataset_id}")
    return _handle_response(r)