import math
import re
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

FEATURE_DIM = 64

INTERACTION_WEIGHTS = {
    "VIEW": 1.0,
    "BOOKMARK": 2.5,
    "RATING": 3.5,
    "PURCHASE": 5.0
}

def hash_term(term: str, seed: int = 0) -> int:
    h = 2166136261 ^ seed
    for ch in term:
        h = ((h * 16777619) ^ ord(ch)) & 0xFFFFFFFF
    return h

def compute_content_feature_vector(title: str, category: str, tags: str, description: str) -> np.ndarray:
    """
    Computes a 64-dimensional normalized dense feature vector capturing item semantics.
    """
    vec = np.zeros(FEATURE_DIM, dtype=np.float32)

    # 1. Category emphasis (highest weight)
    clean_cat = category.lower().strip()
    h_cat = hash_term(clean_cat) % FEATURE_DIM
    vec[h_cat] += 3.0

    # 2. Tags emphasis
    tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
    for t in tag_list:
        h_t = hash_term(t, 19) % FEATURE_DIM
        vec[h_t] += 2.0

    # 3. Title & Description tokens
    words = re.findall(r'\b[a-z0-9_-]+\b', f"{title} {description}".lower())
    for w in words:
        hw = hash_term(w, 37) % FEATURE_DIM
        sign = 1.0 if (hash_term(w, 7) % 2 == 0) else -1.0
        vec[hw] += sign * 0.8

    norm = np.linalg.norm(vec)
    if norm > 1e-5:
        vec /= norm
    return vec

def vector_to_bytes(v: np.ndarray) -> bytes:
    return v.astype(np.float32).tobytes()

