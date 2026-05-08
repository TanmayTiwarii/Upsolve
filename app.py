from fastapi import FastAPI, Query
from typing import List
import httpx
import os
import asyncio
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
load_dotenv()

origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GRAPHQL_URL = os.getenv("GRAPHQL_URL", "https://leetcode.com/graphql/")

# globals to be initialized at startup
df_sim = None
df_diff = None
hybrid_recommend = None
recommend_diff = None


async def fetch_question_data(client: httpx.AsyncClient, slug: str) -> int:
    query_question = {
        "operationName": "questionData",
        "variables": {
            "titleSlug": slug
        },
        "query": "query questionData($titleSlug: String!) { question(titleSlug: $titleSlug) { questionId questionFrontendId title titleSlug difficulty topicTags { name slug } } }"
    }
    try:
        resp = await client.post(GRAPHQL_URL, json=query_question)
        if resp.status_code == 200:
            data = resp.json()
            question = data.get("data", {}).get("question")
            if question and question.get("questionFrontendId"):
                return int(question.get("questionFrontendId"))
    except Exception as e:
        print(f"Error fetching data for slug {slug}: {e}")
    return None

async def fetch_recent_problems(username: str) -> List[int]:
    query_recent = {
        "operationName": "recentAcSubmissions",
        "variables": {
            "username": username,
            "limit": 20
        },
        "query": "query recentAcSubmissions($username: String!, $limit: Int!) { recentAcSubmissionList(username: $username, limit: $limit) { id title titleSlug timestamp } }"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(GRAPHQL_URL, json=query_recent)
            if resp.status_code != 200:
                print(f"Failed to fetch recent submissions for {username}")
                return []
            
            data = resp.json()
            submissions = data.get("data", {}).get("recentAcSubmissionList")
            if not submissions:
                return []
            
            # Extract unique titleSlugs
            title_slugs = list(set([sub.get("titleSlug") for sub in submissions if sub.get("titleSlug")]))
            
            # Fetch question data concurrently
            tasks = [fetch_question_data(client, slug) for slug in title_slugs]
            results = await asyncio.gather(*tasks)
            
            # Filter out None and return valid IDs
            return [res for res in results if res is not None]
            
    except httpx.ReadTimeout:
        print(f"Timeout when fetching recent problems for {username}")
        return []
    except Exception as e:
        print(f"Error fetching recent problems for {username}: {e}")
        return []


@app.on_event("startup")
async def load_resources():
    """
    Import heavy modules and load data after FastAPI starts,
    so Render detects the open port quickly.
    """
    global df_sim, df_diff, hybrid_recommend, recommend_diff
    from routes import recommend_similar, recommend_diff as diff_module

    df_sim = recommend_similar.df
    hybrid_recommend = recommend_similar.hybrid_recommend
    df_diff = diff_module.df
    recommend_diff = diff_module.recommend_diff

    print("DEBUG: Resources loaded at startup ✅")


@app.get("/recommend/similar")
async def get_similar(username: str = Query(..., description="LeetCode username")):
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


@app.get("/recommend/diff")
async def get_diff(username: str = Query(..., description="LeetCode username")):
    if not recommend_diff or df_diff is None:
        return {"error": "Resources not ready yet, please try again shortly."}

    last_ids = await fetch_recent_problems(username)
    if not last_ids:
        return {"error": "Could not fetch recent problems or user has no submissions"}

    recs = recommend_diff(df_diff, last_ids, top_k=5)
    return recs[["id", "problem_name", "difficulty", "topics"]].to_dict(orient="records")


@app.get("/health", include_in_schema=False)
@app.head("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}