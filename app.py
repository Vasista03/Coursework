from __future__ import annotations
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
from datetime import date

from scripts.data_loader import get_all_datasets, apply_global_filters
from scripts.ui_utils import init_session_state, metric_card, dataframe_download, kpi_color

st.set_page_config(page_title="Promo Performance Dashboard", layout="wide")

# Inject CSS
with open(os.path.join("assets", "style.css"), "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

init_session_state()

@st.cache_data(show_spinner=False)
def load_data():
    return get_all_datasets()

datasets = load_data()
# Unpack
campaigns = datasets.get("campaign_data", pd.DataFrame())
products = datasets.get("product_data", pd.DataFrame())
stores = datasets.get("stores_data", pd.DataFrame())
events = datasets.get("event_data", pd.DataFrame())
clean_revenue = datasets.get("clean_revenue", pd.DataFrame())
city_sales = datasets.get("city_sales", pd.DataFrame())
clean_all = datasets.get("clean_all", pd.DataFrame())

# ------- TOP BAR -------
st.markdown("## 📊 Promo Performance Dashboard")

# Top-level filters
col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,2,2,2])
with col1:
    st.session_state["campaigns"] = st.multiselect("Campaign", options=campaigns.get("campaign_id", pd.Series()).unique().tolist())
with col2:
    st.session_state["categories"] = st.multiselect("Category", options=products.get("category", pd.Series()).unique().tolist())
with col3:
    st.session_state["products"] = st.multiselect("Product", options=products.get("product_code", pd.Series()).unique().tolist())
with col4:
    st.session_state["promo_types"] = st.multiselect("Promo Type", options=events.get("promo_type", pd.Series()).dropna().unique().tolist())
with col5:
    st.session_state["cities"] = st.multiselect("City", options=stores.get("city", pd.Series()).dropna().unique().tolist())
with col6:
    st.session_state["kpi_focus"] = st.radio("KPI", ["Revenue","Units","Margin","IR%"], horizontal=True)

# Date presets
c7, c8, c9 = st.columns([2,2,2])
with c7:
    today = date.today()
    st.session_state["date_start"], st.session_state["date_end"] = st.date_input("Date Range", value=(date(today.year,1,1), today))
with c8:
    st.session_state["compare_mode"] = st.toggle("Compare Mode")
with c9:
    if st.button("Apply Filters", type="primary"):
        st.experimental_rerun()

# ------- SIDEBAR -------
with st.sidebar:
    st.header("Filters & Controls")
    st.caption("Use Apply Filters from top bar to update")

    with st.expander("Sliders"):
        st.session_state["discount_range"] = st.slider("Discount %", 0.0, 1.0, st.session_state.get("discount_range", (0.0, 1.0)))
        st.session_state["price_range"] = st.slider("Base Price", 0.0, 1_000.0, st.session_state.get("price_range", (0.0, 1_000.0)))
        st.session_state["inc_rev_range"] = st.slider("Incremental Revenue", 0.0, 100000.0, st.session_state.get("inc_rev_range", (0.0, 100000.0)))
        st.session_state["ir_range"] = st.slider("IR%", 0.0, 1.0, st.session_state.get("ir_range", (0.0, 1.0)))
    with st.expander("Flags"):
        st.checkbox("Show Before", value=True, key="show_before")
        st.checkbox("Show After", value=True, key="show_after")
        st.checkbox("Positive results only", value=False, key="positive_only")
        st.checkbox("Normalize by store size", value=False, key="normalize_store")
    st.session_state["top_n"] = st.number_input("Top N", min_value=5, max_value=100, value=10)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Reset"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.experimental_rerun()
    with col_b:
        st.button("Export view")

# ------- CENTER + RIGHT PANELS -------
center, right = st.columns([2,1])

# Apply global filters to dataframes where applicable
filtered_clean_revenue = apply_global_filters(clean_revenue, st.session_state)
filtered_city_sales = apply_global_filters(city_sales, st.session_state)
filtered_clean_all = apply_global_filters(clean_all, st.session_state)

# Prepare data for visuals using filtered data
map_df = filtered_city_sales.copy()
if not map_df.empty:
    # Decide color metric by KPI
    kpi = st.session_state.get("kpi_focus", "Revenue").lower()
    color_col = "revenue_after_promo" if "rev" in kpi else (
        "total_quantity_sold" if "unit" in kpi else (
            "margin_efficiency" if "margin" in kpi and "margin_efficiency" in map_df.columns else "total_quantity_sold"
        )
    )

