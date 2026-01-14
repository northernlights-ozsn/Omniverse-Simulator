import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. Setup & Session State
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="Omniverse Simulator Pro v4.3")

# Initialize Parameters
if 'draw_params' not in st.session_state:
    st.session_state['draw_params'] = {
        'shape_type': 'Torus', 'R_base': 10.0, 'r_tube': 3.0, 'h_cylinder': 20.0,
        'outer_scale': 1.0, 'inner_scale': 0.95,
        'segments_main': 24, 'segments_sub': 18, 'smoothness': 100,
        'bg_color': '#000000',
        'show_bb': True, 'bb_shape': 'circle', 'bb_size': 10.0, 'bb_color': '#FFFF00',
        'show_surf': True, 'surf_color': '#00A2E8', 'surf_opacity': 0.3,
        'outer_color': '#00A2E8', 'lw_outer': 1.2,
        'inner_color': '#FFAEC9', 'lw_inner': 1.0,
        'wire_start': 0.0, 'wire_span': 360.0, 'surf_start': 0.0, 'surf_span': 270.0,
        'camera_mode': 'Overview', 'rot_x': 0, 'rot_y': 0, 'rot_z': 0
    }

COLOR_PALETTE = {
    "Black": "#000000", "Dark Gray": "#7F7F7F", "Dark Red": "#880015", "Red": "#ED1C24",
    "Orange": "#FF7F27", "Gold": "#FFF200", "Yellow": "#EFE4B0", "Green": "#22B14C",
    "Turquoise": "#00A2E8", "Indigo": "#3F48CC", "White": "#FFFFFF", "Light Gray": "#C3C3C3",
    "Brown": "#B97A57", "Rose": "#FFAEC9", "Light Gold": "#FFC90E", "Light Yellow": "#FEF200",
    "Light Green": "#B5E61D", "Light Blue": "#99D9EA", "Blue Gray": "#7092BE", "Lavender": "#C8BFE7"
}
COLOR_KEYS = list(COLOR_PALETTE.keys()) + ["Custom"]

# ---------------------------------------------------------
# 2. UI Helpers & Callbacks
# ---------------------------------------------------------
def color_ui(label, key_suffix, default_key="Custom", default_hex="#00FFFF"):
    st.caption(f"■ {label}")
    drop = st.selectbox(f"{label}", COLOR_KEYS, index=COLOR_KEYS.index(default_key), key=f"drop_{key_suffix}", label_visibility="collapsed")
    pick = default_hex
    if drop == "Custom":
        pick = st.color_picker(f"Pick {label}", default_hex, key=f"pick_{key_suffix}")
    
    sync = False
    if label not in ["Background", "Singularity"]:
        sync = st.checkbox(f"Sync Background", key=f"sync_{key_suffix}")
    return drop, pick, sync

def resolve_color(drop, pick, sync, bg_hex):
    if sync: return bg_hex
    if drop == "Custom": return pick
    return COLOR_PALETTE.get(drop, pick)

# --- Callbacks for Synchronization ---
def update_from_slider(key_base):
    # Slider changed -> Update Box and Master State
    val = st.session_state[f"{key_base}_s"]
    st.session_state[key_base] = float(val)
    st.session_state[f"{key_base}_b"] = float(val)

def update_from_box(key_base):
    # Box changed -> Update Slider and Master State
    val = st.session_state[f"{key_base}_b"]
    st.session_state[key_base] = val
    st.session_state[f"{key_base}_s"] = int(val)

