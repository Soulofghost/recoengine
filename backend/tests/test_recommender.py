import numpy as np
import pytest
from app.engine.recommender import (
    compute_content_feature_vector,
    vector_to_bytes,
    bytes_to_vector,
    cosine_similarity,
    generate_recommendations,
    FEATURE_DIM
)

def test_feature_vector_properties():
    vec = compute_content_feature_vector(
        title="Deep Reinforcement Learning in Robotics",
        category="Artificial Intelligence",
        tags="robotics, rl, neural-networks, control",
        description="Comprehensive guide to policy gradients and Q-learning in robotic manipulators."
    )
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (FEATURE_DIM,)
    assert vec.dtype == np.float32

    # L2 Norm should be ~ 1.0
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-4

def test_cold_start_fallback():
    # When user has 0 interactions, recommend popular items
    items = [
        {"id": "item1", "title": "AI Course", "category": "AI", "description": "Intro", "tags": "ai", "price": 49.0, "avg_rating": 4.9, "feature_vector_blob": vector_to_bytes(compute_content_feature_vector("AI", "AI", "ai", "desc"))},
        {"id": "item2", "title": "Cloud Course", "category": "Cloud", "description": "Intro", "tags": "cloud", "price": 39.0, "avg_rating": 4.6, "feature_vector_blob": vector_to_bytes(compute_content_feature_vector("Cloud", "Cloud", "cloud", "desc"))}
    ]
    recs = generate_recommendations("new_user_cold", [], items, top_k=2)
    assert len(recs) == 2
    assert recs[0]["strategy"] == "COLD_START_POPULARITY"
    assert recs[0]["item_id"] == "item1"  # Higher rating 4.9

def test_content_and_collaborative_personalization():
    it1_vec = compute_content_feature_vector("Python Deep Learning", "AI", "python, ml, dl", "desc")
    it2_vec = compute_content_feature_vector("PyTorch Computer Vision", "AI", "pytorch, vision, dl", "desc")
    it3_vec = compute_content_feature_vector("Terraform AWS DevOps", "DevOps", "aws, terraform", "desc")

    items = [
        {"id": "it1", "title": "Python Deep Learning", "category": "AI", "description": "desc", "tags": "ml", "price": 50.0, "avg_rating": 4.8, "feature_vector_blob": vector_to_bytes(it1_vec)},
        {"id": "it2", "title": "PyTorch Computer Vision", "category": "AI", "description": "desc", "tags": "ml", "price": 60.0, "avg_rating": 4.7, "feature_vector_blob": vector_to_bytes(it2_vec)},
        {"id": "it3", "title": "Terraform AWS DevOps", "category": "DevOps", "description": "desc", "tags": "devops", "price": 40.0, "avg_rating": 4.5, "feature_vector_blob": vector_to_bytes(it3_vec)}
    ]

    # Alvin purchased it1 (AI). Peer users also purchased it1 and it2 together.
    interactions = [
        {"user_id": "alvin", "item_id": "it1", "weight": 5.0},
        {"user_id": "peer1", "item_id": "it1", "weight": 5.0},
        {"user_id": "peer1", "item_id": "it2", "weight": 5.0},
        {"user_id": "peer2", "item_id": "it3", "weight": 5.0}
    ]

    recs = generate_recommendations("alvin", interactions, items, strategy="HYBRID", top_k=2)
    assert len(recs) >= 1
    # it2 (PyTorch Computer Vision) must rank highest because it shares category AI and peer co-purchase
    assert recs[0]["item_id"] == "it2"
    assert "explanation" in recs[0]
