import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Sales Performance Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).parent / "data" / "sales_sample.csv"


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """Load the demo dataset from disk and enrich with convenience columns."""
    df = pd.read_csv(DATA_PATH, parse_dates=["order_date"])
    df["month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    df["year"] = df["order_date"].dt.year
    return df


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.header("Filters")
        regions = st.multiselect(
            "Region",
            options=sorted(df["region"].unique()),
            default=sorted(df["region"].unique()),
        )
        categories = st.multiselect(
            "Category",
            options=sorted(df["category"].unique()),
            default=sorted(df["category"].unique()),
        )
        segments = st.multiselect(
            "Customer segment",
            options=sorted(df["customer_segment"].unique()),
            default=sorted(df["customer_segment"].unique()),
        )
        min_date = df["order_date"].min().date()
        max_date = df["order_date"].max().date()
        date_range = st.date_input(
            "Order date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        st.caption("Download or adjust the filters to explore the dataset.")

    filtered = df.copy()
    if regions:
        filtered = filtered[filtered["region"].isin(regions)]
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]
    if segments:
        filtered = filtered[filtered["customer_segment"].isin(segments)]

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered = filtered[filtered["order_date"].between(start, end)]

    return filtered


def render_kpis(df: pd.DataFrame) -> None:
    total_sales = float(df["sales"].sum())
    total_profit = float(df["profit"].sum())
    avg_margin = (total_profit / total_sales * 100) if total_sales else 0.0
    avg_order_value = df["sales"].mean() if not df.empty else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total sales", f"${total_sales:,.0f}")
    col2.metric("Total profit", f"${total_profit:,.0f}")
    col3.metric("Average margin", f"{avg_margin:,.1f}%")
    col4.metric("Avg. order", f"${avg_order_value:,.0f}")


def render_charts(df: pd.DataFrame) -> None:
    sales_trend = df.groupby("order_date", as_index=False)["sales"].sum()
    category_sales = df.groupby("category", as_index=False)["sales"].sum()
    segment_profit = df.groupby("customer_segment", as_index=False)["profit"].sum()

    trend_fig = px.line(
        sales_trend,
        x="order_date",
        y="sales",
        title="Daily sales trend",
        markers=True,
    )
    trend_fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))

    category_fig = px.bar(
        category_sales,
        x="category",
        y="sales",
        title="Sales by category",
        color="category",
        text_auto=True,
    )
    category_fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10))

    segment_fig = px.pie(
        segment_profit,
        names="customer_segment",
        values="profit",
        title="Profit contribution by segment",
        hole=0.4,
    )
    segment_fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))

    left_col, right_col = st.columns((2, 1))
    left_col.plotly_chart(trend_fig, use_container_width=True)
    left_col.plotly_chart(category_fig, use_container_width=True)
    right_col.plotly_chart(segment_fig, use_container_width=True)


def render_details(df: pd.DataFrame) -> None:
    st.subheader("Transaction details")
    st.dataframe(
        df.sort_values("order_date", ascending=False),
        use_container_width=True,
    )
    st.download_button(
        "Download filtered data",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_sales.csv",
        mime="text/csv",
    )


def main() -> None:
    st.title("Sales Performance Dashboard")
    st.caption(
        "Use this demo to explore sales, profit, and customer trends on a simple sample dataset. "
        "Adjust the filters in the sidebar to focus on specific regions or customer segments."
    )

    data = load_data()
    filtered_data = filter_data(data)

    if filtered_data.empty:
        st.warning("No records match your filters. Adjust the selections to see data.")
        return

    render_kpis(filtered_data)
    st.divider()
    render_charts(filtered_data)
    st.divider()
    render_details(filtered_data)


if __name__ == "__main__":
    main()
