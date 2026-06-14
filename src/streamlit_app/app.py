import streamlit as st
import pandas as pd
import mysql.connector
import subprocess
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import sys

# Add streamlit_app directory to path so hive_connector resolves correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from hive_connector import (
        query_hive, get_hive_status, reset_connection_cache, batch_query_all_views
    )
    _HIVE_CONNECTOR_AVAILABLE = True
except ImportError:
    _HIVE_CONNECTOR_AVAILABLE = False

# Set page layout
st.set_page_config(page_title="Food Sentiment Analysis", layout="wide", page_icon="🍲")

# Custom CSS for aesthetics
st.markdown("""
<style>
    .reportview-container {
        background: #1e1e1e;
        color: white;
    }
    .sidebar .sidebar-content {
        background: #2b2b2b;
    }
    h1, h2, h3 {
        color: #fca311;
    }
    .stButton>button {
        background-color: #14213d;
        color: white;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #fca311;
        color: black;
    }
</style>
""", unsafe_allow_html=True)

# Function to connect to MySQL (Streamlit runs inside WSL, MySQL on 127.0.0.1 TCP port 3306)
def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="root",
        database="food_sentiment_db",
        use_pure=True        # Force pure-Python driver to avoid Unix socket fallback
    )

def run_hive_query(query):
    """Run Hive query using subprocess and return a pandas DataFrame."""
    try:
        # Using hive -e with sed to remove warnings and keep only output
        # Setting hive.cli.print.header=true gives us headers
        full_query = f"set hive.cli.print.header=true; {query}"
        result = subprocess.check_output(['hive', '-S', '-e', full_query], stderr=subprocess.STDOUT)
        
        # Parse TSV
        from io import StringIO
        output = result.decode('utf-8')
        
        # Filter out noisy Hadoop logs if any
        clean_lines = [line for line in output.split('\n') if not line.startswith('SLF4J')]
        clean_output = '\n'.join(clean_lines)
        
        if clean_output.strip():
            df = pd.read_csv(StringIO(clean_output), sep='\t')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Hive Query Failed: {e}")
        return pd.DataFrame()

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select a page:", 
                            ["Data Management (CRUD)", "Big Data Reports", "DevOps & Jobs Execution"])

    if page == "Data Management (CRUD)":
        render_crud_page()
    elif page == "Big Data Reports":
        render_reports_page()
    elif page == "DevOps & Jobs Execution":
        render_devops_page()

