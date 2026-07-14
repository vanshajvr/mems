def test_create_project(client):
    r = client.post("/projects", json={"name": "Test Project", "desc": "pytest run"})
    assert r.status_code == 200
    assert r.json()["name"] == "Test Project"
    assert "id" in r.json()


def test_create_project_missing_name_returns_422(client):
    # name is required -- omitting it should fail Pydantic validation,
    # not reach the database at all
    r = client.post("/projects", json={"desc": "no name given"})
    assert r.status_code == 422


def test_get_nonexistent_project_returns_404(client):
    r = client.get("/projects/999999")
    assert r.status_code == 404


def test_create_experiment_with_bad_project_id_returns_404(client):
    r = client.post("/experiments", json={"project_id": 999999, "title": "orphan"})
    assert r.status_code == 404


def test_full_pipeline_project_to_report(client, tmp_path):
    """
    The real end-to-end test: create project -> experiment -> upload a
    real-shaped CSV -> run analysis -> confirm the report shows it all
    correctly nested. This is the same sequence you ran manually in
    /docs, just automated so it can be re-run anytime with one command.
    """
    # 1. Create project
    r = client.post("/projects", json={"name": "Pipeline Test", "desc": "pytest"})
    assert r.status_code == 200
    project_id = r.json()["id"]

    # 2. Create experiment
    r = client.post("/experiments", json={
        "project_id": project_id,
        "title": "10kHz sweep",
        "instrument": "AH2700A",
        "freq": 10000
    })
    assert r.status_code == 200
    experiment_id = r.json()["id"]

    # 3. Build a small CSV with the real AH2700A column shape, matching
    #    your actual measurement_20260706_162551.csv headers
    csv_content = (
        "Observation,Timestamp,Elapsed Time (s),Temperature (\u00b0C),"
        "Humidity (%),Frequency (Hz),Working Voltage (V),Average Count,"
        "Loss Mode,Cp (pF),Loss\n"
        "1,2026-01-01 00:00:00,0.1,0.0,0.0,10000.0,15.0,4,Dissipation (tan\u03b4),0.020911,-0.000506\n"
        "2,2026-01-01 00:00:20,20.1,25.3,53.3,10000.0,15.0,4,Dissipation (tan\u03b4),0.020912,-0.000470\n"
        "3,2026-01-01 00:00:40,40.2,25.4,53.5,10000.0,15.0,4,Dissipation (tan\u03b4),0.020918,-0.000462\n"
        "4,2026-01-01 00:01:00,60.3,25.5,53.8,10000.0,15.0,4,Dissipation (tan\u03b4),0.020925,-0.000455\n"
    )
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(csv_content)

    with open(csv_path, "rb") as f:
        r = client.post(
            "/datasets/upload",
            data={"experiment_id": experiment_id},
            files={"file": ("sample.csv", f, "text/csv")}
        )
    assert r.status_code == 200
    dataset_id = r.json()["id"]

    # 4. Run analysis
    r = client.post(f"/analysis/run/{dataset_id}")
    assert r.status_code == 200
    analysis = r.json()
    assert analysis["mean_cp"] is not None
    assert analysis["std_dev"] is not None

    # 5. Confirm the report shows everything nested correctly
    r = client.get(f"/projects/{project_id}/report")
    assert r.status_code == 200
    report = r.json()
    assert report["id"] == project_id
    assert len(report["experiments"]) == 1
    assert report["experiments"][0]["id"] == experiment_id
    assert len(report["experiments"][0]["datasets"]) == 1
    assert report["experiments"][0]["datasets"][0]["analysis"]["mean_cp"] == analysis["mean_cp"]


def test_upload_rejects_non_csv(client, tmp_path):
    r = client.post("/projects", json={"name": "Reject Test"})
    project_id = r.json()["id"]
    r = client.post("/experiments", json={"project_id": project_id, "title": "exp"})
    experiment_id = r.json()["id"]

    bad_file = tmp_path / "notacsv.txt"
    bad_file.write_text("this is not a csv")

    with open(bad_file, "rb") as f:
        r = client.post(
            "/datasets/upload",
            data={"experiment_id": experiment_id},
            files={"file": ("notacsv.txt", f, "text/plain")}
        )
    assert r.status_code == 400


def test_analysis_on_empty_csv_returns_400_not_500(client, tmp_path):
    # This is the exact edge case you found manually -- now it's
    # permanently guarded against regressing back to a 500 crash.
    r = client.post("/projects", json={"name": "Empty CSV Test"})
    project_id = r.json()["id"]
    r = client.post("/experiments", json={"project_id": project_id, "title": "exp"})
    experiment_id = r.json()["id"]

    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("")

    with open(empty_csv, "rb") as f:
        r = client.post(
            "/datasets/upload",
            data={"experiment_id": experiment_id},
            files={"file": ("empty.csv", f, "text/csv")}
        )
    dataset_id = r.json()["id"]

    r = client.post(f"/analysis/run/{dataset_id}")
    assert r.status_code == 400  # NOT 500