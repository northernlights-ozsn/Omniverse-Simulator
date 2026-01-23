import streamlit as st
import auth_manager as am
import ui_components as ui
import geometry_engine as ge
import numpy as np
import plotly.graph_objects as go

# --- Auth ---
if not am.check_password():
    st.stop()

st.set_page_config(layout="wide", page_title="Project: CORE Simulator")

# --- Custom CSS ---
st.markdown("""
    <style>
        section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
        section[data-testid="stSidebar"] h1 { margin-bottom: 0.5rem !important; }
        section[data-testid="stSidebar"] hr { margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; }
        section[data-testid="stSidebar"] .stVerticalBlock > div { gap: 0.5rem !important; }
        section[data-testid="stSidebar"] .stCaption { margin-bottom: 0.2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- Default Params (Updated) ---
DEFAULTS = {
    'shape_type': 'Torus', 'R_base': 10.0, 'r_tube': 3.0, 'h_cylinder': 20.0,
    'outer_scale': 1.0, 'inner_scale': 0.95,
    'segments_main': 24.0, 'segments_sub': 18.0, 'smoothness': 100.0,
    'bg_color': '#000000', 'show_bb': True, 'bb_size': 10.0, 'bb_color': '#FFFF00',
    'show_surf': True, 'surf_color': '#00A2E8', 'surf_opacity': 0.3,
    # New: Wireframe Toggles
    'show_out_wire': True, 'outer_color': '#00A2E8', 'lw_outer': 1.2,
    'show_in_wire': True, 'inner_color': '#FFAEC9', 'lw_inner': 1.0,
    'wire_start': 0.0, 'wire_span': 360.0, 'surf_start': 0.0, 'surf_span': 270.0,
    'camera_mode': 'Overview', 'rot_x': 0.0, 'rot_y': 0.0, 'rot_z': 0.0
}

# --- Expanded Palette (20 Colors) ---
PALETTE = {
    "Black": "#000000", "Dark Gray": "#7F7F7F", "Dark Red": "#880015", "Red": "#ED1C24",
    "Orange": "#FF7F27", "Gold": "#FFF200", "Yellow": "#EFE4B0", "Green": "#22B14C",
    "Turquoise": "#00A2E8", "Indigo": "#3F48CC", "White": "#FFFFFF", "Light Gray": "#C3C3C3",
    "Brown": "#B97A57", "Rose": "#FFAEC9", "Light Gold": "#FFC90E", "Light Yellow": "#FEF200",
    "Light Green": "#B5E61D", "Light Blue": "#99D9EA", "Blue Gray": "#7092BE", "Lavender": "#C8BFE7"
}

# --- State Management ---
if 'draw_params' not in st.session_state:
    loaded = am.load_settings()
    # 新しいパラメータ(show_out_wire等)が無い場合に備えてデフォルトとマージ
    current = DEFAULTS.copy()
    if loaded:
        current.update(loaded)
    st.session_state['draw_params'] = current

if 'presets' not in st.session_state:
    st.session_state['presets'] = {}

# ==========================================
# Sidebar Layout
# ==========================================

# --- 1. Preset Manager Section ---
st.sidebar.title("Preset Manager")

preset_list = ["Last Session"] + list(st.session_state.presets.keys())
selected_preset = st.sidebar.selectbox("Select Preset", preset_list, label_visibility="collapsed")

if st.sidebar.button("Load Preset", use_container_width=True):
    if selected_preset == "Last Session":
        loaded = am.load_settings()
        if loaded:
            current = DEFAULTS.copy()
            current.update(loaded)
            st.session_state.draw_params = current
            st.rerun()
    elif selected_preset in st.session_state.presets:
        st.session_state.draw_params = st.session_state.presets[selected_preset].copy()
        st.rerun()

if st.sidebar.button("Save Current as Preset", use_container_width=True):
    slot_no = len(st.session_state.presets) + 1
    p_name = f"#{slot_no} {st.session_state.draw_params['shape_type']}"
    st.session_state.presets[p_name] = st.session_state.draw_params.copy()
    st.sidebar.success(f"Saved: {p_name}")
    st.rerun()

st.sidebar.markdown("---")
reset_btn = st.sidebar.button("Reset to Factory Defaults", use_container_width=True)
st.sidebar.markdown("---")

# --- 2. CORE Settings Section ---
st.sidebar.title("CORE Settings")
apply_btn = st.sidebar.button("Apply Changes", type="primary", use_container_width=True)

# --- Tabs ---
tab1, tab2, tab3 = st.sidebar.tabs(["Shape", "Color & Light", "View & Cut"])

with tab1:
    st.header("■ Current Shape")
    ui_shape = st.selectbox("Type", ["Torus", "Sphere", "Cylinder"], 
                            index=["Torus", "Sphere", "Cylinder"].index(st.session_state.draw_params['shape_type']))
    
    with st.expander("Size Settings", expanded=True):
        ui_R = st.number_input("Radius (R)", value=float(st.session_state.draw_params['R_base']), step=0.1, format="%.3f")
        ui_r = st.number_input("Tube Radius (r)", value=float(st.session_state.draw_params.get('r_tube', 3.0)), step=0.1) if ui_shape == "Torus" else 3.0
        ui_h = st.number_input("Height (h)", value=float(st.session_state.draw_params.get('h_cylinder', 20.0)), step=1.0) if ui_shape == "Cylinder" else 20.0
    
    with st.expander("Layer Scale", expanded=True):
        ui_out_sc = st.number_input("Outer Scale", value=float(st.session_state.draw_params['outer_scale']), step=0.001, format="%.3f")
        ui_in_sc = st.number_input("Inner Scale", value=float(st.session_state.draw_params['inner_scale']), step=0.001, format="%.3f")

    with st.expander("Mesh Density (Synced)", expanded=True):
        ui_seg_m = ui.synced_ui("Main Segments", "seg_m", st.session_state.draw_params['segments_main'], 10, 360, step_s=1, fmt="%d")
        ui_seg_s = ui.synced_ui("Sub Segments", "seg_s", st.session_state.draw_params['segments_sub'], 4, 360, step_s=1, fmt="%d")
        ui_smooth = ui.synced_ui("Smoothness", "smooth", st.session_state.draw_params['smoothness'], 50, 360, step_s=1, fmt="%d")

with tab2:
    with st.expander("Singularity (Big Bang)", expanded=False):
        ui_show_bb = st.checkbox("Show", value=st.session_state.draw_params.get('show_bb', True))
        ui_bb_size = st.number_input("Scale (Size)", value=float(st.session_state.draw_params.get('bb_size', 10.0)), step=0.5)
        ui_bb_d, ui_bb_p, _ = ui.color_ui("Singularity", "bb", PALETTE, default_hex=st.session_state.draw_params.get('bb_color', '#FFFF00'))

    with st.expander("Surface Skin", expanded=True):
        ui_show_surf = st.checkbox("Show Surface", value=st.session_state.draw_params['show_surf'])
        ui_sf_d, ui_sf_p, ui_sf_sync = ui.color_ui("Surface", "sf", PALETTE, default_hex=st.session_state.draw_params['surf_color'])
        ui_sf_op = ui.synced_ui("Opacity", "sf_op", st.session_state.draw_params['surf_opacity'], 0.0, 1.0, step_s=0.1, step_b=0.01)

    with st.expander("Wireframe", expanded=True):
        # Outer Wire Checkbox
        ui_show_out = st.checkbox("Show Outer Wire", value=st.session_state.draw_params.get('show_out_wire', True))
        ui_out_d, ui_out_p, ui_out_sync = ui.color_ui("Outer Wire", "out", PALETTE, default_hex=st.session_state.draw_params['outer_color'])
        ui_lw_out = st.number_input("Outer Width", value=float(st.session_state.draw_params['lw_outer']))
        st.markdown("---")
        # Inner Wire Checkbox
        ui_show_in = st.checkbox("Show Inner Wire", value=st.session_state.draw_params.get('show_in_wire', True))
        ui_in_d, ui_in_p, ui_in_sync = ui.color_ui("Inner Wire", "in", PALETTE, default_hex=st.session_state.draw_params['inner_color'])
        ui_lw_in = st.number_input("Inner Width", value=float(st.session_state.draw_params['lw_inner']))

    with st.expander("Background", expanded=True):
        ui_bg_d, ui_bg_p, _ = ui.color_ui("Background", "bg", PALETTE, default_hex=st.session_state.draw_params['bg_color'])
with tab3:
    with st.expander("Section Cut", expanded=True):
        ui_w_st = ui.synced_ui("Wire Start", "w_st", st.session_state.draw_params['wire_start'], 0, 360)
        ui_w_sp = ui.synced_ui("Wire Span", "w_sp", st.session_state.draw_params['wire_span'], 0, 360)
        st.markdown("---")
        ui_s_st = ui.synced_ui("Surf Start", "s_st", st.session_state.draw_params['surf_start'], 0, 360)
        ui_s_sp = ui.synced_ui("Surf Span", "s_sp", st.session_state.draw_params['surf_span'], 0, 360)

    with st.expander("Camera & Rotation", expanded=True):
        ui_cam = st.radio("Mode", ["Overview", "POV"], index=["Overview", "POV"].index(st.session_state.draw_params['camera_mode']))
        ui_rx = ui.synced_ui("Rotate X", "rot_x_ui", st.session_state.draw_params['rot_x'], 0, 360)
        ui_ry = ui.synced_ui("Rotate Y", "rot_y_ui", st.session_state.draw_params['rot_y'], 0, 360)
        ui_rz = ui.synced_ui("Rotate Z", "rot_z_ui", st.session_state.draw_params['rot_z'], 0, 360)

# --- Logic Apply ---
if reset_btn:
    st.session_state.draw_params = DEFAULTS.copy()
    am.save_settings(DEFAULTS)
    st.rerun()

if apply_btn:
    new_params = st.session_state.draw_params.copy()
    # 背景色のロジック修正: ui.resolve_color を使用してドロップダウンの値を反映させる
    resolved_bg = ui.resolve_color(ui_bg_d, ui_bg_p, False, None, PALETTE)
    
    new_params.update({
        'shape_type': ui_shape, 'R_base': ui_R, 'r_tube': ui_r, 'h_cylinder': ui_h,
        'outer_scale': ui_out_sc, 'inner_scale': ui_in_sc,
        'segments_main': ui_seg_m, 'segments_sub': ui_seg_s, 'smoothness': ui_smooth,
        'bg_color': resolved_bg, 'show_bb': ui_show_bb, 'bb_size': ui_bb_size, 'bb_color': ui_bb_p,
        'show_surf': ui_show_surf, 'surf_color': ui.resolve_color(ui_sf_d, ui_sf_p, ui_sf_sync, resolved_bg, PALETTE), 'surf_opacity': ui_sf_op,
        'show_out_wire': ui_show_out, # New
        'outer_color': ui.resolve_color(ui_out_d, ui_out_p, ui_out_sync, resolved_bg, PALETTE), 'lw_outer': ui_lw_out,
        'show_in_wire': ui_show_in, # New
        'inner_color': ui.resolve_color(ui_in_d, ui_in_p, ui_in_sync, resolved_bg, PALETTE), 'lw_inner': ui_lw_in,
        'wire_start': ui_w_st, 'wire_span': ui_w_sp, 'surf_start': ui_s_st, 'surf_span': ui_s_sp,
        'camera_mode': ui_cam, 'rot_x': ui_rx, 'rot_y': ui_ry, 'rot_z': ui_rz
    })
    st.session_state.draw_params = new_params
    am.save_settings(new_params)

# --- Drawing Logic ---
P = st.session_state.draw_params
rm = ge.rot_matrix(P['rot_x'], P['rot_y'], P['rot_z'])
fig = go.Figure()

try:
    if P['show_surf']:
        sm = int(P['smoothness'])
        us = np.radians(np.linspace(P['surf_start'], P['surf_start']+P['surf_span'], sm))
        if P['shape_type'] == "Sphere":
            vs = np.linspace(0, np.pi, sm)
            us, vs = np.meshgrid(us, vs)
        elif P['shape_type'] == "Cylinder": vs = np.linspace(0, 1, sm)
        else:
            vs = np.linspace(0, 2*np.pi, sm)
            us, vs = np.meshgrid(us, vs)
        xs, ys, zs = ge.get_coords(P, P['shape_type'], P['outer_scale'], us, vs)
        rxs, rys, rzs = ge.apply_rot(xs.flatten(), ys.flatten(), zs.flatten(), rm)
        fig.add_trace(go.Surface(x=rxs.reshape(xs.shape), y=rys.reshape(ys.shape), z=rzs.reshape(zs.shape), 
                                 surfacecolor=np.ones_like(xs), colorscale=[[0, P['surf_color']], [1, P['surf_color']]], 
                                 showscale=False, opacity=P['surf_opacity'], hoverinfo='none'))

    def add_wire_trace(scale, color, width, start, span):
        sm = int(P['smoothness'])
        n_seg = int(P['segments_main'] * (span / 360)) + 1
        uw = np.radians(np.linspace(start, start+span, max(2, n_seg)))
        us = np.radians(np.linspace(start, start+span, sm))
        if P['shape_type'] == "Sphere":
            vw = np.linspace(0, np.pi, int(P['segments_sub']) + 1)
            vs = np.linspace(0, np.pi, sm)
            for u in uw:
                x, y, z = ge.get_coords(P, P['shape_type'], scale, u, vs)
                rx, ry, rz = ge.apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False))
            for v in vw[1:-1]:
                x, y, z = ge.get_coords(P, P['shape_type'], scale, us, v)
                rx, ry, rz = ge.apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False))
        elif P['shape_type'] == "Cylinder":
            vw = np.linspace(-float(P['h_cylinder'])/2, float(P['h_cylinder'])/2, int(P['segments_sub']) + 1)
            vs = np.linspace(-float(P['h_cylinder'])/2, float(P['h_cylinder'])/2, sm)
            for u in uw:
                x, y, z = ge.get_coords(P, P['shape_type'], scale, u, vs)
                rx, ry, rz = ge.apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False))
            for v in vw:
                R = float(P['R_base']) * scale
                x, y, z = R * np.cos(us), R * np.sin(us), np.full_like(us, v)
                rx, ry, rz = ge.apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False))
        else: # Torus
            vw = np.linspace(0, 2*np.pi, int(P['segments_sub']) + 1)
            vs = np.linspace(0, 2*np.pi, sm)
            for u in uw:
                x, y, z = ge.get_coords(P, P['shape_type'], scale, u, vs)
                rx, ry, rz = ge.apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False))
            for v in vw[:-1]:
                x, y, z = ge.get_coords(P, P['shape_type'], scale, us, v)
                rx, ry, rz = ge.apply_rot(x, y, z, rm)
                fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color=color, width=width), showlegend=False))

    # Updated: Checkbox flags
    if P.get('show_in_wire', True):
        add_wire_trace(P['inner_scale'], P['inner_color'], P['lw_inner'], P['wire_start'], P['wire_span'])
    
    if P.get('show_out_wire', True):
        add_wire_trace(P['outer_scale'], P['outer_color'], P['lw_outer'], P['wire_start'], P['wire_span'])

    if P.get('show_bb', True):
        bb_scale = float(P.get('bb_size', 10.0)) * 0.05
        sm_bb = 20
        us_bb, vs_bb = np.meshgrid(np.linspace(0, 2*np.pi, sm_bb), np.linspace(0, np.pi, sm_bb))
        bx, by, bz = ge.get_coords({'R_base': 1.0}, "Sphere", bb_scale, us_bb, vs_bb)
        fig.add_trace(go.Surface(x=bx, y=by, z=bz,
                                 surfacecolor=np.ones_like(bx), colorscale=[[0, P['bb_color']], [1, P['bb_color']]],
                                 showscale=False, opacity=1.0, hoverinfo='none'))

    # Camera Setup
    eye = dict(x=1.6, y=1.6, z=1.6)
    if P['camera_mode'] == "POV":
        eye = dict(x=0.05, y=0, z=0.01) if P['shape_type'] == "Torus" else dict(x=0.01, y=0, z=0)
    
    fig.update_layout(scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False), bgcolor=P['bg_color'], aspectmode='data'), 
                      paper_bgcolor=P['bg_color'], margin=dict(l=0,r=0,b=0,t=0), height=800, scene_camera=dict(eye=eye))
    st.plotly_chart(fig, use_container_width=True, theme=None)

except Exception as e:
    st.error(f"Render Error: {e}")