def render_crud_page():
    st.title("🍽️ Data Management (CRUD)")
    st.write("Manage restaurants in the MySQL relational database.")
    
    # Initialize connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
    except Exception as e:
        st.error(f"Failed to connect to MySQL: {e}")
        return

    # Tabs for CRUD operations
    tab_read, tab_insert, tab_update, tab_delete = st.tabs(["View Records", "Insert New", "Update Record", "Delete Record"])
    
    with tab_read:
        st.subheader("View Restaurants")
        search_term = st.text_input("Search by Name or District:", "")
        if st.button("Search"):
            if search_term:
                cursor.execute("SELECT * FROM restaurants WHERE name LIKE %s OR district LIKE %s LIMIT 100", (f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor.execute("SELECT * FROM restaurants LIMIT 100")
            
            rows = cursor.fetchall()
            df = pd.DataFrame(rows)
            if not df.empty:
                st.dataframe(df)
            else:
                st.warning("No records found.")
                
    with tab_insert:
        st.subheader("Insert New Restaurant")
        with st.form("insert_form"):
            r_id = st.text_input("ID (e.g., rest_9999)")
            name = st.text_input("Name")
            rating = st.number_input("Rating", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
            rev_count = st.number_input("Review Count", min_value=0, value=0)
            address = st.text_input("Address")
            district = st.text_input("District")
            city = st.text_input("City", value="HCMC")
            price = st.selectbox("Price Range", ["Budget", "Moderate", "Luxury", "Unknown"])
            
            submit = st.form_submit_button("Insert Record")
            if submit:
                try:
                    cursor.execute("""
                        INSERT INTO restaurants (id, name, rating, review_count, address, district, city, price_range) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (r_id, name, rating, rev_count, address, district, city, price))
                    conn.commit()
                    st.success(f"Restaurant '{name}' inserted successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab_update:
        st.subheader("Update Restaurant Rating")
        with st.form("update_form"):
            update_id = st.text_input("Restaurant ID to update")
            new_rating = st.number_input("New Rating", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
            
            update_submit = st.form_submit_button("Update")
            if update_submit:
                try:
                    cursor.execute("UPDATE restaurants SET rating = %s WHERE id = %s", (new_rating, update_id))
                    conn.commit()
                    st.success(f"Updated rating for ID '{update_id}'.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab_delete:
        st.subheader("Delete Restaurant")
        with st.form("delete_form"):
            delete_id = st.text_input("Restaurant ID to delete")
            del_submit = st.form_submit_button("Delete")
            if del_submit:
                try:
                    cursor.execute("DELETE FROM restaurants WHERE id = %s", (delete_id,))
                    conn.commit()
                    st.success(f"Deleted restaurant ID '{delete_id}'.")
                except Exception as e:
                    st.error(f"Error: {e}")

    conn.close()

def _mock_dist():
    return pd.DataFrame({
        "district": ["Quận 1", "Quận 3", "Quận 5", "Bình Thạnh", "Quận 7"],
        "avg_rating": [4.35, 4.28, 4.10, 4.20, 4.45],
        "total_count": [312, 198, 87, 145, 203],
    })

def _mock_cuisine():
    return pd.DataFrame({
        "category": ["Seafood", "Chicken", "Beef", "Vegetarian", "Pork", "Pasta"],
        "cnt": [85, 78, 65, 52, 47, 43],
    })

def _mock_price_seg():
    return pd.DataFrame({
        "price_range": ["Budget", "Moderate", "Luxury", "Unknown"],
        "cnt": [487, 612, 158, 77],
    })

def _mock_sentiment_price():
    return pd.DataFrame({
        "price_range": ["Luxury", "Moderate", "Budget"],
        "avg_sentiment": [4.52, 4.21, 3.95],
        "review_count": [8423, 24156, 18934],
    })

def _mock_review_dist():
    return pd.DataFrame({
        "stars": [1, 2, 3, 4, 5],
        "cnt": [612, 1478, 5834, 18920, 22450],
    })

def _mock_delivery():
    return pd.DataFrame({
        "service_type": ["Dine-in", "Delivery"],
        "avg_rating": [4.22, 3.98],
        "review_count": [41830, 7464],
    })


def render_reports_page():
    st.title("📊 Big Data Reports")
    st.caption("OLAP analytics powered by Apache Hive — backed by Hadoop HDFS")

    # ── Data source status banner ─────────────────────────────────────────────
    if _HIVE_CONNECTOR_AVAILABLE:
        with st.spinner("Detecting Hive connection..."):
            hive_mode = get_hive_status()

        col_status, col_refresh = st.columns([5, 1])
        with col_status:
            if hive_mode == "live":
                st.success("🟢 **Live Hive Data** — Connected to HiveServer2 (port 10000). Charts show real-time HDFS data.")
            elif hive_mode == "subprocess":
                st.warning("🟡 **Hive CLI Mode** — HiveServer2 not running; using `hive -S -e` subprocess fallback. Data is live but slower.")
            else:
                st.info("⚪ **Offline Mode** — Hive not available. Charts display pre-computed representative data.")
        with col_refresh:
            if st.button("🔄 Re-probe", help="Force re-detect Hive connection mode"):
                reset_connection_cache()
                st.rerun()
    else:
        hive_mode = "offline"
        st.info("⚪ **Offline Mode** — `hive_connector` module not loaded. Displaying pre-computed mock data.")

    st.divider()

    # ── Batch load all data once, cache in session_state ──────────────────────
    # Key includes hive_mode so a mode change triggers a fresh fetch
    cache_key = f"hive_data_{hive_mode}"

    col_refresh_top, _ = st.columns([1, 5])
    with col_refresh_top:
        force_refresh = st.button(
            "🔄 Refresh Data",
            help="Re-query all Hive views (clears cached results)",
            key="refresh_data_btn",
        )

    if force_refresh or cache_key not in st.session_state:
        with st.spinner("⏳ Loading analytics data from Hive (this may take 1–2 minutes on first load)..."):
            if _HIVE_CONNECTOR_AVAILABLE and hive_mode != "offline":
                data = batch_query_all_views()
            else:
                # offline: use mock
                data = {
                    "view_rating_by_district": _mock_dist(),
                    "view_cuisine_frequency": _mock_cuisine(),
                    "view_price_segment": _mock_price_seg(),
                    "view_sentiment_by_price": _mock_sentiment_price(),
                    "view_review_distribution": _mock_review_dist(),
                    "view_delivery_sentiment": _mock_delivery(),
                }
        st.session_state[cache_key] = data
    else:
        data = st.session_state[cache_key]

    def get_df(view_key: str, mock_fn) -> pd.DataFrame:
        df = data.get(view_key, pd.DataFrame())
        return df

    # ── Charts grid ───────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        # Chart 1 — Average Rating by District (Bar)
        st.subheader("1. Đánh giá trung bình theo Quận")
        df_dist = get_df("view_rating_by_district", _mock_dist)
        try:
            fig_bar1 = px.bar(
                df_dist, x="district", y="avg_rating",
                title="Ratings per District",
                color="avg_rating",
                color_continuous_scale="Oranges",
                hover_data={"total_count": True, "avg_rating": ":.2f"},
                text="avg_rating",
            )
            fig_bar1.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_bar1.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_bar1, use_container_width=True)
        except Exception as e:
            st.error(f"Chart 1 render error: {e}")

        # Chart 2 — Cuisine Frequency (Donut)
        st.subheader("2. Phân bố ẩm thực (Donut)")
        df_cuis = get_df("view_cuisine_frequency", _mock_cuisine)
        try:
            fig_pie1 = px.pie(
                df_cuis, names="category", values="cnt",
                hole=0.42, title="Cuisine Category Breakdown",
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig_pie1.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie1, use_container_width=True)
        except Exception as e:
            st.error(f"Chart 2 render error: {e}")

        # Chart 3 — Review Star Distribution (Line)
        st.subheader("3. Phân phối số sao đánh giá")
        df_revs = get_df("view_review_distribution", _mock_review_dist)
        try:
            fig_line = px.line(
                df_revs, x="stars", y="cnt",
                markers=True, title="Star Rating Distribution Curve",
                color_discrete_sequence=["#fca311"],
            )
            fig_line.update_traces(line_width=3, marker_size=9)
            fig_line.update_xaxes(tickvals=[1, 2, 3, 4, 5])
            st.plotly_chart(fig_line, use_container_width=True)
        except Exception as e:
            st.error(f"Chart 3 render error: {e}")

    with col2:
        # Chart 4 — Sentiment (avg rating) by Price Range (Bar)
        st.subheader("4. Sentiment trung bình theo phân khúc giá")
        df_sent = get_df("view_sentiment_by_price", _mock_sentiment_price)
        try:
            fig_bar2 = px.bar(
                df_sent, x="price_range", y="avg_sentiment",
                title="Avg Sentiment Score by Price Segment",
                color="price_range",
                color_discrete_sequence=px.colors.qualitative.Vivid,
                hover_data={"review_count": True, "avg_sentiment": ":.3f"},
                text="avg_sentiment",
            )
            fig_bar2.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            st.plotly_chart(fig_bar2, use_container_width=True)
        except Exception as e:
            st.error(f"Chart 4 render error: {e}")

        # Chart 5 — Price Segment Breakdown (Pie)
        st.subheader("5. Phân khúc giá (Pie)")
        df_price = get_df("view_price_segment", _mock_price_seg)
        try:
            fig_pie2 = px.pie(
                df_price, names="price_range", values="cnt",
                title="Price Range Distribution",
                color_discrete_sequence=px.colors.sequential.RdBu,
            )
            fig_pie2.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie2, use_container_width=True)
        except Exception as e:
            st.error(f"Chart 5 render error: {e}")

        # Chart 6 — Delivery vs Dine-in Sentiment (Scatter / Bubble)
        st.subheader("6. Delivery vs Dine-in — So sánh Sentiment")
        df_del = get_df("view_delivery_sentiment", _mock_delivery)
        try:
            fig_scatter = px.scatter(
                df_del,
                x="service_type", y="avg_rating",
                size="review_count", color="service_type",
                title="Delivery vs Dine-in Sentiment Comparison",
                color_discrete_sequence=["#fca311", "#14213d"],
                hover_data={"review_count": True, "avg_rating": ":.3f"},
                text="avg_rating",
            )
            fig_scatter.update_traces(texttemplate="%{text:.2f}", textposition="top center")
            fig_scatter.update_yaxes(range=[3.5, 5.0])
            st.plotly_chart(fig_scatter, use_container_width=True)
        except Exception as e:
            st.error(f"Chart 6 render error: {e}")

def render_devops_page():
    st.title("⚙️ DevOps & Jobs Execution")
    st.write("Trigger backup scripts and MapReduce batch jobs directly from the dashboard.")
    
    st.subheader("1. Database Backup")
    if st.button("Run Backup Script (db_backup.sh)"):
        with st.spinner("Running backup..."):
            try:
                result = subprocess.check_output(['bash', 'src/backup/db_backup.sh'], stderr=subprocess.STDOUT)
                st.success("Backup Completed!")
                st.code(result.decode('utf-8'))
            except Exception as e:
                st.error(f"Backup script failed or not found: {e}")

    st.subheader("2. Run MapReduce Analytical Jobs")
    job_choice = st.selectbox("Select Job to Run", [
        "mr_rating_by_district.py",
        "mr_cuisine_count.py",
        "mr_price_segment.py",
        "mr_sentiment_analysis.py",
        "mr_ingredient_match.py",
        "mr_top_reviewed.py",
        "mr_review_distribution.py",
        "mr_delivery_analysis.py"
    ])
    
    if st.button("Execute Job"):
        with st.spinner(f"Running {job_choice} on Hadoop YARN..."):
            try:
                # Run MapReduce job on Hadoop YARN
                hdfs_base = "hdfs://localhost:9000/data/raw"
                conf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mrjob.conf'))
                if job_choice == 'mr_cuisine_count.py':
                    cmd = ['python', f'src/mapreduce/{job_choice}', '-r', 'hadoop', '--conf-path', conf_path, f'{hdfs_base}/meals/meals.jsonl']
                elif job_choice == 'mr_ingredient_match.py':
                    cmd = ['python', f'src/mapreduce/{job_choice}', '-r', 'hadoop', '--conf-path', conf_path, '--file', 'src/crawler/seed/ingredients.json', f'{hdfs_base}/restaurants/restaurants.jsonl']
                else:
                    cmd = ['python', f'src/mapreduce/{job_choice}', '-r', 'hadoop', '--conf-path', conf_path, f'{hdfs_base}/restaurants/restaurants.jsonl']
                    
                result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                st.success(f"{job_choice} completed!")
                st.code(result.decode('utf-8'))
            except subprocess.CalledProcessError as e:
                st.error(f"Job failed.")
                st.code(e.output.decode('utf-8'))
            except Exception as e:
                st.error(f"Execution error: {e}")

if __name__ == "__main__":
    main()
