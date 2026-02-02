


import os

# --- 1. HEADLESS DISPLAY SETUP (CRITICAL FOR CLOUD) ---
# We must start the "fake screen" before importing PyVista
os.system('/usr/bin/Xvfb :99 -screen 0 1024x768x24 &')
os.environ['DISPLAY'] = ':99'


import streamlit as st
import pyvista as pv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from stpyvista import stpyvista
import plotly.graph_objects as go
# ==========================================
# 1. PAGE CONFIG & CSS (FULL SCREEN HACKS)
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="NING RESEARCH | Digital Twin",
    page_icon="⚗️",
    initial_sidebar_state="expanded"
)

# FORCE FULL SCREEN & DARK MODE
st.markdown("""
<style>
    /* 1. Main Background */
    .stApp { background-color: #000000; }
    
    /* 2. Text Colors */
    h1, h2, h3, h4, h5, h6, p, li, span { color: #FFFFFF !important; }
    div[data-testid="stMetricValue"] { color: #00FF7F !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #CCCCCC !important; }
    section[data-testid="stSidebar"] { background-color: #111111; }
    
    /* 3. REMOVE PADDING (The "Come Down" Fix) */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    
    /* 4. MAXIMIZE IFRAME (The "Empty Space" Fix) */
    iframe {
        width: 100% !important;
        height: 80vh !important; /* Forces plot to take 80% of vertical screen */
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00FFFF;'>NING RESEARCH</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.header("🎛️ Controls")
    
    with st.expander("Process Inputs", expanded=True):
        fluid_ratio = st.slider("Fluid A Ratio (%)", 0, 100, 49)
        time_step = st.slider("Time Step (s)", 0.0, 10.0, 0.5)

    with st.expander("Viz Settings", expanded=False):
        cmap_choice = st.selectbox("Color Map", ["jet", "turbo", "magma", "viridis"], index=0)
        v_max = st.slider("Max Velocity (m/s)", 1.0, 20.0, 5.0)
        show_bg_grid = st.checkbox("Show Reference Grid", value=True) 

# ==========================================
# 3. HELPER FUNCTION
# ==========================================
@st.cache_resource
def load_mesh():
    try:
        multiblock = pv.read("master.case")
        grid = multiblock[0]
        return grid
    except:
        return pv.Cylinder(radius=0.5, height=1.2, direction=(0,0,1))

# ==========================================
# 4. VISUALIZATION ENGINES (LARGE SCREEN)
# ==========================================

# --- ENGINE A: VELOCITY ---
def get_velocity_model(grid, t, cmap, clim_max, show_gridlines):
    pulse = np.abs(np.sin(t)) + 0.5
    display_grid = grid.copy(deep=False) 
    
    if "velocity" not in display_grid.array_names:
        display_grid["velocity"] = np.random.rand(display_grid.n_points, 3)
    display_grid["display_vel"] = display_grid["velocity"] * pulse

    slice_plane = display_grid.slice(normal='z', origin=(0, 0, 0.5))

    # CRITICAL CHANGE: Increased window_size to 1600x900 (Widescreen)
    plotter = pv.Plotter(window_size=[1600, 900])
    plotter.set_background("#000000")
    
    sargs = dict(title="Velocity (m/s)", title_font_size=16, label_font_size=14,
                 vertical=False, position_x=0.2, position_y=0.05, width=0.6, height=0.08,
                 color="white", font_family="arial") 

    plotter.add_mesh(slice_plane, scalars="display_vel", cmap=cmap, clim=[0, clim_max], 
                     opacity=1.0, show_scalar_bar=True, scalar_bar_args=sargs)
    
    if show_gridlines:
        plotter.show_grid(color='gray', xtitle="Length", ytitle="Width", ztitle="Height",
                          font_size=12, grid=False, location='outer')
    else:
        plotter.add_axes(color='white')
    
    plotter.view_xy()
    return plotter

# --- ENGINE B: MESH (GREY WIREFRAME) ---
def get_mesh_model(grid):
    # CRITICAL CHANGE: Widescreen Resolution
    plotter = pv.Plotter(window_size=[1600, 900])
    plotter.set_background("#000000") 
    
    plotter.add_mesh(grid, style='wireframe', color="#444444", opacity=0.3, line_width=1)
    
    plotter.add_axes(color='white')
    plotter.show_grid(color='gray', location='outer')
    plotter.view_isometric()
    return plotter

# --- ENGINE C: GRAPH ---
# --- ENGINE C: PROFESSIONAL PLOTLY CHART ---
def get_mixing_graph(current_ratio):
    # 1. Generate Data
    x = np.linspace(0, 100, 100)
    y = 0.05 * (x - 50)**2 + 10
    current_y = 0.05 * (current_ratio - 50)**2 + 10
    
    # 2. Create Plotly Figure
    fig = go.Figure()

    # --- LAYER 1: The "Optimal Zone" Shading ---
    fig.add_hrect(
        y0=0, y1=12, 
        line_width=0, fillcolor="#00FF7F", opacity=0.1,
        annotation_text="OPTIMAL ZONE", annotation_position="top right",
        annotation_font_color="#00FF7F",
        annotation_font_size=16  # Larger text for large screen
    )

    # --- LAYER 2: The Main Curve ---
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode='lines',
        name='Mixing Profile',
        line=dict(color='#00FFFF', width=5), # Thicker line for large screen
        fill='tozeroy', 
        fillcolor='rgba(0, 255, 255, 0.1)' 
    ))

    # --- LAYER 3: The Current Point ---
    fig.add_trace(go.Scatter(
        x=[current_ratio], y=[current_y],
        mode='markers',
        name='Current Setpoint',
        marker=dict(color='#FF00FF', size=25, line=dict(color='white', width=3)), # Larger marker
        hovertemplate="Ratio: %{x}%<br>Time: %{y:.1f} min"
    ))

    # --- LAYER 4: Reference Lines ---
    fig.add_shape(type="line",
        x0=current_ratio, y0=0, x1=current_ratio, y1=current_y,
        line=dict(color="#FF00FF", width=2, dash="dot")
    )

    # 3. Professional Layout Formatting (FULL SCREEN TWEAKS)
    fig.update_layout(
        title=dict(text="<b>Process Homogeneity Curve</b>", font=dict(size=24, color='white')),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        
        # --- THE FIX: MAKE IT TALL ---
        height=800,  # Increased from 350 to 800 pixels
        autosize=True,
        
        # Minimized margins to push graph to the edges
        margin=dict(l=50, r=50, t=80, b=50),
        
        # Axis Styling (Larger Fonts)
        xaxis=dict(
            title="Fluid A Proportion (%)", 
            title_font=dict(size=18),
            tickfont=dict(size=14),
            showgrid=True, gridcolor='#333333', 
            zeroline=False, range=[0, 100]
        ),
        yaxis=dict(
            title="Mixing Time (min)", 
            title_font=dict(size=18),
            tickfont=dict(size=14),
            showgrid=True, gridcolor='#333333', 
            zeroline=False
        ),
        showlegend=False 
    )

    return fig, current_y

# ==========================================
# 5. MAIN APP
# ==========================================
st.title("Mixing Process Digital Twin")

grid = load_mesh()
tab1, tab2, tab3 = st.tabs(["Velocity Field", "Analytics", "Geometry Check"])

# --- TAB 1: FULL SCREEN VELOCITY ---
with tab1:
    # No text above, just straight to the plot for max space
    plotter_vel = get_velocity_model(grid, time_step, cmap_choice, v_max, show_bg_grid)
    # The key ensures Streamlit doesn't reload unnecessarily
    key_vel = f"vel_{fluid_ratio}_{time_step}_{cmap_choice}_{v_max}_{show_bg_grid}"
    stpyvista(plotter_vel, key=key_vel)

# --- TAB 2: ANALYTICS ---
# --- TAB 2: ANALYTICS ---
with tab2:
    st.markdown("#### Operational KPI Dashboard")
    
    # 1. Metrics (Top Row)
    fig, mixing_time = get_mixing_graph(fluid_ratio)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Predicted Time", f"{mixing_time:.1f} min")
    kpi2.metric("Avg Velocity", f"{(1.2 + np.sin(time_step)*0.2):.2f} m/s")
    kpi3.metric("Homogeneity", "98.5%")
    kpi4.metric("Power Draw", f"{(12.5 + fluid_ratio/100):.1f} kW")
    
    st.markdown("---") # Visual separator
    
    # 2. Graph (Fills the rest of the page)
    # The 'height=800' inside the function handles the vertical size.
    # 'use_container_width=True' handles the horizontal size.
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: FULL SCREEN MESH ---
with tab3:
    # 1. THE PLOT (Full Width)
    plotter_mesh = get_mesh_model(grid)
    stpyvista(plotter_mesh, key="mesh_view_widescreen")
    
    # 2. THE STATS (Below, so they don't squeeze the plot width)
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Elements", f"{grid.n_cells:,}")
    c2.metric("Total Nodes", f"{grid.n_points:,}")
    c3.info("Grey Wireframe Mode Active")