def angle_ui(label, key_base, def_val):
    st.caption(label)
    # Initialize session state keys if they don't exist
    if key_base not in st.session_state: st.session_state[key_base] = def_val
    if f"{key_base}_s" not in st.session_state: st.session_state[f"{key_base}_s"] = int(def_val)
    if f"{key_base}_b" not in st.session_state: st.session_state[f"{key_base}_b"] = float(def_val)

    # Slider (Integer step)
    st.slider(
        f"{label} Slider", 0, 360, key=f"{key_base}_s", step=1, 
        on_change=update_from_slider, args=(key_base,), label_visibility="collapsed"
    )
    
    # Box (Float precision) - Stacked vertically
    st.number_input(
        f"{label} Box", 0.0, 360.0, key=f"{key_base}_b", step=0.01, format="%.2f",
        on_change=update_from_box, args=(key_base,), label_visibility="collapsed"
    )
    
    return st.session_state[key_base]

# ---------------------------------------------------------
# 3. Sidebar Construction
# ---------------------------------------------------------
st.sidebar.title("Omniverse Settings")
tab1, tab2, tab3 = st.sidebar.tabs(["Shape", "Color & Light", "View & Cut"])

# === Tab 1: Shape ===
with tab1:
    st.header("■ Basic Shape")
    ui_shape = st.selectbox("Type", ["Torus", "Sphere", "Cylinder"], index=0)
    
    with st.expander("Size Settings", expanded=True):
        ui_R = st.number_input("Radius (R)", value=10.000, step=0.100, format="%.3f")
        ui_r, ui_h = 3.0, 20.0
        if ui_shape == "Torus":
            ui_r = st.number_input("Tube Radius (r)", value=3.000, step=0.100, format="%.3f")
        elif ui_shape == "Cylinder":
            ui_h = st.number_input("Height (h)", value=20.000, step=1.000, format="%.3f")

    with st.expander("Layer Scale", expanded=True):
        ui_out_sc = st.number_input("Outer Scale", value=1.000, step=0.001, format="%.3f")
        ui_in_sc = st.number_input("Inner Scale", value=0.950, step=0.001, format="%.3f")

    with st.expander("Mesh Density", expanded=False):
        def_main = int(st.session_state['draw_params'].get('segments_main', 24))
        def_sub = int(st.session_state['draw_params'].get('segments_sub', 18))
        def_smooth = int(st.session_state['draw_params'].get('smoothness', 100))

        st.caption("Main Segments")
        ui_seg_m = st.slider("Main Segments", 10, 360, def_main, step=1, label_visibility="collapsed")
        
        st.caption("Sub Segments")
        ui_seg_s = st.slider("Sub Segments", 4, 360, def_sub, step=1, label_visibility="collapsed")
        
        st.caption("Smoothness")
        ui_smooth = st.slider("Smoothness", 50, 360, def_smooth, step=1, label_visibility="collapsed")

# === Tab 2: Color & Light ===
with tab2:
    with st.expander("Singularity (Big Bang)", expanded=False):
        ui_show_bb = st.checkbox("Show Singularity", value=True)
        ui_bb_shape, ui_bb_size = "circle", 10.0
        ui_bb_d, ui_bb_p = "Yellow", "#FFFF00"
        if ui_show_bb:
            ui_bb_shape = st.selectbox("Shape", ["circle", "square", "diamond", "cross", "x"])
            ui_bb_size = st.number_input("Size", value=10.0, step=1.0)
            ui_bb_d, ui_bb_p, _ = color_ui("Singularity", "bb", "Yellow", "#FFFF00")

    with st.expander("Surface Skin", expanded=True):
        ui_show_surf = st.checkbox("Show Surface", value=True)
        ui_sf_d, ui_sf_p, ui_sf_sync, ui_sf_op = "Turquoise", "#00A2E8", False, 0.3
        if ui_show_surf:
            ui_sf_d, ui_sf_p, ui_sf_sync = color_ui("Surface", "sf", "Turquoise", "#00A2E8")
            st.caption("Opacity")
            if 'op_val' not in st.session_state: st.session_state.op_val = 0.3
            op_s = st.slider("Op S", 0.0, 1.0, st.session_state.op_val, 0.1, key="op_s", label_visibility="collapsed")
            op_b = st.number_input("Op B", 0.0, 1.0, st.session_state.op_val, 0.001, format="%.3f", key="op_b", label_visibility="collapsed")
            st.session_state.op_val = op_b if op_b != st.session_state.op_val else op_s
            ui_sf_op = st.session_state.op_val

    with st.expander("Wireframe", expanded=True):
        ui_out_d, ui_out_p, ui_out_sync = color_ui("Outer Wire", "out", "Turquoise", "#00A2E8")
        ui_lw_out = st.number_input("Outer Width", value=1.2, step=0.1)
        st.markdown("---")
        ui_in_d, ui_in_p, ui_in_sync = color_ui("Inner Wire", "in", "Rose", "#FFAEC9")
        ui_lw_in = st.number_input("Inner Width", value=1.0, step=0.1)

    with st.expander("Background", expanded=True):
        ui_bg_d, ui_bg_p, _ = color_ui("Background", "bg", "Black", "#000000")

