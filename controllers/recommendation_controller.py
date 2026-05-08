from typing import Dict, Any, List, Union
from controllers.leetcode_controller import fetch_recent_problems

df_sim = None
df_diff = None
hybrid_recommend = None
recommend_diff = None

def load_ml_resources():
    global df_sim, df_diff, hybrid_recommend, recommend_diff
    from services import recommend_similar, recommend_diff as diff_module

    df_sim = recommend_similar.df
    hybrid_recommend = recommend_similar.hybrid_recommend
    df_diff = diff_module.df
    recommend_diff = diff_module.recommend_diff

    print("DEBUG: Resources loaded at startup ✅")

async def get_similar_recommendations(username: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    if not hybrid_recommend or df_sim is None:
        return {"error": "Resources not ready yet, please try again shortly."}

    last_ids = await fetch_recent_problems(username)
    if not last_ids:
        return {"error": "Could not fetch recent problems or user has no submissions"}

    recs = hybrid_recommend(df_sim, last_ids, top_k=5)
    if "similarity" in recs.columns:
        recs["similarity"] = recs["similarity"].round(4)
        return recs[["id", "problem_name", "difficulty", "topics", "similarity"]].to_dict(orient="records")
    return []

async def get_diff_recommendations(username: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    if not recommend_diff or df_diff is None:
        return {"error": "Resources not ready yet, please try again shortly."}

    last_ids = await fetch_recent_problems(username)
    if not last_ids:
        return {"error": "Could not fetch recent problems or user has no submissions"}

    recs = recommend_diff(df_diff, last_ids, top_k=5)
    return recs[["id", "problem_name", "difficulty", "topics"]].to_dict(orient="records")