with center:
    st.subheader("Geospatial Performance")
    # Controls for map type before rendering
    map_mode = st.radio("Map Mode", ["Bubbles","Heatmap"], horizontal=True, key="map_mode")
    if map_df.empty or not set(["lat","lng"]).issubset(map_df.columns):
        st.info("City map requires 'lat' and 'lng' columns in city_sales.")
    else:
        view_state = pdk.ViewState(latitude=float(map_df["lat"].mean()), longitude=float(map_df["lng"].mean()), zoom=3)
        layers = []
        if map_mode == "Bubbles":
            layers.append(pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position='[lng, lat]',
                get_radius='total_quantity_sold',
                radius_scale=20,
                get_fill_color='[50, 180, 120, 160]',
                pickable=True,
                auto_highlight=True,
            ))
        else:
            layers.append(pdk.Layer(
                "HeatmapLayer",
                data=map_df,
                get_position='[lng, lat]',
                get_weight='total_quantity_sold',
                radius_pixels=60,
            ))
        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state, tooltip={"text": "{city}\nQty: {total_quantity_sold}"}))

    # Focus city selector to drive drill-down
    if not map_df.empty and "city" in map_df.columns:
        st.session_state["selected_city"] = st.selectbox("Focus City", ["All"] + sorted(map_df["city"].dropna().unique().tolist()))

    # Additional chart: Before vs After stacked bar from clean_revenue
    st.subheader("Before vs After by City")
    if filtered_clean_revenue.empty:
        st.info("Upload clean_revenue to see charts.")
    else:
        # Aggregate
        agg = filtered_clean_revenue.groupby("city").agg({
            "revenue_before_promo": "sum", "revenue_after_promo": "sum"
        }).reset_index()
        chart = px.bar(agg.melt(id_vars="city", var_name="phase", value_name="revenue"), x="city", y="revenue", color="phase", barmode="group")
        st.plotly_chart(chart, use_container_width=True)

with right:
    st.subheader("KPI Summary")
    # Basic KPIs
    # City-scoped metrics when a focus city is selected
    scope_df = filtered_clean_revenue
    focus_city = st.session_state.get("selected_city")
    if focus_city and focus_city != "All" and "city" in scope_df.columns:
        scope_df = scope_df[scope_df["city"] == focus_city]

    total_before = scope_df["revenue_before_promo"].sum() if "revenue_before_promo" in scope_df.columns else 0
    total_after = scope_df["revenue_after_promo"].sum() if "revenue_after_promo" in scope_df.columns else 0
    ir_percent = (total_after - total_before) / total_before * 100 if total_before else 0

    metric_card("Revenue Before", f"${total_before:,.0f}")
    metric_card("Revenue After", f"${total_after:,.0f}")
    metric_card("IR%", f"{ir_percent:.1f}%")

    # Scatter: discount vs margin if available
    st.subheader("Discount vs Margin")
    if not filtered_clean_all.empty and set(["promo_discount","incremental_margin%","promo_category"]).issubset(filtered_clean_all.columns):
        scatter_df = filtered_clean_all
        if focus_city and focus_city != "All" and "city" in scatter_df.columns:
            scatter_df = scatter_df[scatter_df["city"] == focus_city]
        fig = px.scatter(scatter_df, x="promo_discount", y="incremental_margin%", color="promo_category")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Provide 'promo_discount' and 'incremental_margin%' in clean_all for scatter.")

    # Data table
    st.subheader("Details")
    if not filtered_clean_revenue.empty:
        st.dataframe(filtered_clean_revenue.head(200), use_container_width=True)
        dataframe_download(filtered_clean_revenue, "clean_revenue_view.csv")
    else:
        st.caption("No data loaded.")

# ------- BOTTOM BAND -------
st.markdown("---")
st.subheader("Advanced Analytics")

bt1, bt2, bt3 = st.columns(3)

with bt1:
    st.caption("Heatmap: promo_type × category vs IR% (placeholder)")
with bt2:
    st.caption("Treemap: category → product → promo (placeholder)")
with bt3:
    st.caption("Sankey: campaign → product → store (placeholder)")

st.success("Scaffold ready. Place your CSVs under /data and run: streamlit run app.py")
