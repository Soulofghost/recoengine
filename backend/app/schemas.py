from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ItemCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    category: str = Field(..., min_length=2, max_length=80)
    description: str = Field(..., min_length=10)
    tags: str = Field(..., min_length=2)
    price: Optional[float] = 0.0
    avg_rating: Optional[float] = 4.5

class ItemOut(ItemCreate):
    id: str
    created_at: str

class InteractionCreate(BaseModel):
    user_id: str = Field(..., min_length=2, max_length=64)
    item_id: str = Field(..., min_length=2, max_length=64)
    interaction_type: str = Field(..., pattern=r'^(VIEW|BOOKMARK|RATING|PURCHASE)$')

class InteractionOut(InteractionCreate):
    id: str
    weight: float
    timestamp_epoch: float
    created_at: str

class RecommendationItemOut(BaseModel):
    item_id: str
    title: str
    category: str
    description: str
    price: float
    avg_rating: float
    score: float
    strategy: str
    explanation: str

class RecommendationResponse(BaseModel):
    user_id: str
    strategy: str
    beta: float
    top_k: int
    latency_ms: float
    recommendations: List[RecommendationItemOut]

class RecoMetricsOut(BaseModel):
    total_items: int
    total_users: int
    total_interactions: int
    avg_latency_ms: float
    category_distribution: Dict[str, int]
