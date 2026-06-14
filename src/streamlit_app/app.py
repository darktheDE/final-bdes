import streamlit as st
import pandas as pd
import mysql.connector
import subprocess
import plotly.express as px
import plotly.graph_objects as go
import json
import os

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

def render_reports_page():
    st.title("📊 Big Data Reports")
    st.write("Visualizations based on Hive OLAP data (processed via MapReduce).")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Average Rating by District")
        # For demonstration, use mock data if Hive is not set up
        df_dist = pd.DataFrame({
            "district": ["District 1", "District 2", "District 3", "District 4"],
            "avg_rating": [4.2, 4.5, 3.8, 4.0]
        })
        fig_bar1 = px.bar(df_dist, x='district', y='avg_rating', title="Ratings per District", color='district')
        st.plotly_chart(fig_bar1, use_container_width=True)

        st.subheader("2. Cuisine Frequency (Donut)")
        df_cuis = pd.DataFrame({
            "cuisine": ["Vietnamese", "Japanese", "Italian", "American"],
            "count": [120, 45, 30, 20]
        })
        fig_pie1 = px.pie(df_cuis, names='cuisine', values='count', hole=0.4, title="Cuisine Breakdown")
        st.plotly_chart(fig_pie1, use_container_width=True)
        
        st.subheader("3. Reviews Distribution Curve")
        df_revs = pd.DataFrame({
            "stars": [1, 2, 3, 4, 5],
            "reviews": [500, 1200, 3000, 8000, 15000]
        })
        fig_line = px.line(df_revs, x='stars', y='reviews', markers=True, title="Star Distribution")
        st.plotly_chart(fig_line, use_container_width=True)

    with col2:
        st.subheader("4. Sentiment by Category")
        df_sent = pd.DataFrame({
            "category": ["Budget", "Moderate", "Luxury"],
            "sentiment_score": [0.65, 0.78, 0.88]
        })
        fig_bar2 = px.bar(df_sent, x='category', y='sentiment_score', title="Sentiment Score", color='category')
        st.plotly_chart(fig_bar2, use_container_width=True)
        
        st.subheader("5. Price Segment Breakdown")
        df_price = pd.DataFrame({
            "segment": ["Budget", "Moderate", "Luxury"],
            "count": [450, 600, 150]
        })
        fig_pie2 = px.pie(df_price, names='segment', values='count', title="Price Distribution")
        st.plotly_chart(fig_pie2, use_container_width=True)

        st.subheader("6. Delivery vs Non-Delivery Sentiment")
        df_del = pd.DataFrame({
            "type": ["Delivery", "Delivery", "Dine-in", "Dine-in"],
            "x": [1, 2, 1, 2],
            "sentiment": [0.7, 0.75, 0.8, 0.82]
        })
        fig_scatter = px.scatter(df_del, x='x', y='sentiment', color='type', size='sentiment', title="Delivery Sentiment Comparison")
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.info("Note: The visualizations currently use mock datasets representing the expected MapReduce/Hive output.")

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
        "mr_price_segment.py"
    ])
    
    if st.button("Execute Job"):
        with st.spinner(f"Running {job_choice} on Hadoop YARN..."):
            try:
                # Run MapReduce job on Hadoop YARN
                hdfs_base = "hdfs://localhost:9000/data/raw"
                if job_choice == 'mr_cuisine_count.py':
                    cmd = ['python', f'src/mapreduce/{job_choice}', '-r', 'hadoop', f'{hdfs_base}/meals/meals.jsonl']
                else:
                    cmd = ['python', f'src/mapreduce/{job_choice}', '-r', 'hadoop', f'{hdfs_base}/restaurants/restaurants.jsonl']
                    
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
