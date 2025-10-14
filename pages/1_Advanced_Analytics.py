from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
from scripts.data_loader import get_all_datasets
from scripts.ui_utils import init_session_state

st.set_page_config(page_title="Advanced Analytics", layout="wide")
init_session_state()

datasets = get_all_datasets()
clean_all = datasets.get("clean_all", pd.DataFrame())

st.markdown("## 🔬 Advanced Analytics")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Promo Type × Category vs IR%")
    if not clean_all.empty and set(["promo_type","category"]).issubset(clean_all.columns):
        # choose IR% column fallback
        ir_col = "ir%" if "ir%" in clean_all.columns else ("ir_percent_calc" if "ir_percent_calc" in clean_all.columns else None)
        if ir_col:
            pivot = clean_all.pivot_table(index="promo_type", columns="category", values=ir_col, aggfunc="mean")
            fig = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="Oranges")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No IR% column found.")
    else:
        st.info("Need 'promo_type' and 'category' in clean_all.")

with col2:
    st.subheader("Treemap: Category → Product → Promo")
    if not clean_all.empty and set(["category","product_name","promo_type"]).issubset(clean_all.columns):
        value_col = "incremental_revenue" if "incremental_revenue" in clean_all.columns else ("revenue_after_promo" if "revenue_after_promo" in clean_all.columns else None)
        if value_col:
            fig = px.treemap(clean_all, path=["category","product_name","promo_type"], values=value_col)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Provide revenue column for sizing.")
    else:
        st.info("Need 'category','product_name','promo_type'.")

with col3:
    st.subheader("Sankey: Campaign → Product → Store")
    st.caption("Placeholder: requires constructing label-indexed links from your data.")

st.markdown("---")

st.subheader("What-if Panel")
colL, colR = st.columns([1,2])
with colL:
    discount = st.slider("Assumed discount %", 0.0, 1.0, 0.2, 0.01)
    margin = st.slider("Assumed margin %", 0.0, 1.0, 0.3, 0.01)
with colR:
    if not clean_all.empty and set(["base_price","quantity_sold (after_promo)"]).issubset(clean_all.columns):
        qty = clean_all["quantity_sold (after_promo)"].sum()
        base_rev = (clean_all["base_price"] * clean_all["quantity_sold (after_promo)"]).sum()
        sim_price = (1 - discount) * clean_all["base_price"]
        sim_rev = (sim_price * clean_all["quantity_sold (after_promo)"]).sum()
        baseline_margin = base_rev * margin
        simulated_margin = sim_rev * margin
        delta_rev = sim_rev - base_rev
        delta_margin = simulated_margin - baseline_margin
        st.metric("Baseline Revenue", f"${base_rev:,.0f}")
        st.metric("Simulated Revenue", f"${sim_rev:,.0f}", delta=f"{delta_rev:,.0f}")
        st.metric("Baseline Margin", f"${baseline_margin:,.0f}")
        st.metric("Simulated Margin", f"${simulated_margin:,.0f}", delta=f"{delta_margin:,.0f}")
    else:
        st.info("Provide 'base_price' and 'quantity_sold (after_promo)' in clean_all for simulation.")
