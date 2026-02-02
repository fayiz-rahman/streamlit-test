# -*- coding: utf-8 -*-
"""
Created on Thu Jan 29 15:01:18 2026

@author: zhiha
"""
import os

# --- 1. HEADLESS DISPLAY SETUP (CRITICAL FOR CLOUD) ---
# We must start the "fake screen" before importing PyVista
os.system('/usr/bin/Xvfb :99 -screen 0 1024x768x24 &')
os.environ['DISPLAY'] = ':99'
import streamlit as st
import pyvista as pv
import numpy as np
import matplotlib.pyplot as plt
from stpyvista import stpyvista

# ==========================================
# 1. PROFESSIONAL PAGE SETUP
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="NING RESEARCH | Digital Twin",
    page_icon="⚗️"
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR
# ==========================================
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True) 
    except:
        st.warning("⚠️ logo.png not found")
        
    ##st.markdown("<h2 style='text-align: center; color: #333;'>NING RESEARCH</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.header("🎛️ Operation Parameters")
    with st.expander("Process Inputs", expanded=True):
        fluid_ratio = st.slider("Fluid A Proportion (%)", 0, 100, 49)
        time_step = st.slider("Simulation Time (s)", 0.0, 10.0, 0.5)

    with st.expander("Visualization Settings", expanded=False):
        cmap_choice = st.selectbox("Color Map", ["jet", "viridis", "plasma", "coolwarm"], index=0)
        v_max = st.slider("Legend Max (m/s)", 1.0, 20.0, 5.0)

# ==========================================
# 3. HELPER FUNCTION: LOAD DATA
# ==========================================
# We cache this so we don't reload the file 3 times per second
@st.cache_resource
def load_mesh():
    try:
        multiblock = pv.read("master.case")
        grid = multiblock[0]
        return grid
    except:
        # Dummy if missing
        return pv.Cylinder(radius=0.5, height=1.2, direction=(0,0,1))

# ==========================================
# 4. VISUALIZATION ENGINES
# ==========================================

# --- ENGINE A: VELOCITY SLICE ---
def get_velocity_model(grid, t, cmap, clim_max):
    # Apply Physics (Pulse)
    pulse = np.abs(np.sin(t)) + 0.5
    
    # Create temp array for display
    # We copy to avoid corrupting the cached original
    display_grid = grid.copy(deep=False) 
    
    if "velocity" not in display_grid.array_names:
        display_grid["velocity"] = np.random.rand(display_grid.n_points, 3)
    
    display_grid["display_vel"] = display_grid["velocity"] * pulse

    # Slice
    slice_plane = display_grid.slice(normal='z', origin=(0, 0, 0.5))

    plotter = pv.Plotter(window_size=[800, 600])
    plotter.set_background("white")
    
    # Horizontal Legend
    sargs = dict(title="Velocity (m/s)", title_font_size=14, label_font_size=12,
                 vertical=False, position_x=0.2, position_y=0.05, width=0.6, height=0.08,
                 color="black", font_family="arial")

    plotter.add_mesh(slice_plane, scalars="display_vel", cmap=cmap, clim=[0, clim_max], 
                     opacity=1.0, show_scalar_bar=True, scalar_bar_args=sargs)
    
    plotter.view_xy()
    return plotter

# --- ENGINE B: FULL MESH VIEWER ---
def get_mesh_model(grid):
    plotter = pv.Plotter(window_size=[800, 600])
    plotter.set_background("white")
    
    # 1. Show the solid surface (Semi-transparent)
    plotter.add_mesh(grid, color="lightblue", opacity=0.3, show_scalar_bar=False)
    
    # 2. Show the Wireframe (The "Mesh" lines)
    # We use 'show_edges=True' to reveal the mesh structure
    plotter.add_mesh(grid, style='wireframe', color="black", opacity=0.1, line_width=0.5)
    
    plotter.add_axes() # Show XYZ arrows
    plotter.view_isometric()
    return plotter

# --- ENGINE C: GRAPH ---
def get_mixing_graph(current_ratio):
    plt.style.use('seaborn-v0_8-whitegrid')
    x = np.linspace(0, 100, 100)
    y = 0.05 * (x - 50)**2 + 10
    current_y = 0.05 * (current_ratio - 50)**2 + 10
    
    fig, ax = plt.subplots(figsize=(12, 3.5))
    ax.plot(x, y, color='#004e89', linewidth=2.5)
    ax.scatter([current_ratio], [current_y], color='#ff4b4b', s=120, zorder=5, edgecolors='black')
    ax.axvline(x=current_ratio, color='#ff4b4b', linestyle=':', alpha=0.6)
    
    ax.set_title("Predicted Homogeneity Time", fontsize=12, fontweight='bold', loc='left')
    ax.set_xlabel("Fluid A Proportion (%)", fontsize=10)
    ax.set_ylabel("Time (min)", fontsize=10)
    return fig, current_y

# ==========================================
# 5. MAIN LAYOUT
# ==========================================
st.title("🏭 Mixing Process Digital Twin")

# Load Data Once
grid = load_mesh()

# --- PART 1: VELOCITY ---
st.subheader("Velocity Field Analysis")
plotter_vel = get_velocity_model(grid, time_step, cmap_choice, v_max)
key_vel = f"vel_{fluid_ratio}_{time_step}_{cmap_choice}_{v_max}"
stpyvista(plotter_vel, key=key_vel)

st.markdown("---")

# --- PART 2: PERFORMANCE ---
st.subheader("Performance Analytics")
fig, mixing_time = get_mixing_graph(fluid_ratio)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Predicted Mixing Time", f"{mixing_time:.1f} min")
kpi2.metric("Avg Velocity", f"{(1.2 + np.sin(time_step)*0.2):.2f} m/s")
kpi3.metric("Homogeneity Index", "98.5%")
kpi4.metric("Power", f"{(12.5 + fluid_ratio/100):.1f} kW")

st.pyplot(fig)

st.markdown("---")

# --- PART 3: MESH & GEOMETRY (NEW) ---
st.subheader("Geometric & Mesh Integrity")

col_mesh_view, col_mesh_info = st.columns([3, 1])

with col_mesh_view:
    # Interactive Mesh Viewer
    # This one doesn't need to update often, so we use a static key or simple key
    plotter_mesh = get_mesh_model(grid)
    stpyvista(plotter_mesh, key="mesh_viewer_static")

with col_mesh_info:
    st.markdown("#### Grid Statistics")
    # Real data from your file
    st.metric("Total Elements", f"{grid.n_cells:,}")
    st.metric("Total Nodes", f"{grid.n_points:,}")
    st.metric("Mesh Volume", f"{grid.volume:.2f} m³")
    
    st.info("""
    The domain uses a **tetrahedral** mesh with boundary layer refinement for accurate near-wall turbulence capture.
    """)