# === Tab 3: View & Cut ===
with tab3:
    with st.expander("Section Cut", expanded=True):
        ui_w_st = angle_ui("Wire Start (°)", "w_st", 0.0)
        ui_w_sp = angle_ui("Wire Span (°)", "w_sp", 360.0)
        st.markdown("---")
        ui_s_st = angle_ui("Surface Start (°)", "s_st", 0.0)
        ui_s_sp = angle_ui("Surface Span (°)", "s_sp", 270.0)

    with st.expander("Camera View", expanded=True):
        ui_cam = st.radio("Mode", ["Overview", "POV"])
        st.caption("Manual Rotation (0-360°)")
        
        # State retrieval
        def_rx = int(st.session_state['draw_params'].get('rot_x', 0))
        def_ry = int(st.session_state['draw_params'].get('rot_y', 0))
        def_rz = int(st.session_state['draw_params'].get('rot_z', 0))

        st.caption("Rotate X")
        ui_rx = st.slider("Rot X", 0, 360, def_rx, 1, key="sl_rx", label_visibility="collapsed")
        
        st.caption("Rotate Y")
        ui_ry = st.slider("Rot Y", 0, 360, def_ry, 1, key="sl_ry", label_visibility="collapsed")
        
        st.caption("Rotate Z")
        ui_rz = st.slider("Rot Z", 0, 360, def_rz, 1, key="sl_rz", label_visibility="collapsed")

# ---------------------------------------------------------
# 4. Apply Logic
# ---------------------------------------------------------
st.sidebar.markdown("---")
def apply_changes():
    bg = resolve_color(ui_bg_d, ui_bg_p, False, "#000000")
    st.session_state['draw_params'] = {
        'shape_type': ui_shape,
        'R_base': ui_R, 'r_tube': ui_r, 'h_cylinder': ui_h,
        'outer_scale': ui_out_sc, 'inner_scale': ui_in_sc,
        'segments_main': int(ui_seg_m), 
        'segments_sub': int(ui_seg_s), 
        'smoothness': int(ui_smooth),
        'bg_color': bg,
        'show_bb': ui_show_bb, 'bb_shape': ui_bb_shape, 'bb_size': ui_bb_size,
        'bb_color': resolve_color(ui_bb_d, ui_bb_p, False, bg),
        'show_surf': ui_show_surf,
        'surf_color': resolve_color(ui_sf_d, ui_sf_p, ui_sf_sync, bg),
        'surf_opacity': ui_sf_op,
        'outer_color': resolve_color(ui_out_d, ui_out_p, ui_out_sync, bg),
        'lw_outer': ui_lw_out,
        'inner_color': resolve_color(ui_in_d, ui_in_p, ui_in_sync, bg),
        'lw_inner': ui_lw_in,
        'wire_start': ui_w_st, 'wire_span': ui_w_sp,
        'surf_start': ui_s_st, 'surf_span': ui_s_sp,
        'camera_mode': ui_cam, 
        'rot_x': int(ui_rx), 
        'rot_y': int(ui_ry), 
        'rot_z': int(ui_rz)
    }

