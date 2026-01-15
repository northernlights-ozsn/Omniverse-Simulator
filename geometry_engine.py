import numpy as np
import plotly.graph_objects as go

def get_coords(P, type_str, scale, u, v):
    scale = float(scale)
    if type_str == "Torus":
        R, r = float(P['R_base']), float(P['r_tube']) * scale
        x, y, z = (R + r * np.cos(v)) * np.cos(u), (R + r * np.cos(v)) * np.sin(u), r * np.sin(v)
    elif type_str == "Sphere":
        R = float(P['R_base']) * scale
        x, y, z = R * np.sin(v) * np.cos(u), R * np.sin(v) * np.sin(u), R * np.cos(v)
    elif type_str == "Cylinder":
        R, H = float(P['R_base']) * scale, float(P['h_cylinder'])
        z_g = np.linspace(-H/2, H/2, len(v))
        z_m, t_m = np.meshgrid(z_g, u)
        return R * np.cos(t_m), R * np.sin(t_m), z_m
    else: return np.zeros_like(u), np.zeros_like(u), np.zeros_like(u)
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