import os
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------
# Load precomputed dataset & embeddings
# -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

df = pd.read_csv(os.path.join(PROJECT_ROOT, "processed.csv"))
embeddings = np.load(os.path.join(PROJECT_ROOT, "embeddings.npy"))

# -----------------------
# Recommendation helpers
# -----------------------
def recommend(df, last_20_ids, top_k=5):
    id_type = df["id"].dtype
    last_20_ids = [id_type.type(x) if hasattr(id_type, 'type') else id_type(x) for x in last_20_ids]
    mask = df["id"].isin(last_20_ids).values
    last_vecs = embeddings[mask]

    if last_vecs.size == 0 or embeddings.size == 0:
        return df.head(0)
    if last_vecs.ndim != 2 or embeddings.ndim != 2:
        return df.head(0)

    sim_scores = cosine_similarity(last_vecs, embeddings).mean(axis=0)

    sim_df = df.copy()
    sim_df["similarity"] = sim_scores
    sim_df = sim_df[~sim_df["id"].isin(last_20_ids)]

    return sim_df.sort_values("similarity", ascending=False).head(top_k)

def hybrid_recommend(df, last_20_ids, top_k=5):
    last_20 = df[df["id"].isin(last_20_ids)]
    sim_df = recommend(df, last_20_ids, top_k=len(df))

    counts = last_20["difficulty"].value_counts(normalize=True)
    target_mix = {
        "Easy": counts.get("Easy", 0.3),
        "Medium": counts.get("Medium", 0.4),
        "Hard": counts.get("Hard", 0.3),
    }

    recs = []
    for diff, frac in target_mix.items():
        n_pick = max(1, int(top_k * frac))
        pool = sim_df[sim_df["difficulty"] == diff]
        if len(pool) > 0:
            recs.append(pool.head(n_pick))

    if recs:
        out = pd.concat(recs)
        if len(out) < top_k:
            extra = sim_df[~sim_df["id"].isin(out["id"])].head(top_k - len(out))
            out = pd.concat([out, extra])
        return out.head(top_k)
    else:
        return sim_df.head(top_k)
