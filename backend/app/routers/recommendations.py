import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.database import get_db_connection
from app.schemas import (
    ItemCreate,
    ItemOut,
    InteractionCreate,
    InteractionOut,
    RecommendationResponse,
    RecommendationItemOut,
    RecoMetricsOut
)
from app.engine.recommender import (
    compute_content_feature_vector,
    vector_to_bytes,
    generate_recommendations,
    INTERACTION_WEIGHTS
)

router = APIRouter(prefix="/api", tags=["recommendations"])

@router.post("/items", response_model=ItemOut, status_code=201)
def create_item(payload: ItemCreate):
    conn = get_db_connection()
    item_id = str(uuid.uuid4())
    vec = compute_content_feature_vector(payload.title, payload.category, payload.tags, payload.description)
    blob = vector_to_bytes(vec)

    with conn:
        conn.execute("""
            INSERT INTO items (id, title, category, description, tags, price, avg_rating, feature_vector_blob)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_id, payload.title, payload.category, payload.description, payload.tags, payload.price or 0.0, payload.avg_rating or 4.5, blob))

    row = conn.execute("SELECT id, title, category, description, tags, price, avg_rating, created_at FROM items WHERE id = ?", (item_id,)).fetchone()
    return ItemOut(**dict(row))

@router.get("/items", response_model=List[ItemOut])
def list_items(category: Optional[str] = None):
    conn = get_db_connection()
    sql = "SELECT id, title, category, description, tags, price, avg_rating, created_at FROM items WHERE 1=1"
    params = []
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    return [ItemOut(**dict(r)) for r in rows]

@router.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT id, title, category, description, tags, price, avg_rating, created_at FROM items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemOut(**dict(row))

@router.post("/interactions", response_model=InteractionOut, status_code=201)
def log_interaction(payload: InteractionCreate):
    conn = get_db_connection()
    # Check item exists
    item = conn.execute("SELECT id FROM items WHERE id = ?", (payload.item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=404, detail="Target item not found")

    inter_id = str(uuid.uuid4())
    weight = INTERACTION_WEIGHTS.get(payload.interaction_type, 1.0)
    now = time.time()

    with conn:
        conn.execute("""
            INSERT INTO interactions (id, user_id, item_id, interaction_type, weight, timestamp_epoch)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (inter_id, payload.user_id, payload.item_id, payload.interaction_type, weight, now))

    row = conn.execute("SELECT id, user_id, item_id, interaction_type, weight, timestamp_epoch, created_at FROM interactions WHERE id = ?", (inter_id,)).fetchone()
    return InteractionOut(**dict(row))

@router.get("/recommendations/{user_id}", response_model=RecommendationResponse)
def get_recommendations(
    user_id: str,
    strategy: Optional[str] = Query("HYBRID", pattern="^(HYBRID|COLLABORATIVE|CONTENT_BASED)$"),
    beta: Optional[float] = Query(0.6, ge=0.0, le=1.0),
    top_k: Optional[int] = Query(6, ge=1, le=20)
):
    start = time.perf_counter()
    conn = get_db_connection()

    # Pull all interactions and all items
    interactions_rows = conn.execute("SELECT user_id, item_id, weight FROM interactions").fetchall()
    interactions = [dict(r) for r in interactions_rows]

    items_rows = conn.execute("SELECT id, title, category, description, tags, price, avg_rating, feature_vector_blob FROM items").fetchall()
    items = [dict(r) for r in items_rows]

    if not items:
        return RecommendationResponse(
            user_id=user_id,
            strategy=strategy,
            beta=beta,
            top_k=top_k,
            latency_ms=0.0,
            recommendations=[]
        )

    recs = generate_recommendations(
        target_user_id=user_id,
        all_interactions=interactions,
        items=items,
        strategy=strategy,
        beta=beta,
        top_k=top_k
    )

    latency = round((time.perf_counter() - start) * 1000, 2)

    # Log recommendation event
    with conn:
        conn.execute("""
            INSERT INTO recommendation_logs (id, user_id, strategy, recommended_count, latency_ms)
            VALUES (?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), user_id, strategy, len(recs), latency))

    return RecommendationResponse(
        user_id=user_id,
        strategy=strategy,
        beta=beta,
        top_k=top_k,
        latency_ms=latency,
        recommendations=[RecommendationItemOut(**r) for r in recs]
    )

@router.get("/analytics/reco-metrics", response_model=RecoMetricsOut)
def get_metrics():
    conn = get_db_connection()
    total_items = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    total_users = conn.execute("SELECT COUNT(DISTINCT user_id) FROM interactions").fetchone()[0]
    total_interactions = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
    avg_latency = conn.execute("SELECT AVG(latency_ms) FROM recommendation_logs").fetchone()[0] or 0.0

    cat_rows = conn.execute("SELECT category, COUNT(*) as cnt FROM items GROUP BY category").fetchall()
    cat_distribution = {r["category"]: r["cnt"] for r in cat_rows}

    return RecoMetricsOut(
        total_items=total_items,
        total_users=total_users,
        total_interactions=total_interactions,
        avg_latency_ms=round(avg_latency, 2),
        category_distribution=cat_distribution
    )
