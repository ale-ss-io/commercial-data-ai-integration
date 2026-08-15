def test_requires_api_key(client):
    resp = client.get("/customers")
    assert resp.status_code == 401


def test_rejects_wrong_api_key(client):
    resp = client.get(
        "/customers",
        headers={"X-API-Key": "wrong"}
    )
    assert resp.status_code == 401


def test_list_customers(client, auth_headers):
    resp = client.get(
        "/customers",
        headers=auth_headers
    )

    assert resp.status_code == 200
    assert resp.json()[0]["customer_id"] == "C1"


def test_get_customer_404(client, auth_headers):
    resp = client.get(
        "/customers/DOES_NOT_EXIST",
        headers=auth_headers
    )

    assert resp.status_code == 404


def test_customer_summary_marks_high_risk(client, auth_headers):
    resp = client.get(
        "/customers/C1/summary",
        headers=auth_headers
    )

    assert resp.status_code == 200

    body = resp.json()

    assert body["risk_level"] == "HIGH"
    assert body["overdue_invoices"] == 1
    assert body["outstanding_balance"] == 150000.0


def test_customers_at_risk_includes_c1(client, auth_headers):
    resp = client.get(
        "/customers/at-risk",
        headers=auth_headers
    )

    assert resp.status_code == 200

    ids = [
        customer["customer_id"]
        for customer in resp.json()
    ]

    assert "C1" in ids


def test_health_no_auth_needed(client):
    resp = client.get("/health")

    assert resp.status_code == 200