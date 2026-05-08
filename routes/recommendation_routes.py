from fastapi import APIRouter, Query
from controllers.recommendation_controller import get_similar_recommendations, get_diff_recommendations

router = APIRouter(prefix="/recommend", tags=["recommendations"])

@router.get("/similar")
async def get_similar(username: str = Query(..., description="LeetCode username")):
    return await get_similar_recommendations(username)

@router.get("/diff")
async def get_diff(username: str = Query(..., description="LeetCode username")):
    return await get_diff_recommendations(username)
