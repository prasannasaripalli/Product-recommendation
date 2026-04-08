import os
import random
import pandas as pd

FEEDBACK_PATH = "storage/feedback.csv"
EPSILON = 0.2


class ProductRecommender:
    def __init__(self, products_path, feedback_path=FEEDBACK_PATH):
        self.products_path = products_path
        self.feedback_path = feedback_path
        self.products_df = pd.read_csv(products_path)
        self.feedback_df = self.load_feedback()

    def load_feedback(self):
        if os.path.exists(self.feedback_path):
            return pd.read_csv(self.feedback_path)

        df = pd.DataFrame(columns=["user_id", "product_id", "shown", "clicked"])
        df.to_csv(self.feedback_path, index=False)
        return df

    def refresh_feedback(self):
        self.feedback_df = self.load_feedback()

    def get_products_by_category(self, category):
        if not category or category == "All":
            return self.products_df.copy()
        return self.products_df[self.products_df["category"] == category].copy()

    def get_user_preference(self, user_id):
        if self.feedback_df.empty:
            return None

        clicked_df = self.feedback_df[
            (self.feedback_df["user_id"] == user_id) &
            (self.feedback_df["clicked"] == 1)
        ]

        if clicked_df.empty:
            return None

        merged = clicked_df.merge(
            self.products_df[["product_id", "category"]],
            on="product_id",
            how="left"
        )

        if merged.empty:
            return None

        return merged["category"].mode().iloc[0]

    def get_product_stats(self):
        stats = self.products_df[["product_id", "product_name", "category", "brand", "price", "rating"]].copy()

        if self.feedback_df.empty:
            stats["shown_count"] = 0
            stats["click_count"] = 0
            stats["click_rate"] = 0.0
            return stats

        grouped = self.feedback_df.groupby("product_id")[["shown", "clicked"]].sum().reset_index()
        grouped = grouped.rename(columns={"shown": "shown_count", "clicked": "click_count"})

        stats = stats.merge(grouped, on="product_id", how="left").fillna(0)
        stats["shown_count"] = stats["shown_count"].astype(int)
        stats["click_count"] = stats["click_count"].astype(int)

        stats["click_rate"] = stats.apply(
            lambda row: row["click_count"] / row["shown_count"] if row["shown_count"] > 0 else 0.0,
            axis=1
        )

        return stats

    def choose_recommendations(self, user_id, category="All", top_n=20, epsilon=EPSILON):
        user_preference = self.get_user_preference(user_id)

        if category != "All":
            candidates = self.get_products_by_category(category)
        elif user_preference:
            candidates = self.get_products_by_category(user_preference)
        else:
            candidates = self.products_df.copy()

        stats = self.get_product_stats()[["product_id", "shown_count", "click_count", "click_rate"]]
        candidates = candidates.merge(stats, on="product_id", how="left").fillna(0)

        if candidates.empty:
            return []

        recommendations = []
        available = candidates.copy()

        for _ in range(min(top_n, len(available))):
            if random.random() < epsilon:
                selected = available.sample(1).iloc[0]
            else:
                selected = available.sort_values(
                    by=["click_rate", "rating", "shown_count"],
                    ascending=[False, False, True]
                ).iloc[0]

            recommendations.append(selected.to_dict())
            available = available[available["product_id"] != selected["product_id"]]

        return recommendations

    def save_feedback(self, user_id, product_id, shown, clicked):
        row = pd.DataFrame([{
            "user_id": user_id,
            "product_id": product_id,
            "shown": shown,
            "clicked": clicked
        }])
        row.to_csv(self.feedback_path, mode="a", index=False, header=False)
        self.refresh_feedback()

    def log_impression(self, user_id, product_id):
        self.save_feedback(user_id, product_id, shown=1, clicked=0)

    def log_click(self, user_id, product_id):
        self.save_feedback(user_id, product_id, shown=0, clicked=1)