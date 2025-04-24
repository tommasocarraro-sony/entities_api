from rapidfuzz import process


# 🎯 Step 2: Fuzzy match function
def correct_actor_name(input_name, candidates, threshold=90):
    """
    Returns the best fuzzy match if above threshold; otherwise returns None.
    """
    match, score, _ = process.extractOne(input_name, candidates)
    if score >= threshold:
        return match
    return None


import pandas as pd
import ast


def extract_unique_actor_names(csv_path):
    df = pd.read_csv(csv_path, sep='\t')

    all_actors = set()

    for row in df['actors_list'].dropna():
        try:
            # Convert string to list safely
            actor_list = ast.literal_eval(row)
            all_actors.update(actor.strip() for actor in actor_list)
        except Exception as e:
            print(f"Error parsing row: {row}\n{e}")

    return sorted(all_actors)


# 🧪 Example usage
csv_path = './data/recsys/ml-100k/final_ml-100k.csv'
actor_names = extract_unique_actor_names(csv_path)


# 🧪 Step 3: Demo
for user_input in ["Tom Cruize", "Leonardo DiKaprio", "Morgan Freemn", "Scarlett Johanson", "Chris Hemswarth"]:
    corrected = correct_actor_name(user_input, actor_names)
    print(f"Input: {user_input} → Match: {corrected}")
