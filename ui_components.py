import streamlit as st

def synced_ui(label, key_base, def_val, min_v, max_v, step_s=1, step_b=0.01, fmt="%.2f"):
    st.caption(label)
    if key_base not in st.session_state:
        st.session_state[key_base] = float(def_val)
    if f"{key_base}_s" not in st.session_state:
        st.session_state[f"{key_base}_s"] = int(def_val)
    if f"{key_base}_b" not in st.session_state:
        st.session_state[f"{key_base}_b"] = float(def_val)

    def on_slider():
        val = st.session_state[f"{key_base}_s"]
        st.session_state[key_base] = float(val)
        st.session_state[f"{key_base}_b"] = float(val)

    def on_box():
        val = st.session_state[f"{key_base}_b"]
        st.session_state[key_base] = val
        st.session_state[f"{key_base}_s"] = int(val)

    st.slider(f"{label} Sl", min_v, max_v, key=f"{key_base}_s", step=step_s, on_change=on_slider, label_visibility="collapsed")
    st.number_input(f"{label} Bx", float(min_v), float(max_v), key=f"{key_base}_b", step=step_b, format=fmt, on_change=on_box, label_visibility="collapsed")
    return st.session_state[key_base]

def color_ui(label, key_suffix, palette, default_key="Custom", default_hex="#00FFFF"):
    st.caption(f"■ {label}")
    keys = list(palette.keys()) + ["Custom"]
    drop = st.selectbox(f"{label} D", keys, index=keys.index(default_key), key=f"drop_{key_suffix}", label_visibility="collapsed")
    pick = default_hex
    if drop == "Custom":
        pick = st.color_picker(f"Pick {label}", default_hex, key=f"pick_{key_suffix}")
    sync = False
    if label not in ["Background", "Singularity"]:
        sync = st.checkbox(f"Sync BG", key=f"sync_{key_suffix}")
    return drop, pick, sync

def resolve_color(drop, pick, sync, bg_hex, palette):
    if sync: return bg_hex
    if drop == "Custom": return pick
    return palette.get(drop, pick)