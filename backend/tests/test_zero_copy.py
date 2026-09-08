def test_import_sample_and_generate_candidates(client):
    resp = client.post("/api/materials/import-sample")
    assert resp.status_code == 200
    summaries = resp.json()
    assert len(summaries) == 2
    assert sum(s["imported"] for s in summaries) == 17  # 8 rows (ERP-A) + 9 rows (ERP-B)
    assert sum(s["matches_generated"] for s in summaries) > 0


def test_zero_copy_source_records_never_mutated(client):
    client.post("/api/materials/import-sample")

    before = {m["id"]: m["description"] for m in client.get("/api/materials").json()}

    matches = client.get("/api/matches", params={"status": "pending"}).json()
    assert len(matches) > 0
    for m in matches:
        action = "reject" if m["conflict_reason"] else "accept"
        r = client.post(f"/api/matches/{m['id']}/resolve", json={"action": action})
        assert r.status_code == 200

    after = {m["id"]: m["description"] for m in client.get("/api/materials").json()}
    assert before == after  # not a single source description was touched


def test_conflict_pair_is_flagged_not_auto_merged(client):
    client.post("/api/materials/import-sample")
    matches = client.get("/api/matches", params={"status": "pending"}).json()
    conflicts = [m for m in matches if m["conflict_reason"]]
    assert len(conflicts) >= 1
    # a conflicted pair must never be pre-accepted by the engine itself
    assert all(m["status"] == "pending" for m in conflicts)


def test_accept_creates_identity_and_links_materials(client):
    client.post("/api/materials/import-sample")
    matches = client.get("/api/matches", params={"status": "pending"}).json()
    clean = next(m for m in matches if not m["conflict_reason"])

    resolved = client.post(f"/api/matches/{clean['id']}/resolve", json={"action": "accept"}).json()
    assert resolved["status"] == "accepted"
    assert resolved["identity_id"] is not None

    graph = client.get("/api/graph").json()
    node_ids = {n["id"] for n in graph["nodes"]}
    assert resolved["identity_id"] in node_ids
    assert clean["material_a"] in node_ids
    assert clean["material_b"] in node_ids


def test_reject_does_not_create_identity(client):
    client.post("/api/materials/import-sample")
    matches = client.get("/api/matches", params={"status": "pending"}).json()
    target = matches[0]

    resolved = client.post(f"/api/matches/{target['id']}/resolve", json={"action": "reject"}).json()
    assert resolved["status"] == "rejected"
    assert resolved["identity_id"] is None
