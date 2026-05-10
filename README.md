# ML Backend LeetCode Helper

A Machine Learning-powered REST API built with FastAPI that provides personalized LeetCode problem recommendations based on a user's recent submission history.

## Architecture & Pipeline

The recommendation pipeline ensures high performance and accurate suggestions:

1. **Startup Phase:** 
   - Uses FastAPI's `@app.on_event("startup")` to load preprocessed datasets (`processed.csv`) and their precomputed SentenceTransformer vector embeddings (`embeddings.npy`).
   - Loading on startup instead of globally allows fast port binding for deployment health checks.

2. **Client Request:** 
   - The frontend requests `/recommend/similar` or `/recommend/diff` with the LeetCode username.

3. **Data Fetching (GraphQL):** 
   - The backend uses `httpx` and `asyncio` to interact with the **LeetCode GraphQL API** (`https://leetcode.com/graphql/`).
   - First, it executes a `recentAcSubmissions` GraphQL query to fetch the `titleSlug` of the 20 most recent problems solved by the given username.
   - Next, it fires concurrent `questionData` GraphQL queries for each slug to map them to their corresponding `questionFrontendId`s. Using `asyncio.gather` ensures these multiple network requests are resolved rapidly without blocking the server.

4. **Embedding Preprocessing (Offline):**
   - The dataset of LeetCode problems (`LeetCode Questions.csv`) is preprocessed offline via a dedicated Python script.
   - The text features (specifically, `difficulty` + `topics`, e.g., "Medium Array Hash Table") are concatenated.
   - A lightweight SentenceTransformer model (`paraphrase-MiniLM-L3-v2`) processes these combined strings and encodes them into normalized, high-dimensional dense vectors.
   - These vectors are saved locally as an `embeddings.npy` Numpy array file alongside a cleaned `processed.csv`. This means the API never performs expensive NLP inference during runtime.

5. **Recommendation Engine (Cosine Similarity):**
   - **Similar Problems (`/recommend/similar`):** 
     - The engine retrieves the exact vectors for the user's recently solved `questionFrontendId`s from the `embeddings.npy` file stored in memory.
     - It calculates the mathematical average of these vectors to generate a single **"User Profile Vector"**.
     - It then uses scikit-learn's **Cosine Similarity** metric to measure the angle between the User Profile Vector and every other problem vector in the entire dataset. Scores closer to 1.0 indicate high semantic overlap in topic and difficulty.
     - Finally, it applies a **Hybrid Recommendation Logic** to the sorted list, ensuring that the final recommended problems match the specific difficulty ratio (Easy/Medium/Hard) of the user's recent solves.
   - **Different Problems (`/recommend/diff`):** 
     - Filters out seen problems and provides a randomized sample of fresh, unseen problems for variety.

6. **Response:** 
   - Returns the top 5 customized problem recommendations in JSON format.

## Technology Stack & Decisions

* **FastAPI:** Chosen for its native asynchronous capabilities (`async def`), auto-generated Swagger UI, and high performance compared to Flask/Django.
* **SentenceTransformers (`paraphrase-MiniLM-L3-v2`):** A lightweight BERT-based model used to map categorical features (e.g., "Medium Array Hash Table") into high-dimensional vector embeddings for mathematical similarity calculation without needing expensive GPUs.
* **Precomputed Embeddings:** Generating embeddings on-the-fly is slow. By using a separate script to precalculate and save them as `.npy` arrays, API latency drops from seconds to milliseconds.
* **Asynchronous `httpx`:** Replaces the standard synchronous `requests` library to ensure network calls to external APIs don't block the main event loop.

## Setup Instructions

### Option 1: Local Development (Native Python)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Mac/Linux
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   - Make sure your `.env` file is set up in the `backend` folder.
5. Run the server:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

### Option 2: Docker Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Build and run using Docker Compose:
   ```bash
   docker compose up --build
   ```
3. The API will be available at `http://localhost:8000`.

## Scalability Roadmap

While the current architecture handles the existing 3,000+ LeetCode problems easily, scaling to millions of entries would involve:

* **Vector Databases:** Replacing the in-memory numpy arrays and `O(N)` linear Cosine Similarity check with an Approximate Nearest Neighbor (ANN) search using databases like **Pinecone**, **Milvus**, or the **FAISS** library for `O(log N)` complexity.
* **Database Migration:** Moving from static CSV files loaded via Pandas to a distributed relational database like **PostgreSQL**.
* **Caching Layer:** Implementing **Redis** to cache external API requests and generated recommendations for highly active users.
