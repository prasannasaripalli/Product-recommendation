import uuid
import streamlit as st

from recommendation import ProductRecommender


st.set_page_config(page_title="Product Recommendation System", layout="wide")
st.title("Product Recommendation System")
st.caption("Discover products picked for you.")

@st.cache_resource
def load_recommender():
    return ProductRecommender("data/products.csv")

recommender = load_recommender()

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]

if "recommendations" not in st.session_state:
    st.session_state.recommendations = []

if "impressions_logged" not in st.session_state:
    st.session_state.impressions_logged = False


def get_categories():
    return ["All"] + sorted(recommender.products_df["category"].unique().tolist())


with st.sidebar:
    st.header("Shop")
    category = st.selectbox("Category", get_categories())

    if st.button("Show Products", type="primary"):
        category_products = recommender.get_products_by_category(category)
        st.session_state.recommendations = recommender.choose_recommendations(
            user_id=st.session_state.user_id,
            category=category,
            top_n=len(category_products)
        )
        st.session_state.impressions_logged = False
        st.rerun()

    if st.button("Clear"):
        st.session_state.recommendations = []
        st.session_state.impressions_logged = False
        st.rerun()


recommendations = st.session_state.recommendations

if recommendations and not st.session_state.impressions_logged:
    for item in recommendations:
        recommender.log_impression(st.session_state.user_id, int(item["product_id"]))
    st.session_state.impressions_logged = True

if not recommendations:
    st.info("Select a category and click 'Show Products' to browse recommendations.")
else:
    st.subheader("Recommended for You")

    cols = st.columns(3)

    for i, item in enumerate(recommendations):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {item['product_name']}")
                st.write(f"**Brand:** {item['brand']}")
                st.write(f"**Category:** {item['category']}")
                st.write(f"**Price:** ${item['price']:.2f}")
                st.write(f"**Rating:** {item['rating']}")
                st.write(item["description"])

                if st.button("View / Click", key=f"click_{item['product_id']}"):
                    recommender.log_click(st.session_state.user_id, int(item["product_id"]))
                    st.success(f"You clicked {item['product_name']}")