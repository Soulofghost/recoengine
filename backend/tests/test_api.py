import os
import pytest
from fastapi.testclient import TestClient

TEST_DB = "file:recoengine_test?mode=memory&cache=shared"
os.environ["RECOENGINE_DB_PATH"] = TEST_DB

from app.database import init_db, get_db_connection
from app.main import app

client = TestClient(app)

holding_conn = None

@pytest.fixture(scope="session", autouse=True)
def setup_database_session():
    global holding_conn
    holding_conn = init_db(TEST_DB)
    yield
    if holding_conn:
        holding_conn.close()

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert res.json()["service"] == "RecoEngine"

def test_catalog_interaction_and_recommendation_flow():
    # 1. Create items
    items_data = [
        {"title": "Distributed Systems with Go", "category": "Cloud Architecture", "description": "Raft, consensus, and RPCs in Go.", "tags": "go, cloud, raft", "price": 49.99, "avg_rating": 4.9},
        {"title": "Kubernetes in Production", "category": "Cloud Architecture", "description": "Clustering, ingress, and autoscaling.", "tags": "k8s, cloud, containers", "price": 59.99, "avg_rating": 4.8},
        {"title": "Deep Learning with PyTorch", "category": "Machine Learning", "description": "Transformers, CNNs, and backprop.", "tags": "ai, pytorch, dl", "price": 54.99, "avg_rating": 4.7},
        {"title": "Automated Market Making in DeFi", "category": "FinTech", "description": "Liquidity pools, slippage, and AMMs.", "tags": "crypto, defi, finance", "price": 64.99, "avg_rating": 4.6}
    ]

    created_ids = {}
    for item in items_data:
        res = client.post("/api/items", json=item)
        assert res.status_code == 201
        created_ids[item["title"]] = res.json()["id"]

    # 2. Verify List Items
    list_res = client.get("/api/items?category=Cloud Architecture")
    assert list_res.status_code == 200
    cloud_items = list_res.json()
    assert len(cloud_items) == 2

    # 3. Test Cold Start Recommendation
    cold_res = client.get("/api/recommendations/new_user_123")
    assert cold_res.status_code == 200
    cold_data = cold_res.json()
    assert len(cold_data["recommendations"]) >= 3
    assert cold_data["recommendations"][0]["strategy"] == "COLD_START_POPULARITY"

    # 4. Log User Interactions
    # Alvin purchases "Distributed Systems with Go" and bookmarks "Kubernetes in Production"
    inter1 = client.post("/api/interactions", json={
        "user_id": "alvin_dev",
        "item_id": created_ids["Distributed Systems with Go"],
        "interaction_type": "PURCHASE"
    })
    assert inter1.status_code == 201

    inter2 = client.post("/api/interactions", json={
        "user_id": "alvin_dev",
        "item_id": created_ids["Kubernetes in Production"],
        "interaction_type": "BOOKMARK"
    })
    assert inter2.status_code == 201

    # Peer user Sophia also purchases "Distributed Systems with Go" and "Kubernetes in Production"
    client.post("/api/interactions", json={
        "user_id": "sophia_peer",
        "item_id": created_ids["Distributed Systems with Go"],
        "interaction_type": "PURCHASE"
    })
    client.post("/api/interactions", json={
        "user_id": "sophia_peer",
        "item_id": created_ids["Deep Learning with PyTorch"],
        "interaction_type": "PURCHASE"
    })

    # 5. Fetch Personalized Hybrid Recommendations for Alvin
    reco_res = client.get("/api/recommendations/alvin_dev?strategy=HYBRID&beta=0.6&top_k=3")
    assert reco_res.status_code == 200
    reco_data = reco_res.json()
    assert reco_data["user_id"] == "alvin_dev"
    assert len(reco_data["recommendations"]) >= 1

    # 6. Verify Analytics Metrics
    metrics_res = client.get("/api/analytics/reco-metrics")
    assert metrics_res.status_code == 200
    m = metrics_res.json()
    assert m["total_items"] == 4
    assert m["total_users"] >= 2
    assert m["total_interactions"] >= 4
    assert "Cloud Architecture" in m["category_distribution"]
