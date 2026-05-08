from typing import List
import httpx
import os
import asyncio

GRAPHQL_URL = os.getenv("GRAPHQL_URL", "https://leetcode.com/graphql/")

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
