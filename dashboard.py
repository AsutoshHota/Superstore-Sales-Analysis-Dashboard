import warnings

import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import streamlit as st

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Superstore!!!", page_icon=":bar_chart:", layout="wide")

st.title(":bar_chart: Sample Superstore EDA")
st.markdown("<style>div.block-container{padding-top:2.5rem;}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
fl = st.file_uploader(":file_folder: Upload a File", type=["csv", "txt", "xlsx", "xls"])

if fl is not None:
    st.write(fl.name)
    if fl.name.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(fl)
    else:
        df = pd.read_csv(fl, encoding="ISO-8859-1")
else:
    # Keep Superstore.csv in the same folder as dashboard.py
    df = pd.read_csv("Superstore.csv", encoding="ISO-8859-1")

df["Order Date"] = pd.to_datetime(df["Order Date"])

# ---------------------------------------------------------------------------
# Date filter
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

startDate = df["Order Date"].min()
endDate = df["Order Date"].max()

with col1:
    date1 = pd.to_datetime(st.date_input("Start Date", startDate))

with col2:
    date2 = pd.to_datetime(st.date_input("End Date", endDate))

if date1 > date2:
    st.error("Start date must be before or equal to the end date.")
    st.stop()

df = df[(df["Order Date"] >= date1) & (df["Order Date"] <= date2)].copy()

# ---------------------------------------------------------------------------
# Sidebar filters (Region -> State -> City)
# ---------------------------------------------------------------------------
st.sidebar.header("Choose your filter: ")

region = st.sidebar.multiselect("Pick your Region", sorted(df["Region"].unique()))
df2 = df[df["Region"].isin(region)] if region else df.copy()

state = st.sidebar.multiselect("Pick the State", sorted(df2["State"].unique()))
df3 = df2[df2["State"].isin(state)] if state else df2.copy()

city = st.sidebar.multiselect("Pick the City", sorted(df3["City"].unique()))
filtered_df = df3[df3["City"].isin(city)].copy() if city else df3.copy()

if filtered_df.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# ---------------------------------------------------------------------------
# Category and Region charts
# ---------------------------------------------------------------------------
category_df = filtered_df.groupby(by=["Category"], as_index=False)["Sales"].sum()

with col1:
    st.subheader("Category wise Sales")
    fig = px.bar(
        category_df,
        x="Category",
        y="Sales",
        text=["${:,.2f}".format(x) for x in category_df["Sales"]],
        template="seaborn",
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Region wise Sales")
    fig = px.pie(filtered_df, values="Sales", names="Region", hole=0.5)
    fig.update_traces(textinfo="label+percent", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

cl1, cl2 = st.columns(2)

with cl1:
    with st.expander("Category_ViewData"):
        st.write(category_df.style.background_gradient(cmap="Blues"))
        csv = category_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Data",
            data=csv,
            file_name="Category.csv",
            mime="text/csv",
            help="Click here to download the data as a CSV file",
            key="download_category",
        )

with cl2:
    with st.expander("Region_ViewData"):
        region_df = filtered_df.groupby(by="Region", as_index=False)["Sales"].sum()
        st.write(region_df.style.background_gradient(cmap="Oranges"))
        csv = region_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Data",
            data=csv,
            file_name="Region.csv",
            mime="text/csv",
            help="Click here to download the data as a CSV file",
            key="download_region",
        )

# ---------------------------------------------------------------------------
# Time series
# ---------------------------------------------------------------------------
filtered_df["month_year"] = filtered_df["Order Date"].dt.to_period("M")
st.subheader("Time Series Analysis")

linechart = filtered_df.groupby("month_year")["Sales"].sum().reset_index().sort_values("month_year")
linechart["month_year"] = linechart["month_year"].dt.strftime("%Y : %b")

fig2 = px.line(
    linechart,
    x="month_year",
    y="Sales",
    labels={"Sales": "Amount", "month_year": "Month"},
    height=500,
    template="gridon",
)
st.plotly_chart(fig2, use_container_width=True)

with st.expander("View Data of TimeSeries:"):
    st.write(linechart.set_index("month_year").T.style.background_gradient(cmap="Blues"))
    csv = linechart.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Data",
        data=csv,
        file_name="TimeSeries.csv",
        mime="text/csv",
        key="download_timeseries",
    )

# ---------------------------------------------------------------------------
# Treemap
# ---------------------------------------------------------------------------
st.subheader("Hierarchical view of Sales using TreeMap")
fig3 = px.treemap(
    filtered_df,
    path=["Region", "Category", "Sub-Category"],
    values="Sales",
    hover_data=["Sales"],
    color="Sub-Category",
)
fig3.update_layout(height=650)
st.plotly_chart(fig3, use_container_width=True)

# ---------------------------------------------------------------------------
# Segment and Category pies
# ---------------------------------------------------------------------------
chart1, chart2 = st.columns(2)

with chart1:
    st.subheader("Segment wise Sales")
    fig = px.pie(filtered_df, values="Sales", names="Segment", template="plotly_dark")
    fig.update_traces(textinfo="label+percent", textposition="inside")
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader("Category wise Sales")
    fig = px.pie(filtered_df, values="Sales", names="Category", template="gridon")
    fig.update_traces(textinfo="label+percent", textposition="inside")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Summary table and month-wise pivot
# ---------------------------------------------------------------------------
st.subheader(":point_right: Month wise Sub-Category Sales Summary")
with st.expander("Summary_Table"):
    df_sample = filtered_df.head(5)[
        ["Region", "State", "City", "Category", "Sales", "Profit", "Quantity"]
    ]
    fig = ff.create_table(df_sample, colorscale="Cividis")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("Month wise sub-Category Table")
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    filtered_df["month"] = pd.Categorical(
        filtered_df["Order Date"].dt.month_name(), categories=month_order, ordered=True
    )
    sub_category_month = pd.pivot_table(
        data=filtered_df,
        values="Sales",
        index=["Sub-Category"],
        columns="month",
        aggfunc="sum",
        observed=False,
    ).fillna(0)
    st.write(sub_category_month.style.background_gradient(cmap="Blues"))

# ---------------------------------------------------------------------------
# Scatter plot
# ---------------------------------------------------------------------------
# size must be positive, so guard against zero/negative quantities
scatter_df = filtered_df[filtered_df["Quantity"] > 0]
data1 = px.scatter(scatter_df, x="Sales", y="Profit", size="Quantity")
data1.update_layout(
    title=dict(
        text="Relationship between Sales and Profits using Scatter Plot.",
        font=dict(size=20),
    ),
    xaxis=dict(title=dict(text="Sales", font=dict(size=19))),
    yaxis=dict(title=dict(text="Profit", font=dict(size=19))),
)
st.plotly_chart(data1, use_container_width=True)

with st.expander("View Data"):
    view_cols = [
        "Order Date", "Region", "State", "City", "Category", "Sub-Category",
        "Sales", "Quantity", "Discount", "Profit",
    ]
    view_cols = [c for c in view_cols if c in filtered_df.columns]
    numeric_cols = [c for c in ["Sales", "Quantity", "Discount", "Profit"] if c in view_cols]
    st.write(
        filtered_df[view_cols]
        .head(500)
        .style.background_gradient(cmap="Oranges", subset=numeric_cols)
    )

# ---------------------------------------------------------------------------
# Download the (date-filtered) dataset
# ---------------------------------------------------------------------------
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("Download Data", data=csv, file_name="Data.csv", mime="text/csv", key="download_all")