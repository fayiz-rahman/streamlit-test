import streamlit as st
import pyvista as pv
import os

# --- 1. HEADLESS MODE CONFIG ---
# This fixes the segmentation fault on cloud
pv.start_xvfb()

# --- 2. IMPORT REST ---
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from stpyvista import stpyvista
import plotly.graph_objects as go

# ==========================================
# 3. PAGE CONFIG & DEEP DARK CSS
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="NING RESEARCH | Digital Twin",
    page_icon="⚗️",
    initial_sidebar_state="expanded"
)

# FORCE COMPLETE BLACK THEME
st.markdown("""
<style>
    /* 1. Main Background & Text */
    .stApp { 
        background-color: #000000; 
        color: #FFFFFF;
    }
    
    /* 2. Hide the Top White Header Bar */
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0); /* Transparent */
        visibility: hidden; /* Or set to visible if you need the menu */
    }
    
    /* 3. Sidebar Background */
    section[data-testid="stSidebar"] {
        background-color: #050505; /* Almost black */
        border-right: 1px solid #333;
    }

    /* 4. Fix Inputs (Sliders/Expanders) to match Dark Theme */
    .stSelectbox, .stSlider, .stMarkdown {
        color: white !important;
    }
    
    /* Expander Backgrounds (Process Inputs Box) */
    .streamlit-expanderHeader {
        background-color: #111111 !important;
        color: white !important;
        border: 1px solid #333;
    }
    div[data-testid="stExpander"] {
        background-color: #111111 !important;
        border: none;
    }

    /* 5. Metrics & Text Colors */
    h1, h2, h3, h4, h5, h6, span { color: #FFFFFF !important; }
    div[data-testid="stMetricValue"] { color: #00FF7F !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #888888 !important; }
    
    /* 6. Remove Padding for Full Screen */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* 7. Maximize 3D Viewers */
    iframe { width: 100% !important; height: 80vh !important; }

</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00FFFF;'>Yottakern</h2>", unsafe_allow_html=True)
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
# 5. HELPER FUNCTION
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
# 6. VISUALIZATION ENGINES
# ==========================================

# --- ENGINE A: VELOCITY ---
def get_velocity_model(grid, t, cmap, clim_max, show_gridlines):
    pulse = np.abs(np.sin(t)) + 0.5
    display_grid = grid.copy(deep=False) 
    
    if "velocity" not in display_grid.array_names:
        display_grid["velocity"] = np.random.rand(display_grid.n_points, 3)
    display_grid["display_vel"] = display_grid["velocity"] * pulse

    slice_plane = display_grid.slice(normal='z', origin=(0, 0, 0.5))

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

# --- ENGINE B: MESH ---
def get_mesh_model(grid):
    plotter = pv.Plotter(window_size=[1600, 900])
    plotter.set_background("#000000") 
    plotter.add_mesh(grid, style='wireframe', color="#444444", opacity=0.3, line_width=1)
    plotter.add_axes(color='white')
    plotter.show_grid(color='gray', location='outer')
    plotter.view_isometric()
    return plotter

# --- ENGINE C: PLOTLY GRAPH ---
def get_mixing_graph(current_ratio):
    x = np.linspace(0, 100, 100)
    y = 0.05 * (x - 50)**2 + 10
    current_y = 0.05 * (current_ratio - 50)**2 + 10
    
    fig = go.Figure()

    # Optimal Zone
    fig.add_hrect(
        y0=0, y1=12, 
        line_width=0, fillcolor="#00FF7F", opacity=0.1,
        annotation_text="OPTIMAL ZONE", annotation_position="top right",
        annotation_font_color="#00FF7F", annotation_font_size=16
    )

    # Main Curve
    fig.add_trace(go.Scatter(
        x=x, y=y, mode='lines', name='Mixing Profile',
        line=dict(color='#00FFFF', width=5), 
        fill='tozeroy', fillcolor='rgba(0, 255, 255, 0.1)' 
    ))

    # Current Point
    fig.add_trace(go.Scatter(
        x=[current_ratio], y=[current_y], mode='markers', name='Current Setpoint',
        marker=dict(color='#FF00FF', size=25, line=dict(color='white', width=3)), 
        hovertemplate="Ratio: %{x}%<br>Time: %{y:.1f} min"
    ))

    # Reference Line
    fig.add_shape(type="line", x0=current_ratio, y0=0, x1=current_ratio, y1=current_y,
        line=dict(color="#FF00FF", width=2, dash="dot")
    )

    fig.update_layout(
        title=dict(text="<b>Process Homogeneity Curve</b>", font=dict(size=24, color='white')),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        height=800, autosize=True,
        margin=dict(l=50, r=50, t=80, b=50),
        xaxis=dict(title="Fluid A Proportion (%)", title_font=dict(size=18), tickfont=dict(size=14), showgrid=True, gridcolor='#333333', zeroline=False, range=[0, 100]),
        yaxis=dict(title="Mixing Time (min)", title_font=dict(size=18), tickfont=dict(size=14), showgrid=True, gridcolor='#333333', zeroline=False),
        showlegend=False 
    )
    return fig, current_y

# ==========================================
# 7. MAIN APP
# ==========================================
st.title("Mixing Process Digital Twin")

grid = load_mesh()
tab1, tab2, tab3 = st.tabs(["Velocity Field", "Analytics", "Geometry Check"])

# --- TAB 1 ---
with tab1:
    plotter_vel = get_velocity_model(grid, time_step, cmap_choice, v_max, show_bg_grid)
    key_vel = f"vel_{fluid_ratio}_{time_step}_{cmap_choice}_{v_max}_{show_bg_grid}"
    stpyvista(plotter_vel, key=key_vel)

# --- TAB 2 ---
with tab2:
    st.markdown("#### Operational KPI Dashboard")
    fig, mixing_time = get_mixing_graph(fluid_ratio)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Predicted Time", f"{mixing_time:.1f} min")
    kpi2.metric("Avg Velocity", f"{(1.2 + np.sin(time_step)*0.2):.2f} m/s")
    kpi3.metric("Homogeneity", "98.5%")
    kpi4.metric("Power Draw", f"{(12.5 + fluid_ratio/100):.1f} kW")
    st.markdown("---") 
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 3 ---
with tab3:
    plotter_mesh = get_mesh_model(grid)
    stpyvista(plotter_mesh, key="mesh_view_widescreen")
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Elements", f"{grid.n_cells:,}")
    c2.metric("Total Nodes", f"{grid.n_points:,}")
    c3.info("Grey Wireframe Mode Active")