import os


def get_app_store_data():
    try:
        import pandas as pd
        return pd.read_csv('./utils/AppStore_Data.csv')
    except ImportError:
        raise ImportError(
            "pandas is required to use get_app_store_data(). Please install it first.")


def get_embeddings(texts: list[str], model="text-embedding-3-large"):
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        embeddings = client.embeddings.create(input=texts, model=model)
        return [embedding.embedding for embedding in embeddings.data]
    except ImportError:
        raise ImportError(
            "openai is required to use get_embeddings(). Please install it first.")
    except Exception as e:
        raise Exception(f"Error in get_embeddings: {str(e)}")


# Util Functions


def count_tokens(text: str):
    """Count the number of tokens in a string"""
    try:
        from tiktoken import get_encoding
        encoder = get_encoding("cl100k_base")
        return len(encoder.encode(text))
    except ImportError:
        raise ImportError(
            "tiktoken is required to use count_tokens(). Please install it first.")


def row_to_string(row):
    """Convert a row to a string"""
    try:
        app_string = f"""App Name: {row["name"]}
Size: {row["size"]} MB
Price: {row["price"]} {row["currency"]}
Rating Count: {row["rating_count_tot"]}
User Rating: {row["user_rating"]}
Version: {row["ver"]}
Genre: {row["prime_genre"]}
Description: {row["app_desc"]}"""
        return app_string
    except AttributeError:
        raise AttributeError(
            "The row object doesn't have the expected attributes. Make sure you're passing a valid DataFrame row.")


def get_context(tokens: int, df, golden_df=None, shuffle=True):
    """Get the context for a given number of tokens from App Store Data df"""
    try:
        import pandas as pd
        import random

        # 1. If shuffle is true, shuffle the df
        if shuffle:
            df: pd.DataFrame = df.sample(frac=1).reset_index(drop=True)

        # 2. Combine the golden_df and df if golden_df was provided
        if golden_df is not None:
            combined_df = pd.concat([golden_df, df], ignore_index=True)
        else:
            combined_df = df

        app_strs: list[str] = []
        new_df = pd.DataFrame()
        delimiter = "\n================\n"

        # 3. Get the string for each app, count tokens, and append if within threshold
        for _, row in combined_df.iterrows():
            row_str = row_to_string(row)
            num_tokens = count_tokens(
                f"{delimiter.join(app_strs)}{delimiter}{row_str}")
            if num_tokens < tokens:
                app_strs.append(row_str)
                new_df = pd.concat(
                    [new_df, pd.DataFrame([row])], ignore_index=True)
            else:
                break

        # 4. Shuffle the strings
        if shuffle:
            random.shuffle(app_strs)

        return delimiter.join(app_strs), new_df

    except ImportError:
        raise ImportError(
            "pandas is required to use get_context(). Please install it first.")
