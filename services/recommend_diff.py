import pandas as pd
import os

# -----------------------
# Load & preprocess dataset once at startup
# -----------------------
def load_dataset(path):
    df = pd.read_csv(path)
    df.columns = (
        df.columns.str.strip()
                  .str.lower()
                  .str.replace("\n", "_")
                  .str.replace(" ", "_")
    )
    return df

def preprocess_dataset(df):
    df["text_features"] = df["difficulty"].astype(str) + " " + df["topics"].astype(str)
    return df

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(BASE_DIR, "LeetCode Questions.csv")
df = preprocess_dataset(load_dataset(path))

# -----------------------
# Different recommendation (random unseen problems)
# -----------------------
def recommend_diff(df, last_20_ids, top_k=5):
    # Make sure IDs are integers (both df and last_20_ids)
    df = df.copy()
    df["id"] = df["id"].astype(int)
    last_20_ids = [int(x) for x in last_20_ids]

    unseen = df[~df["id"].isin(last_20_ids)]
    if unseen.empty:
        return pd.DataFrame(columns=["id", "problem_name", "difficulty", "topics"])
    
    recs = unseen.sample(n=min(top_k, len(unseen)), random_state=42)
    return recs[["id", "problem_name", "difficulty", "topics"]]