def bytes_to_vector(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = float(np.dot(v1, v2))
    return max(0.0, min(1.0, (dot + 1.0) / 2.0))

def compute_collaborative_scores(
    target_user_id: str,
    all_interactions: List[Dict[str, Any]],
    candidate_item_ids: set
) -> Tuple[Dict[str, float], Dict[str, str]]:
    """
    Item-item collaborative filtering using user co-interaction matrices.
    """
    # 1. Group interactions by user
    user_items: Dict[str, Dict[str, float]] = {}
    for inter in all_interactions:
        u = inter["user_id"]
        i = inter["item_id"]
        w = float(inter["weight"])
        if u not in user_items:
            user_items[u] = {}
        user_items[u][i] = max(user_items[u].get(i, 0.0), w)

    target_profile = user_items.get(target_user_id, {})
    if not target_profile:
        return {}, {}

    # 2. Build item co-occurrence counts across other users
    item_cooccur: Dict[str, Dict[str, float]] = {}
    for u, items in user_items.items():
        if u == target_user_id:
            continue
        item_keys = list(items.keys())
        for i1 in item_keys:
            if i1 not in item_cooccur:
                item_cooccur[i1] = {}
            for i2 in item_keys:
                if i1 == i2:
                    continue
                item_cooccur[i1][i2] = item_cooccur[i1].get(i2, 0.0) + 1.0

    collab_scores: Dict[str, float] = {}
    collab_reasons: Dict[str, str] = {}

    for target_item, user_weight in target_profile.items():
        if target_item in item_cooccur:
            for related_item, co_count in item_cooccur[target_item].items():
                if related_item in candidate_item_ids:
                    add_score = user_weight * co_count
                    collab_scores[related_item] = collab_scores.get(related_item, 0.0) + add_score
                    if related_item not in collab_reasons:
                        collab_reasons[related_item] = f"Users who interacted with your items also engaged with this"

    # Normalize collaborative scores to [0, 1]
    max_c = max(collab_scores.values()) if collab_scores else 0.0
    if max_c > 0:
        for k in collab_scores:
            collab_scores[k] = round(collab_scores[k] / max_c, 4)

    return collab_scores, collab_reasons

def compute_content_scores(
    target_user_id: str,
    user_interactions: List[Dict[str, Any]],
    items_dict: Dict[str, Dict[str, Any]],
    candidate_item_ids: set
) -> Tuple[Dict[str, float], Dict[str, str]]:
    """
    Computes taste profile centroid and cosine similarity to catalog items.
    """
    if not user_interactions:
        return {}, {}

    centroid = np.zeros(FEATURE_DIM, dtype=np.float32)
    total_w = 0.0

    last_item_title = ""
    for inter in user_interactions:
        i_id = inter["item_id"]
        w = float(inter["weight"])
        if i_id in items_dict:
            vec = bytes_to_vector(items_dict[i_id]["feature_vector_blob"])
            centroid += vec * w
            total_w += w
            last_item_title = items_dict[i_id]["title"]

    if total_w > 0:
        norm = np.linalg.norm(centroid)
        if norm > 1e-5:
            centroid /= norm

    content_scores = {}
    content_reasons = {}

    for c_id in candidate_item_ids:
        c_item = items_dict[c_id]
        c_vec = bytes_to_vector(c_item["feature_vector_blob"])
        sim = cosine_similarity(centroid, c_vec)
        content_scores[c_id] = round(sim, 4)
        content_reasons[c_id] = f"Matches your interest profile in {c_item['category']}"

    return content_scores, content_reasons

def generate_recommendations(
    target_user_id: str,
    all_interactions: List[Dict[str, Any]],
    items: List[Dict[str, Any]],
    strategy: str = "HYBRID",
    beta: float = 0.6,
    top_k: int = 6
) -> List[Dict[str, Any]]:
    items_dict = {item["id"]: item for item in items}
    user_interactions = [i for i in all_interactions if i["user_id"] == target_user_id]
    interacted_item_ids = {i["item_id"] for i in user_interactions}

    candidate_ids = set(items_dict.keys()) - interacted_item_ids
    if not candidate_ids:
        # If user interacted with everything, recommend from full catalog
        candidate_ids = set(items_dict.keys())

    # Cold-Start Detection
    if len(user_interactions) == 0:
        # Return top-rated / trending items
        sorted_by_rating = sorted(
            [items_dict[cid] for cid in candidate_ids],
            key=lambda x: (x.get("avg_rating", 4.0), x.get("price", 0.0)),
            reverse=True
        )
        results = []
        for it in sorted_by_rating[:top_k]:
            results.append({
                "item_id": it["id"],
                "title": it["title"],
                "category": it["category"],
                "description": it["description"],
                "price": it["price"],
                "avg_rating": it["avg_rating"],
                "score": 0.85,
                "strategy": "COLD_START_POPULARITY",
                "explanation": f"Top-rated introductory selection in {it['category']}"
            })
        return results

    collab_scores, collab_reasons = compute_collaborative_scores(target_user_id, all_interactions, candidate_ids)
    content_scores, content_reasons = compute_content_scores(target_user_id, user_interactions, items_dict, candidate_ids)

    ranked_items = []
    for cid in candidate_ids:
        it = items_dict[cid]
        c_score = collab_scores.get(cid, 0.0)
        t_score = content_scores.get(cid, 0.5)

        if strategy == "COLLABORATIVE":
            final_score = c_score
            explanation = collab_reasons.get(cid, f"Recommended based on user community behavior")
        elif strategy == "CONTENT_BASED":
            final_score = t_score
            explanation = content_reasons.get(cid, f"Recommended based on content affinity with {it['category']}")
        else: # HYBRID
            # If no collaborative signals yet for this candidate, rely on content score
            effective_beta = beta if c_score > 0 else 0.0
            final_score = (effective_beta * c_score) + ((1.0 - effective_beta) * t_score)
            explanation = collab_reasons.get(cid, content_reasons.get(cid, f"Hybrid recommendation for your profile"))

        ranked_items.append({
            "item_id": it["id"],
            "title": it["title"],
            "category": it["category"],
            "description": it["description"],
            "price": it["price"],
            "avg_rating": it["avg_rating"],
            "score": round(final_score, 4),
            "strategy": strategy,
            "explanation": explanation
        })

    ranked_items.sort(key=lambda x: x["score"], reverse=True)
    return ranked_items[:top_k]