st.sidebar.button("Apply Changes", on_click=apply_changes, type="primary", use_container_width=True)

# ---------------------------------------------------------
# 5. Drawing Logic
# ---------------------------------------------------------
P = st.session_state['draw_params']

try:
    def get_coords(type_str, scale, u, v):
        scale = float(scale)
        if type_str == "Torus":
            R, r = float(P['R_base']), float(P['r_tube']) * scale
            x = (R + r * np.cos(v)) * np.cos(u)
            y = (R + r * np.cos(v)) * np.sin(u)
            z = r * np.sin(v)
        elif type_str == "Sphere":
            R = float(P['R_base']) * scale
            x = R * np.sin(v) * np.cos(u)
            y = R * np.sin(v) * np.sin(u)
            z = R * np.cos(v)
        elif type_str == "Cylinder":
            R, H = float(P['R_base']) * scale, float(P['h_cylinder'])
            z_g = np.linspace(-H/2, H/2, len(v))
            z_m, t_m = np.meshgrid(z_g, u)
            x = R * np.cos(t_m)
            y = R * np.sin(t_m)
            z = z_m
            return x, y, z
        else:
            return np.zeros_like(u), np.zeros_like(u), np.zeros_like(u)
        
        return np.broadcast_arrays(x, y, z)

    def rot_matrix(ax, ay, az):
        ax, ay, az = np.radians(ax), np.radians(ay), np.radians(az)
        Rx = np.array([[1, 0, 0], [0, np.cos(ax), -np.sin(ax)], [0, np.sin(ax), np.cos(ax)]])
        Ry = np.array([[np.cos(ay), 0, np.sin(ay)], [0, 1, 0], [-np.sin(ay), 0, np.cos(ay)]])
        Rz = np.array([[np.cos(az), -np.sin(az), 0], [np.sin(az), np.cos(az), 0], [0, 0, 1]])
        return Rz @ Ry @ Rx

    def apply_rot(x, y, z, m):
        pts = np.stack([x, y, z], axis=-1)
        rot_pts = pts @ m.T
        return rot_pts[..., 0], rot_pts[..., 1], rot_pts[..., 2]

    rm = rot_matrix(P['rot_x'], P['rot_y'], P['rot_z'])
    fig = go.Figure()

    # Surface
    if P['show_surf']:
        sm = int(P['smoothness'])
        us = np.radians(np.linspace(P['surf_start'], P['surf_start']+P['surf_span'], sm))
        if P['shape_type'] == "Sphere":
            vs = np.linspace(0, np.pi, sm)
            us, vs = np.meshgrid(us, vs)
        elif P['shape_type'] == "Cylinder":
            vs = np.linspace(0, 1, sm)
        else: # Torus
            vs = np.linspace(0, 2*np.pi, sm)
            us, vs = np.meshgrid(us, vs)
        
        xs, ys, zs = get_coords(P['shape_type'], P['outer_scale'], us, vs)
        rxs, rys, rzs = apply_rot(xs.flatten(), ys.flatten(), zs.flatten(), rm)
        fig.add_trace(go.Surface(
            x=rxs.reshape(xs.shape), y=rys.reshape(ys.shape), z=rzs.reshape(zs.shape), 
            surfacecolor=np.ones_like(xs), colorscale=[[0, P['surf_color']], [1, P['surf_color']]], 
            showscale=False, opacity=P['surf_opacity'], 
            contours=dict(x=dict(highlight=False), y=dict(highlight=False), z=dict(highlight=False)), 
            hoverinfo='none', lighting=dict(ambient=0.7, diffuse=0.8, roughness=0.5)
        ))

    # Wireframe
    def add_wire(scale, color, width, start, span):
        sm = int(P['smoothness'])
        n_seg = int(P['segments_main'] * (span / 360)) + 1
        uw = np.radians(np.linspace(start, start+span, max(2, n_seg)))
        us = np.radians(np.linspace(start, start+span, sm))
        
        if P['shape_type'] == "Sphere":
            vw = np.linspace(0, np.pi, int(P['segments_sub']) + 1)
            vs = np.linspace(0, np.pi, sm)
            # U lines
            for u in uw:
                x, y, z = get_coords(P['shape_type'], scale, u, vs)
                rx, ry, rz = apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False, hoverinfo='none'))
            # V lines
            for v in vw[1:-1]:
                x, y, z = get_coords(P['shape_type'], scale, us, v)
                rx, ry, rz = apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False, hoverinfo='none'))
        
        elif P['shape_type'] == "Cylinder":
            vw = np.linspace(-float(P['h_cylinder'])/2, float(P['h_cylinder'])/2, int(P['segments_sub']) + 1)
            vs = np.linspace(-float(P['h_cylinder'])/2, float(P['h_cylinder'])/2, sm)
            # U lines
            for u in uw:
                x, y, z = get_coords(P['shape_type'], scale, u, vs)
                rx, ry, rz = apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False, hoverinfo='none'))
            # V lines
            for v in vw:
                R = float(P['R_base']) * scale
                x = R * np.cos(us)
                y = R * np.sin(us)
                z = np.full_like(us, v)
                rx, ry, rz = apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False, hoverinfo='none'))
        
        else: # Torus
            vw = np.linspace(0, 2*np.pi, int(P['segments_sub']) + 1)
            vs = np.linspace(0, 2*np.pi, sm)
            for u in uw:
                x, y, z = get_coords(P['shape_type'], scale, u, vs)
                rx, ry, rz = apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False, hoverinfo='none'))
            for v in vw[:-1]:
                x, y, z = get_coords(P['shape_type'], scale, us, v)
                rx, ry, rz = apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False, hoverinfo='none'))

    add_wire(P['inner_scale'], P['inner_color'], P['lw_inner'], P['wire_start'], P['wire_span'])
    add_wire(P['outer_scale'], P['outer_color'], P['lw_outer'], P['wire_start'], P['wire_span'])

    # Big Bang
    if P['show_bb']:
        if P['bb_shape'] == "circle":
            r_bb = P['bb_size'] * 0.05
            ub, vb = np.meshgrid(np.linspace(0, 2*np.pi, 20), np.linspace(0, np.pi, 20))
            xb = r_bb * np.sin(vb) * np.cos(ub)
            yb = r_bb * np.sin(vb) * np.sin(ub)
            zb = r_bb * np.cos(vb)
            fig.add_trace(go.Surface(
                x=xb, y=yb, z=zb, surfacecolor=np.ones_like(xb), 
                colorscale=[[0, P['bb_color']], [1, P['bb_color']]], 
                showscale=False, opacity=1.0, hoverinfo='none'
            ))
        else:
            fig.add_trace(go.Scatter3d(
                x=[0], y=[0], z=[0], mode='markers', 
                marker=dict(size=P['bb_size'], color=P['bb_color'], symbol=P['bb_shape'], opacity=1.0), 
                name="Big Bang"
            ))

    # Camera
    eye, center = dict(x=1.6, y=1.6, z=1.6), dict(x=0, y=0, z=0)
    if "POV" in P['camera_mode']:
        if P['shape_type'] == "Sphere": eye = dict(x=0.01, y=0, z=0)
        elif P['shape_type'] == "Cylinder": eye = dict(x=0, y=0, z=-0.4)
        else: eye = dict(x=0.05, y=0, z=0.01)

    fig.update_layout(
        scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False), bgcolor=P['bg_color'], aspectmode='data'), 
        paper_bgcolor=P['bg_color'], margin=dict(l=0, r=0, b=0, t=0), 
        scene_camera=dict(eye=eye, center=center), height=800
    )
    st.plotly_chart(fig, use_container_width=True, theme=None)

except Exception as e:
    st.error(f"Error: {e}")