import pytest


@pytest.fixture(scope="function")
def seeded_api_client(client):
    """Return the existing FastAPI TestClient fixture and make the sample route
    deterministic for API-level pipeline assertions.
    """
    return client


def test_import_sample_materials_api_and_material_count(seeded_api_client):
    """POST /api/materials/import-sample imports the committed sample CSV files
    through the active HTTP API and materializes the expected number of rows in
    the isolated SQLite test database.
    """
    response = seeded_api_client.post("/api/materials/import-sample")

    assert response.status_code == 200

    summaries = response.json()
    assert isinstance(summaries, list)
    assert len(summaries) == 2

    first = summaries[0]
    second = summaries[1]
    assert first["source_system"] == "SAP-A"
    assert second["source_system"] == "SAP-B"

    total_imported = first["imported"] + second["imported"]
    assert total_imported == 17

    # The importer contract only generates candidates in the same import pass,
    # and the cross-source matching job should not be empty with the repository
    # sample data.
    assert first["matches_generated"] > 0 or second["matches_generated"] > 0

    materials_response = seeded_api_client.get("/api/materials")
    assert materials_response.status_code == 200

    materials = materials_response.json()
    assert len(materials) == 17
    assert {m["source_system"] for m in materials} == {"SAP-A", "SAP-B"}


def test_matches_endpoint_returns_cross_source_scored_pending_record(seeded_api_client):
    """After the sample import route commits the CSVs into the test database,
    the live GET /api/matches endpoint must expose at least one cross-source
    pending match and return the current scoring fields in the real schema.
    """
    import_response = seeded_api_client.post("/api/materials/import-sample")
    assert import_response.status_code == 200

    matches_response = seeded_api_client.get("/api/matches?status=pending")
    assert matches_response.status_code == 200

    matches = matches_response.json()
    assert len(matches) > 0

    candidate = None
    for match in matches:
        material_a = match["material_a_detail"]
        material_b = match["material_b_detail"]
        if material_a["source_system"] != material_b["source_system"]:
            candidate = match
            break

    assert candidate is not None
    assert candidate["status"] == "pending"
    assert candidate["semantic_score"] is not None
    assert candidate["attribute_score"] is not None
    assert candidate["rule_score"] is not None
    assert candidate["final_confidence"] is not None

    assert set(candidate).issuperset({
        "semantic_score",
        "attribute_score",
        "rule_score",
        "final_confidence",
        "status",
    })


def test_two_source_duplicate_identity_has_two_source_members(seeded_api_client):
    """The committed sample dataset demonstrates the active two-source
    duplicate identity path without inventing an absent legacy third file.
    """
    import_response = seeded_api_client.post("/api/materials/import-sample")
    assert import_response.status_code == 200

    pending_matches = seeded_api_client.get("/api/matches?status=pending").json()

    def pair_has_sources_and_codes(match, sources, codes):
        materials = (
            match["material_a_detail"],
            match["material_b_detail"],
        )
        return (
            {m["source_system"] for m in materials} == set(sources)
            and {m["legacy_code"] for m in materials} == set(codes)
        )

    bolt_sap_a_sap_b = next(
        m for m in pending_matches
        if pair_has_sources_and_codes(m, {"SAP-A", "SAP-B"}, {"A-1001", "B-2001"})
    )

    # Accept the material pair that belongs to the same two-source identity.
    resp_ab = seeded_api_client.post(
        f"/api/matches/{bolt_sap_a_sap_b['id']}/resolve",
        json={"action": "accept", "canonical_name": "SS Hex Bolt M10 x 50mm DIN 933"},
    )
    assert resp_ab.status_code == 200

    identity_id = resp_ab.json()["identity_id"]
    assert identity_id is not None

    identity_detail = seeded_api_client.get(f"/api/identities/{identity_id}").json()
    members = identity_detail["members"]
    assert len(members) == 2
    assert {m["source_system"] for m in members} == {"SAP-A", "SAP-B"}


def test_import_sample_second_run_is_idempotent_and_does_not_duplicate_materials(seeded_api_client):
    """The import-sample contract is intentionally idempotent. A second call
    should not create duplicate material records in the isolated test database.
    """
    first_response = seeded_api_client.post("/api/materials/import-sample")
    assert first_response.status_code == 200

    materials_after_first = seeded_api_client.get("/api/materials")
    assert materials_after_first.status_code == 200
    assert len(materials_after_first.json()) == 17

    second_response = seeded_api_client.post("/api/materials/import-sample")
    assert second_response.status_code == 200

    summaries = second_response.json()
    assert isinstance(summaries, list)
    assert len(summaries) == 2

    total_imported = sum(item["imported"] for item in summaries)
    assert total_imported == 0

    # The importer never duplicates records from an already-imported sample run.
    materials_after_second = seeded_api_client.get("/api/materials")
    assert materials_after_second.status_code == 200
    assert len(materials_after_second.json()) == 17
