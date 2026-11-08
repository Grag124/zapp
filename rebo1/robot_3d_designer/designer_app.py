"""designer_app.py - AERO-1: 3D Autonomous Flying Robot Designer (Dash + Plotly).

Run:
    cd robot_3d_designer
    python3 designer_app.py

Then open http://127.0.0.1:8050 in your browser.

AERO-1 is a four-rotor flying robot that:
  - flies autonomously around the arena (patrol / grab / transport missions)
  - avoids walls and placed components (perception + local repulsion)
  - reacts to collisions: emergency drop + evasion burst (fall recovery)
  - grabs loose parts with a lowering claw and carries them
  - shows its own mind: a visible behavior state machine
    (IDLE -> PATROL -> GRAB -> TRANSPORT -> EVASION -> LANDING)
  - 16-part palette, click-in-scene selection with yellow highlight,
    X/Y/Z + rotation sliders, save/load layout to layout.json.

Architecture (Dash 2.18.x):
  - One dcc.Store holds all state (placed/selected/status).
  - on_action callback: all user actions update the store + slider values.
  - render_figure: store -> 3D figure (with highlight).
  - render_editor_ui: store -> editor heading / slider visibility / remove btn.
"""

import json
import math
import os
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback, callback_context

app = Dash(
    __name__,
    title="3D Robot Layout Designer",
    suppress_callback_exceptions=True,
)

# ---------------------------------------------------------------------------
# Component library
# "shape" is one of: "box", "cylinder_x", "cylinder_z"
# ---------------------------------------------------------------------------

COMPONENT_LIBRARY = {
    "chassis":    {"label": "Chassis",  "color": "#8B6914",
                   "shape": "box",
                   "size": {"x": 40, "y": 25, "z": 10}, "pos": [0, 0, 0]},
    "motor_1":    {"label": "Motor 1",  "color": "#555555",
                   "shape": "box",
                   "size": {"x": 6, "y": 6, "z": 8}, "pos": [-14, -18, 2]},
    "motor_2":    {"label": "Motor 2",  "color": "#555555",
                   "shape": "box",
                   "size": {"x": 6, "y": 6, "z": 8}, "pos": [14, -18, 2]},
    "motor_3":    {"label": "Motor 3",  "color": "#555555",
                   "shape": "box",
                   "size": {"x": 6, "y": 6, "z": 8}, "pos": [-14, 18, 2]},
    "motor_4":    {"label": "Motor 4",  "color": "#555555",
                   "shape": "box",
                   "size": {"x": 6, "y": 6, "z": 8}, "pos": [14, 18, 2]},
    "wheel_1":    {"label": "Wheel 1",  "color": "#222222",
                   "shape": "cylinder_z",
                   "size": {"x": 5, "y": 5, "z": 2}, "pos": [-20, -18, 2]},
    "wheel_2":    {"label": "Wheel 2",  "color": "#222222",
                   "shape": "cylinder_z",
                   "size": {"x": 5, "y": 5, "z": 2}, "pos": [20, -18, 2]},
    "wheel_3":    {"label": "Wheel 3",  "color": "#222222",
                   "shape": "cylinder_z",
                   "size": {"x": 5, "y": 5, "z": 2}, "pos": [-20, 18, 2]},
    "wheel_4":    {"label": "Wheel 4",  "color": "#222222",
                   "shape": "cylinder_z",
                   "size": {"x": 5, "y": 5, "z": 2}, "pos": [20, 18, 2]},
    "sensor":     {"label": "Sensor",   "color": "#1E90FF",
                   "shape": "box",
                   "size": {"x": 4, "y": 3, "z": 4}, "pos": [0, -22, 8]},
    "battery":    {"label": "Battery",  "color": "#008080",
                   "shape": "box",
                   "size": {"x": 12, "y": 7, "z": 3}, "pos": [0, 8, 6]},
    "brain":      {"label": "Pi Brain", "color": "#D2691E",
                   "shape": "box",
                   "size": {"x": 9, "y": 6, "z": 2}, "pos": [0, 0, 6]},
    "wing":       {"label": "Wing",     "color": "#F5F5DC",
                   "shape": "box",
                   "size": {"x": 60, "y": 4, "z": 3}, "pos": [0, 0, 14]},
    "servo":      {"label": "Servo",    "color": "#FF4500",
                   "shape": "box",
                   "size": {"x": 4, "y": 4, "z": 4}, "pos": [0, 0, 12]},
    "axle_1":     {"label": "Axle 1",   "color": "#DEB887",
                   "shape": "cylinder_x",
                   "size": {"x": 36, "y": 1, "z": 1}, "pos": [0, -18, 2]},
    "axle_2":     {"label": "Axle 2",   "color": "#DEB887",
                   "shape": "cylinder_x",
                   "size": {"x": 36, "y": 1, "z": 1}, "pos": [0, 18, 2]},
}

PALETTE_IDS = [f"btn-{k}" for k in COMPONENT_LIBRARY]

LAYOUT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "layout.json"
)

# Highlight color for the selected component
HIGHLIGHT_COLOR = "#FFFF00"

# Arena bounds - AERO-1's flight cage (walls it actively avoids)
ARENA = {"x": 45.0, "y": 45.0, "z_max": 30.0}

# Reverse lookup: label -> component key
LABEL_TO_KEY = {spec["label"]: key for key, spec in COMPONENT_LIBRARY.items()}

# ---------------------------------------------------------------------------
# 3D geometry helpers
# ---------------------------------------------------------------------------

def _box_corners(cx, cy, cz, sx, sy, sz):
    return (
        [cx - sx, cx + sx, cx + sx, cx - sx,
         cx - sx, cx + sx, cx + sx, cx - sx],
        [cy - sy, cy - sy, cy + sy, cy + sy,
         cy - sy, cy - sy, cy + sy, cy + sy],
        [cz - sz, cz - sz, cz - sz, cz - sz,
         cz + sz, cz + sz, cz + sz, cz + sz],
    )


_BOX_FACES = [0, 1, 2, 3]


def _cylinder_z(cx, cy, cz, rx, ry, rz, n=36):
    """Cylinder with axis along Z (vertical). rx=X radius, ry=Y radius."""
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x0 = np.full(n, cx) + rx * np.cos(t)
    y0 = np.full(n, cy) + ry * np.sin(t)
    zb = np.full(n, cz - rz)
    xt = np.full(n, cx) + rx * np.cos(t)
    yt = np.full(n, cy) + ry * np.sin(t)
    zt = np.full(n, cz + rz)
    vx = np.concatenate([x0, xt])
    vy = np.concatenate([y0, yt])
    vz = np.concatenate([zb, zt])
    i, j = [], []
    for k in range(n):
        a, b = k, (k + 1) % n
        i += [a, a, b]
        j += [b, n + b, n + a]
    c0, c1 = 2 * n, 2 * n + 1
    vx = np.append(vx, [cx, cx])
    vy = np.append(vy, [cy, cy])
    vz = np.append(vz, [cz - rz, cz + rz])
    for k in range(n):
        a, b = k, (k + 1) % n
        i += [a, b, a, b, a, b]
        j += [c0, c0, c1, c1, b, a]
    return list(vx), list(vy), list(vz), i, j


def _cylinder_x(cx, cy, cz, rx, ry, rz, n=36):
    """Cylinder with axis along X (horizontal). ry=Y radius, rz=Z radius."""
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    xl = np.full(n, cx - rx)
    yr = np.full(n, cy) + ry * np.cos(t)
    zr = np.full(n, cz) + rz * np.sin(t)
    xl2 = np.full(n, cx + rx)
    vx = np.concatenate([xl, xl2])
    vy = np.concatenate([yr, yr])
    vz = np.concatenate([zr, zr])
    i, j = [], []
    for k in range(n):
        a, b = k, (k + 1) % n
        i += [a, a, b]
        j += [b, n + b, n + a]
    c0, c1 = 2 * n, 2 * n + 1
    vx = np.append(vx, [cx - rx, cx + rx])
    vy = np.append(vy, [cy, cy])
    vz = np.append(vz, [cz, cz])
    for k in range(n):
        a, b = k, (k + 1) % n
        i += [a, b, a, b, a, b]
        j += [c0, c0, c1, c1, b, a]
    return list(vx), list(vy), list(vz), i, j


def _apply_z_rotation(verts, cx, cy, cz, rot_deg):
    """Rotate vertex arrays (vx, vy, vz) around (cx, cy) by rot_deg degrees.

    Returns rotated vertex arrays as lists.
    """
    if not rot_deg:
        return verts
    theta = math.radians(rot_deg)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    vx, vy, vz = verts
    rx, ry, rz = [], [], []
    for x, y, z in zip(vx, vy, vz):
        dx = x - cx
        dy = y - cy
        rx.append(cx + dx * cos_t - dy * sin_t)
        ry.append(cy + dx * sin_t + dy * cos_t)
        rz.append(z)
    return rx, ry, rz


def make_component_traces(comp_key, placed_state, is_selected):
    """Return a list of Plotly traces for one component.

    placed_state: [x, y, z] or [x, y, z, rot_deg]
    is_selected:  bool - if True, add a yellow highlight overlay.
    """
    spec  = COMPONENT_LIBRARY[comp_key]
    pos   = placed_state if placed_state is not None else spec["pos"]
    cx, cy, cz = pos[0], pos[1], pos[2]
    rot = pos[3] if len(pos) > 3 else 0.0
    shape = spec.get("shape", "box")
    size  = spec["size"]
    color = spec["color"]
    label = spec["label"]
    traces = []

    if shape == "box":
        sx, sy, sz = size["x"] / 2, size["y"] / 2, size["z"] / 2
        x, y, z = _box_corners(cx, cy, cz, sx, sy, sz)
        if rot:
            x, y, z = _apply_z_rotation((x, y, z), cx, cy, cz, rot)
        mesh = go.Mesh3d(
            x=x, y=y, z=z,
            i=_BOX_FACES, j=_BOX_FACES,
            color=color, opacity=0.9, name=label, flatshading=True,
        )
        label_z = cz + sz + 1.5

    elif shape == "cylinder_z":
        rx, ry, rz = size["x"] / 2, size["y"] / 2, size["z"] / 2
        vx, vy, vz, fi, fj = _cylinder_z(cx, cy, cz, rx, ry, rz)
        if rot:
            vx, vy, vz = _apply_z_rotation((vx, vy, vz), cx, cy, cz, rot)
        mesh = go.Mesh3d(
            x=vx, y=vy, z=vz, i=fi, j=fj,
            color=color, opacity=0.9, name=label, flatshading=True,
        )
        label_z = cz + rz + 1.5

    elif shape == "cylinder_x":
        rx, ry, rz = size["x"] / 2, size["y"] / 2, size["z"] / 2
        vx, vy, vz, fi, fj = _cylinder_x(cx, cy, cz, rx, ry, rz)
        if rot:
            vx, vy, vz = _apply_z_rotation((vx, vy, vz), cx, cy, cz, rot)
        mesh = go.Mesh3d(
            x=vx, y=vy, z=vz, i=fi, j=fj,
            color=color, opacity=0.9, name=label, flatshading=True,
        )
        label_z = cz + max(ry, rz) + 1.5

    else:
        mesh = None
        label_z = cz + 2

    if mesh is not None:
        traces.append(mesh)
        if is_selected:
            # Build a fresh highlight mesh with same vertices, yellow overlay
            hl = go.Mesh3d(
                x=mesh.x, y=mesh.y, z=mesh.z,
                i=mesh.i, j=mesh.j,
                color=HIGHLIGHT_COLOR, opacity=0.35,
                name=label + " (selected)",
                flatshading=True,
            )
            traces.append(hl)

    label_trace = go.Scatter3d(
        x=[cx], y=[cy], z=[label_z],
        mode="text", text=[label],
        textposition="top center",
        textfont=dict(size=13, color=("yellow" if is_selected else "white")),
        showlegend=False,
    )
    traces.append(label_trace)
    return traces



# ---------------------------------------------------------------------------
# AERO-1: the autonomous flying robot
# ---------------------------------------------------------------------------

def _drone_body(cx, cy, cz, facing_deg, tilt_deg, color="#3AA7F0"):
    """Traces for the AERO-1 body: fuselage + 4 rotor arms + claw hook."""
    t = math.radians(facing_deg)
    ct, st = math.cos(t), math.sin(t)
    span = 9.0
    arm = 5.0
    traces = []
    # X-quad rotor arms (4 motor hubs + thin prop blades)
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        lx = sx * span * ct - sy * span * st
        ly = sx * span * st + sy * span * ct
        rx_, ry_ = cx + lx, cy + ly
        vx, vy, vz, fi, fj = _cylinder_z(rx_, ry_, cz + 1.0, 1.2, 1.2, 1.4)
        traces.append(go.Mesh3d(x=vx, y=vy, z=vz, i=fi, j=fj,
                                color="#111111", opacity=1.0,
                                name="AERO-1", showlegend=False, flatshading=True))
        bl = go.Mesh3d(
            x=[rx_ - arm * ct, rx_ + arm * ct, rx_ + arm * ct, rx_ - arm * ct,
               rx_ - arm * ct, rx_ + arm * ct, rx_ + arm * ct, rx_ - arm * ct],
            y=[ry_ - arm * st, ry_ + arm * st, ry_ + arm * st, ry_ - arm * st,
               ry_ + arm * st, ry_ - arm * st, ry_ - arm * st, ry_ + arm * st],
            z=[cz + 1.4] * 8,
            i=_BOX_FACES, j=_BOX_FACES, color="#DDDDDD", opacity=0.75,
            name="AERO-1", showlegend=False, flatshading=True)
        traces.append(bl)
    # fuselage
    fx, fy, fz = _box_corners(cx, cy, cz, 3.5, 2.5, 1.8)
    traces.append(go.Mesh3d(x=fx, y=fy, z=fz, i=_BOX_FACES, j=_BOX_FACES,
                            color=color, opacity=1.0, name="AERO-1",
                            showlegend=False, flatshading=True))
    # forward sensor dome
    sx, sy = cx + 3.8 * ct, cy + 3.8 * st
    traces.append(go.Scatter3d(x=[sx], y=[sy], z=[cz + 0.8], mode="markers",
                               marker=dict(size=5, color="#1E90FF"),
                               name="AERO-1", showlegend=False))
    # claw hook (front, drops to grab)
    hx, hy = cx + 5.2 * ct, cy + 5.2 * st
    traces.append(go.Scatter3d(
        x=[hx, hx, hx + 0.8], y=[hy, hy, hy],
        z=[cz + 0.6, cz - 1.6, cz - 1.6], mode="lines",
        line=dict(width=4, color="#FFB84D"), name="AERO-1", showlegend=False))
    # label
    traces.append(go.Scatter3d(
        x=[cx], y=[cy], z=[cz + 3.6], mode="text", text=["AERO-1"],
        textposition="top center", showlegend=False,
        textfont=dict(size=14, color=color, family="monospace")))
    return traces


# ---------------------------------------------------------------------------
# AERO-1 autonomous brain (finite-state machine + wall/object avoidance)
# ---------------------------------------------------------------------------

WALL_MARGIN = 3.0
DRONE_RADIUS = 10.0        # safety bubble radius for collision detection


def drone_bounds(placed_components):
    """Radius of the mission corridor around the largest placed part."""
    if not placed_components:
        return 15.0
    hx = hy = 0.0
    for key, pos in placed_components.items():
        if key not in COMPONENT_LIBRARY:
            continue
        s = COMPONENT_LIBRARY[key]["size"]
        hx = max(hx, abs(float(pos[0])) + s["x"] / 2)
        hy = max(hy, abs(float(pos[1])) + s["y"] / 2)
    return float(min(max(max(hx, hy) + 8.0, 18.0), ARENA["x"] - WALL_MARGIN))


def step_autonomy(au, placed_components, dt=0.4):
    """Advance AERO-1's own-mind simulation by one tick (mutates au)."""
    au["t"] = au.get("t", 0.0) + dt
    state = au.get("state", "IDLE")
    au["t_phase"] = au.get("t_phase", 0.0) + dt
    bound = drone_bounds(placed_components)

    def wall_push():
        """Perception: repulsive vector away from the closest arena wall."""
        x, y, z = au["x"], au["y"], au["z"]
        fx = fy = fz = 0.0
        m = ARENA["x"] - WALL_MARGIN
        if x > m: fx = -1.0
        if x < -m: fx = 1.0
        if y > m: fy = -1.0
        if y < -m: fy = 1.0
        if z > ARENA["z_max"] - 5: fz = -1.0
        if z < 3: fz = 1.0
        return fx, fy, fz

    def collision_check():
        """Drone bubble vs placed parts -> emergency evasion trigger."""
        x, y, z = au["x"], au["y"], au["z"]
        r = DRONE_RADIUS
        for key, pos in placed_components.items():
            if key not in COMPONENT_LIBRARY:
                continue
            s = COMPONENT_LIBRARY[key]["size"]
            px, py, pz = float(pos[0]), float(pos[1]), float(pos[2])
            cx = min(max(x, px - s["x"] / 2 - r), px + s["x"] / 2 + r)
            cy = min(max(y, py - s["y"] / 2 - r), py + s["y"] / 2 + r)
            cz = min(max(z, pz - s["z"] / 2 - r), pz + s["z"] / 2 + r)
            if abs(x - cx) < 0.01 and abs(y - cy) < 0.01 and abs(z - cz) < 0.01:
                return key
        return None

    def go_to(tx, ty, tz, speed):
        dx, dy, dz = tx - au["x"], ty - au["y"], tz - au["z"]
        dist = math.hypot(dx, dy, dz) + 1e-6
        au["speed"] = speed
        au["vx"], au["vy"], au["vz"] = dx / dist * speed, dy / dist * speed, dz / dist * speed
        if dist > 0.5:
            au["yaw"] = math.degrees(math.atan2(dx, dy))
        return dist

    # --- collision: emergency reaction overrides everything ---
    hit = collision_check()
    if hit and state not in ("EVASION",):
        state = "EVASION"
        au["t_phase"] = 0.0
        au["event"] = f"COLLISION with {COMPONENT_LIBRARY[hit]['label']} - emergency evasion!"
        pos = placed_components[hit]
        dx = au["x"] - float(pos[0])
        dy = au["y"] - float(pos[1])
        d = math.hypot(dx, dy) + 1e-6
        au["evade_dir"] = [dx / d, dy / d]
        if au.get("grabbed"):
            au["event"] += " Cargo dropped!"
            au["grabbed"] = None

    # wall proximity: brake + steer inward + tilt
    fx, fy, fz = wall_push()
    if (fx or fy or fz):
        au["vx"] += fx * 6.0 * dt
        au["vy"] += fy * 6.0 * dt
        au["vz"] += fz * 4.0 * dt
        au["tilt"] = min(12.0, max(au.get("tilt", 0.0), 6.0 * (abs(fx) + abs(fy))))

    # --- behavior state machine ---
    if state in ("IDLE", "PATROL"):
        target = au.get("target")
        if target is None or au.get("t_phase", 0) > 9.0:
            ang = au["t"] * 0.35
            target = [bound * math.cos(ang), bound * math.sin(ang), 16.0]
            au["target"] = target
            if state == "IDLE":
                state = au["state"] = "PATROL"
                au["t_phase"] = 0.0
                au["event"] = "Patrol: surveying the arena"
            else:
                # occasionally hunt for something to grab
                if placed_components and au["t"] % 20 < dt:
                    state = au["state"] = "GRAB"
                    au["t_phase"] = 0.0
        go_to(*target, 4.0)

    elif state == "GRAB":
        candidates = [k for k in placed_components
                      if k in ("sensor", "brain", "battery", "servo")]
        if not candidates:
            state = au["state"] = "PATROL"
            au["event"] = "Nothing grabbable - resuming patrol"
            au["t_phase"] = 0.0
        else:
            best = min(candidates, key=lambda k: (
                (au["x"] - float(placed_components[k][0])) ** 2 +
                (au["y"] - float(placed_components[k][1])) ** 2))
            p = placed_components[best]
            dist = go_to(float(p[0]), float(p[1]), float(p[2]) + 3.0, 3.0)
            au["hook"] = True
            if dist < 2.5:
                au["grabbed"] = best
                au["hook"] = False
                state = au["state"] = "TRANSPORT"
                au["event"] = f"Grabbed {COMPONENT_LIBRARY[best]['label']} - transporting"
                au["t_phase"] = 0.0

    elif state == "TRANSPORT":
        if not au.get("grabbed"):
            state = au["state"] = "PATROL"
            au["event"] = "Cargo lost - resuming patrol"
            au["t_phase"] = 0.0
        elif au.get("t_phase", 0) > 10.0:
            state = au["state"] = "LANDING"
            au["event"] = "Returning to home pad"
            au["t_phase"] = 0.0
        else:
            p = placed_components.get(au["grabbed"])
            if p is not None:
                go_to(float(p[0]), float(p[1]), ARENA["z_max"] - 8, 3.0)
                au["hook"] = True

    elif state == "LANDING":
        dist = go_to(0.0, 0.0, 16.0, 3.0)
        if dist < 2.0:
            state = au["state"] = "IDLE"
            au["event"] = "Back at home pad - thinking..."
            au["t_phase"] = 0.0
            au["target"] = None

    elif state == "EVASION":
        ex, ey = au.get("evade_dir", [0, 1])
        au["speed"] = 8.0
        au["vx"], au["vy"], au["vz"] = ex * 8.0, ey * 8.0, 4.0
        au["tilt"] = 18.0
        au["hook"] = False
        if au.get("t_phase", 0) > 1.6:
            state = au["state"] = "PATROL"
            au["t_phase"] = 0.0
            au["event"] = "Attitude recovered - back to patrol"

    # --- integrate motion, clamp inside arena (never hits a wall) ---
    au["x"] += au["vx"] * dt
    au["y"] += au["vy"] * dt
    au["z"] += au["vz"] * dt
    lim = ARENA["x"] - 2.0
    if au["x"] > lim:  au["x"], au["vx"] = lim, -abs(au["vx"]) * 0.4
    if au["x"] < -lim: au["x"], au["vx"] = -lim, abs(au["vx"]) * 0.4
    if au["y"] > lim:  au["y"], au["vy"] = lim, -abs(au["vy"]) * 0.4
    if au["y"] < -lim: au["y"], au["vy"] = -lim, abs(au["vy"]) * 0.4
    if au["z"] > ARENA["z_max"] - 1: au["z"], au["vz"] = ARENA["z_max"] - 1, -abs(au["vz"]) * 0.4
    if au["z"] < 2.0:               au["z"], au["vz"] = 2.0, abs(au["vz"]) * 0.4
    au.setdefault("tilt", 0.0)
    if state != "EVASION":
        au["tilt"] = max(0.0, au["tilt"] - 8.0 * dt)

    # motion trail
    trail = au.get("trail", [])
    trail.append([au["x"], au["y"], au["z"]])
    au["trail"] = trail[-24:]
    au["state"] = state
    return au


def build_figure(placed_components, selected_key=None, autonomy=None):
    fig = go.Figure()

    xg, yg = np.meshgrid(np.arange(-40, 41, 10), np.arange(-40, 41, 10))
    fig.add_trace(go.Scatter3d(
        x=xg.ravel(), y=yg.ravel(), z=np.zeros_like(xg.ravel()),
        mode="lines",
        line=dict(width=1, color="rgba(255,255,255,0.15)"),
        name="floor", showlegend=False,
    ))
    fig.add_trace(go.Scatter3d(
        x=[-45, 45], y=[0, 0], z=[0, 0],
        mode="text", text=["-X", "+X"],
        textposition="top center", showlegend=False,
    ))
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[-45, 45], z=[0, 0],
        mode="text", text=["-Y", "+Y"],
        textposition="top center", showlegend=False,
    ))
    # arena wireframe (the walls AERO-1 avoids)
    b = ARENA["x"]
    c = [(-b, -b, 0), (b, -b, 0), (b, b, 0), (-b, b, 0),
         (-b, -b, ARENA["z_max"]), (b, -b, ARENA["z_max"]),
         (b, b, ARENA["z_max"]), (-b, b, ARENA["z_max"])]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    ex = [c[a][0] for a, e in edges] + [c[e][0] for a, e in edges]
    ey = [c[a][1] for a, e in edges] + [c[e][1] for a, e in edges]
    ez = [c[a][2] for a, e in edges] + [c[e][2] for a, e in edges]
    fig.add_trace(go.Scatter3d(x=ex, y=ey, z=ez, mode="lines",
                               line=dict(width=2, color="rgba(78,205,196,0.25)"),
                               name="arena", showlegend=False))
    # home pad
    fig.add_trace(go.Scatter3d(
        x=[-8, 8, 8, -8, -8], y=[-8, -8, 8, 8, -8], z=[0.2] * 5, mode="lines",
        line=dict(width=4, color="rgba(46,204,113,0.8)"), name="home pad", showlegend=False))

    # AERO-1 drone + trail + cargo
    if autonomy:
        for trace in _drone_body(
                autonomy["x"], autonomy["y"], autonomy["z"],
                autonomy.get("yaw", 0.0), autonomy.get("tilt", 0.0)):
            fig.add_trace(trace)
        if len(autonomy.get("trail", [])) > 1:
            tr = autonomy["trail"]
            fig.add_trace(go.Scatter3d(
                x=[p[0] for p in tr], y=[p[1] for p in tr], z=[p[2] for p in tr],
                mode="lines", line=dict(width=3, color="rgba(58,167,240,0.5)"),
                name="trail", showlegend=False))
        gkey = autonomy.get("grabbed")
        if gkey and gkey in COMPONENT_LIBRARY:
            gs = COMPONENT_LIBRARY[gkey]["size"]
            yaw_r = math.radians(autonomy.get("yaw", 0.0))
            gx = autonomy["x"] - math.sin(yaw_r) * 5.2
            gy = autonomy["y"] - math.cos(yaw_r) * 5.2
            bx, by, bz = _box_corners(gx, gy, autonomy["z"] - 3.5,
                                       gs["x"] / 2, gs["y"] / 2, gs["z"] / 2)
            fig.add_trace(go.Mesh3d(x=bx, y=by, z=bz, i=_BOX_FACES, j=_BOX_FACES,
                                    color=COMPONENT_LIBRARY[gkey]["color"],
                                    opacity=0.9, name=f"carrying {gkey}", flatshading=True))

    for comp_key, pos in placed_components.items():
        if comp_key in COMPONENT_LIBRARY:
            is_sel = (comp_key == selected_key)
            for trace in make_component_traces(comp_key, pos, is_sel):
                fig.add_trace(trace)

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X (cm)", range=[-45, 45]),
            yaxis=dict(title="Y (cm)", range=[-45, 45]),
            zaxis=dict(title="Z (cm)", range=[-5, 30]),
            camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2)),
        ),
        title=dict(
            text="AERO-1 - 3D Autonomous Flying Robot Designer",
            font=dict(size=16, color="white"),
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        margin=dict(l=0, r=0, t=50, b=0),
        width=900, height=550,
        uirevision="layout",
    )
    return fig


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

SLIDER_DEFAULT = {"x": 0.0, "y": 0.0, "z": 0.0, "rot": 0.0}


def build_palette_buttons():
    buttons = []
    for key, spec in COMPONENT_LIBRARY.items():
        buttons.append(
            html.Button(
                children=[
                    html.Span(
                        style={"backgroundColor": spec["color"],
                               "display": "inline-block",
                               "width": "14px", "height": "14px",
                               "borderRadius": "3px",
                               "marginRight": "6px"},
                    ),
                    spec["label"],
                ],
                id=f"btn-{key}",
                n_clicks=0,
                style={
                    "display": "flex", "alignItems": "center",
                    "border": "1px solid #333",
                    "backgroundColor": "#2a2a3e",
                    "color": "#eee", "borderRadius": "4px",
                    "padding": "4px 8px", "margin": "2px 0",
                    "fontSize": "12px", "cursor": "pointer",
                    "width": "100%", "justifyContent": "flex-start",
                },
            )
        )
    return buttons


def _slider_row(axis, accent="#4ECDC4"):
    if axis == "rot":
        marks = {v: f"{v}\u00b0" for v in [-180, -90, -45, 0, 45, 90, 180]}
        min_val, max_val = -180, 180
        label = "Rotate"
    else:
        marks = {v: str(v) for v in range(-40, 41, 10)}
        min_val, max_val = -40, 40
        label = axis.upper()
    return html.Div(
        children=[
            html.Label(
                children=f"{label}",
                style={"fontSize": "13px", "color": accent,
                       "marginBottom": "2px", "display": "block"},
            ),
            dcc.RangeSlider(
                id=f"slider-{axis}",
                min=min_val, max=max_val, step=0.5,
                value=[0, 0],
                allowCross=False,
                disabled=True,  # enabled via render_editor_ui when a part is selected
                marks=marks,
            ),
        ],
        style={"marginBottom": "12px", "padding": "8px",
               "borderLeft": f"3px solid {accent}", "backgroundColor": "#25253a"},
    )


def _panel(title, children):
    return html.Div(
        children=[
            html.H5(
                title,
                style={"color": "#4ECDC4", "borderBottom": "1px solid #333",
                       "paddingBottom": "6px", "margin": "0 0 10px 0"},
            ),
            *children,
        ],
        style={"backgroundColor": "#2a2a3e", "borderRadius": "6px",
               "padding": "16px", "height": "100%", "boxSizing": "border-box"},
    )


def _action_buttons():
    base = {
        "backgroundColor": "#2a2a3e", "color": "#eee",
        "border": "1px solid #444", "borderRadius": "4px",
        "padding": "5px 8px", "fontSize": "11px", "cursor": "pointer",
        "width": "100%", "marginBottom": "4px",
    }
    return [
        html.Button(id="btn-clear",  children="Clear All", n_clicks=0, style=base),
        html.Button(id="btn-remove", children="Remove Selected", n_clicks=0,
                    style={**base, "borderColor": "#e74c3c"}, disabled=True),
        html.Button(id="btn-save",   children="Save to layout.json", n_clicks=0,
                    style={**base, "borderColor": "#2ecc71"}),
        html.Button(id="btn-load",   children="Load from layout.json", n_clicks=0,
                    style={**base, "borderColor": "#3498db"}),
        html.Hr(style={"borderColor": "#444", "margin": "8px 0"}),
        html.Button(id="btn-sim", children="\u25b6 Start AERO-1 Autonomy", n_clicks=0,
                    style={**base, "borderColor": "#3AA7F0",
                           "backgroundColor": "#123a5e", "fontWeight": "bold"}),
        html.Button(id="btn-sim-stop", children="\u23f9 Stop AERO-1", n_clicks=0,
                    style={**base, "borderColor": "#FFB84D"}),
    ]


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------

app.layout = html.Div(
    style={"display": "flex", "height": "100vh", "backgroundColor": "#1a1a2e",
           "fontFamily": "sans-serif", "position": "relative"},
    children=[
        # Hidden stores + simulation heartbeat
        dcc.Store(id="store-state", data={
            "placed": {},
            "selected": None,
            "status": "Welcome! Click a component in the palette to begin.",
        }),
        dcc.Store(id="store-drone", data={
            "x": 0, "y": 0, "z": 16, "vx": 0, "vy": 0, "vz": 0,
            "yaw": 0, "speed": 0, "state": "IDLE", "tilt": 0,
            "grabbed": None, "target": None, "evade_dir": None,
            "event": "System online - press Start to launch autonomous flight",
            "t": 0, "t_phase": 0, "trail": [], "hook": False, "active": False,
        }),
        dcc.Interval(id="sim-timer", interval=0, max_intervals=0),
        # Left: palette
        html.Div(
            children=_panel(
                "Component Palette",
                [
                    *build_palette_buttons(),
                    html.Hr(style={"borderColor": "#444", "margin": "10px 0"}),
                    html.Div(
                        [
                            "Click a part to add it.",
                            "Click a part in the 3D view to select it.",
                        ],
                        style={"fontSize": "11px", "color": "#888",
                               "whiteSpace": "pre-line"},
                    ),
                ],
            ),
            style={"width": "220px", "padding": "12px", "flexShrink": "0"},
        ),

        # Center: 3D scene + status bar
        html.Div(
            style={"flex": 1, "display": "flex", "flexDirection": "column",
                   "overflow": "hidden"},
            children=[
                html.Div(
                    id="status-bar",
                    children="Welcome! Click a component in the palette to begin.",
                    style={"padding": "8px 14px", "backgroundColor": "#16213e",
                           "color": "#4ECDC4", "fontSize": "13px",
                           "borderBottom": "1px solid #333", "whiteSpace": "nowrap",
                           "overflow": "hidden"},
                ),
                html.Div(
                    style={"flex": 1, "display": "flex", "alignItems": "center",
                           "justifyContent": "center", "padding": "8px"},
                    children=[dcc.Graph(id="scene3d", figure=build_figure({}),
                                          config={"displayModeBar": False})],
                ),
                html.Div(
                    id="telemetry-bar",
                    children=[
                        html.Span("AERO-1: ", style={"color": "#3AA7F0", "fontWeight": "bold"}),
                        html.Span(id="t-state", children="IDLE"),
                        html.Span("  |  pos ", style={"color": "#888"}),
                        html.Span(id="t-pos", children="(0, 0, 16)"),
                        html.Span("  |  ", style={"color": "#888"}),
                        html.Span(id="t-event", children="system online"),
                    ],
                    style={"padding": "6px 14px", "backgroundColor": "#0a0a14",
                           "color": "#ddd", "fontSize": "12px",
                           "borderTop": "1px solid #222", "fontFamily": "monospace"}),
            ],
        ),

        # Right: editor panel
        html.Div(
            children=_panel(
                "Editor",
                [
                    html.Div(
                        id="editor-heading",
                        children="No component selected",
                        style={"color": "#fff", "fontSize": "14px",
                               "marginBottom": "10px"},
                    ),
                    html.Div(
                        id="slider-panel",
                        style={"display": "none"},
                        children=[
                            _slider_row("x", accent="#4ECDC4"),
                            _slider_row("y", accent="#4ECDC4"),
                            _slider_row("z", accent="#4ECDC4"),
                            _slider_row("rot", accent="#FFB84D"),
                        ],
                    ),
                    html.Hr(style={"borderColor": "#444", "margin": "10px 0"}),
                    *(_action_buttons()),
                    html.Hr(style={"borderColor": "#444", "margin": "10px 0"}),
                    html.Div(
                        [
                            html.H6("About", style={"color": "#4ECDC4"}),
                            html.P(
                                "Design your parts, then launch AERO-1: it patrols, "
                                "avoids the arena walls, grabs and carries loose parts, "
                                "and dodges collisions with an emergency evasion burst.",
                                style={"fontSize": "11px", "color": "#aaa",
                                       "lineHeight": "1.5"},
                            ),
                        ],
                    ),
                ],
            ),
            style={"width": "260px", "padding": "12px", "flexShrink": "0"},
        ),
    ],
)


# ---------------------------------------------------------------------------
# Callback A: all user actions -> store + sliders
# ---------------------------------------------------------------------------

@callback(
    Output("store-state", "data"),
    Output("status-bar", "children"),
    Output("slider-x", "value"),
    Output("slider-y", "value"),
    Output("slider-z", "value"),
    Output("slider-rot", "value"),
    # 16 palette buttons (individual inputs to avoid list-input wildcard issue)
    Input("btn-chassis", "n_clicks"),
    Input("btn-motor_1", "n_clicks"),
    Input("btn-motor_2", "n_clicks"),
    Input("btn-motor_3", "n_clicks"),
    Input("btn-motor_4", "n_clicks"),
    Input("btn-wheel_1", "n_clicks"),
    Input("btn-wheel_2", "n_clicks"),
    Input("btn-wheel_3", "n_clicks"),
    Input("btn-wheel_4", "n_clicks"),
    Input("btn-sensor", "n_clicks"),
    Input("btn-battery", "n_clicks"),
    Input("btn-brain", "n_clicks"),
    Input("btn-wing", "n_clicks"),
    Input("btn-servo", "n_clicks"),
    Input("btn-axle_1", "n_clicks"),
    Input("btn-axle_2", "n_clicks"),
    # 4 action buttons
    Input("btn-clear", "n_clicks"),
    Input("btn-remove", "n_clicks"),
    Input("btn-save", "n_clicks"),
    Input("btn-load", "n_clicks"),
    # 2 autonomy buttons
    Input("btn-sim", "n_clicks"),
    Input("btn-sim-stop", "n_clicks"),
    # 4 sliders
    Input("slider-x", "value"),
    Input("slider-y", "value"),
    Input("slider-z", "value"),
    Input("slider-rot", "value"),
    # 1 click data from the 3D scene
    Input("scene3d", "clickData"),
    # 1 state store
    State("store-state", "data"),
)
def on_action(*args):
    # args: 0-15 palette, 16-19 actions, 20-21 sim buttons, 22-25 sliders,
    #       26 scene clickData, 27 store-state
    state = args[27] if len(args) > 27 else None
    ctx = callback_context
    if not ctx.triggered:
        return state, "Welcome!", [0, 0], [0, 0], [0, 0], [0, 0]
    trigger_id = next(iter(ctx.triggered[0]))
    if "." in trigger_id:
        trigger_id = trigger_id.rsplit(".", 1)[0]

    placed, selected, status = {}, None, "Welcome!"
    if state and isinstance(state, dict):
        placed   = state.get("placed", {})
        selected = state.get("selected")
        status   = state.get("status", "Welcome!")

    # --- palette button: add / select component ---
    palette_map = {f"btn-{k}": k for k in COMPONENT_LIBRARY}
    if trigger_id in palette_map:
        comp_key = palette_map[trigger_id]
        spec = COMPONENT_LIBRARY[comp_key]
        if comp_key in placed:
            selected = comp_key
            status = f"Selected {spec['label']}"
        else:
            placed[comp_key] = list(spec["pos"])
            selected = comp_key
            status = f"Added {spec['label']} - use sliders to position"

    # --- action buttons ---
    elif trigger_id == "btn-remove":
        if selected and selected in placed:
            del placed[selected]
            selected = None
            status = f"Removed {COMPONENT_LIBRARY.get(selected, selected)}"
        else:
            status = "Nothing selected to remove"
    elif trigger_id == "btn-clear":
        placed = {}
        selected = None
        status = "Scene cleared"
    elif trigger_id == "btn-save":
        with open(LAYOUT_FILE, "w") as f:
            json.dump(placed, f, indent=2)
        status = f"Saved {len(placed)} components to layout.json"
    elif trigger_id == "btn-load":
        if os.path.exists(LAYOUT_FILE):
            with open(LAYOUT_FILE, "r") as f:
                loaded = json.load(f)
            placed = {k: v for k, v in loaded.items() if k in COMPONENT_LIBRARY}
            selected = None
            status = f"Loaded {len(placed)} components from layout.json"
        else:
            status = "layout.json not found - nothing to load"

    # --- autonomy buttons: note the toggle (heartbeat does the real work) ---
    elif trigger_id in ("btn-sim", "btn-sim-stop"):
        status = ("AERO-1 autonomous flight loop started."
                  if trigger_id == "btn-sim" else "AERO-1 stopped by operator.")

    # --- slider drag: update the selected component's position/rotation ---
    # arg positions: 0-15 palette, 16 clear, 17 remove, 18 save, 19 load,
    # 20 sim, 21 sim-stop, 22-25 sliders, 26 scene click, 27 state
    elif trigger_id in ("slider-x", "slider-y", "slider-z", "slider-rot"):
        axis_idx = {"slider-x": 0, "slider-y": 1, "slider-z": 2, "slider-rot": 3}[trigger_id]
        slider_arg_pos = {"slider-x": 22, "slider-y": 23, "slider-z": 24, "slider-rot": 25}
        if selected and selected in placed:
            pos = list(placed[selected])
            while len(pos) < 4:
                pos.append(0.0)
            slider_val = args[slider_arg_pos[trigger_id]]
            # RangeSlider value is a list [min_val, max_val] - we use max_val as the position
            new_val = float(slider_val[1]) if isinstance(slider_val, list) else float(slider_val)
            pos[axis_idx] = new_val
            placed[selected] = pos[:4]
            label = COMPONENT_LIBRARY[selected]["label"]
            axis_label = {0: "X", 1: "Y", 2: "Z", 3: "Rot"}[axis_idx]
            status = f"Moved {label} {axis_label} -> {new_val}"

    # --- click in 3D scene: select component ---
    elif trigger_id == "scene3d":
        click_data = args[26]
        if click_data and click_data.get("points"):
            trace_name = click_data["points"][0].get("name", "").replace(" (selected)", "")
            comp_key = LABEL_TO_KEY.get(trace_name)
            if comp_key and comp_key in placed:
                selected = comp_key
                status = f"Selected {COMPONENT_LIBRARY[comp_key]['label']}"
            else:
                selected = None
                status = "Selection cleared"

    # Compute slider values to show
    if selected and selected in placed:
        pos = placed[selected]
        vx = pos[0] if len(pos) > 0 else 0
        vy = pos[1] if len(pos) > 1 else 0
        vz = pos[2] if len(pos) > 2 else 0
        vr = pos[3] if len(pos) > 3 else 0.0
    else:
        vx, vy, vz, vr = 0, 0, 0, 0.0

    new_state = {"placed": placed, "selected": selected, "status": status}
    return [new_state, status, [0, vx], [0, vy], [0, vz], [0, vr]]


# ---------------------------------------------------------------------------
# Callback B: store -> 3D figure
# ---------------------------------------------------------------------------

@callback(
    Output("scene3d", "figure"),
    Input("store-state", "data"),
    Input("store-drone", "data"),
)
def render_figure(state, drone):
    state = state or {}
    placed = state.get("placed", {}) if isinstance(state, dict) else {}
    selected = state.get("selected") if isinstance(state, dict) else None
    auton = drone if (isinstance(drone, dict) and drone.get("active")) else None
    return build_figure(placed, selected_key=selected, autonomy=auton)


# ---------------------------------------------------------------------------
# Callback C: store -> editor heading + slider visibility + remove btn
# ---------------------------------------------------------------------------

@callback(
    Output("editor-heading", "children"),
    Output("slider-panel", "style"),
    Output("btn-remove", "disabled"),
    Output("slider-x", "disabled"),
    Output("slider-y", "disabled"),
    Output("slider-z", "disabled"),
    Output("slider-rot", "disabled"),
    Input("store-state", "data"),
)
def render_editor_ui(state):
    state = state or {}
    placed = state.get("placed", {}) if isinstance(state, dict) else {}
    selected = state.get("selected") if isinstance(state, dict) else None
    has_sel = selected is not None and selected in placed
    if has_sel:
        heading = f"Editing: {COMPONENT_LIBRARY[selected]['label']}"
        style = {"display": "block"}
    else:
        heading = "No component selected"
        style = {"display": "none"}
    sliders_disabled = not has_sel
    return [heading, style, not has_sel,
            sliders_disabled, sliders_disabled, sliders_disabled, sliders_disabled]


# ---------------------------------------------------------------------------
# Callback D: AERO-1 autonomy heartbeat (the robot's own mind)
# ---------------------------------------------------------------------------

STATE_COLORS = {
    "IDLE": "#95a5a6", "PATROL": "#2ecc71", "GRAB": "#FFB84D",
    "TRANSPORT": "#3AA7F0", "EVASION": "#e74c3c", "LANDING": "#4ECDC4",
}


@callback(
    Output("store-drone", "data"),
    Output("t-state", "children"),
    Output("t-state", "style"),
    Output("t-pos", "children"),
    Output("t-event", "children"),
    Output("sim-timer", "interval"),
    Output("btn-sim", "n_clicks"),
    Output("btn-sim-stop", "n_clicks"),
    Input("sim-timer", "n_intervals"),
    Input("btn-sim", "n_clicks"),
    Input("btn-sim-stop", "n_clicks"),
    State("store-drone", "data"),
    State("store-state", "data"),
)
def sim_heartbeat(n_ticks, sim_clicks, stop_clicks, drone, state):
    drone = drone if isinstance(drone, dict) else {}
    # ensure the drone dict always has the keys the FSM needs
    for k, default in (("x", 0.0), ("y", 0.0), ("z", 16.0), ("vx", 0.0), ("vy", 0.0), ("vz", 0.0),
                       ("yaw", 0.0), ("speed", 0.0), ("state", "IDLE"), ("tilt", 0.0),
                       ("grabbed", None), ("target", None), ("evade_dir", None),
                       ("event", ""), ("t", 0.0), ("t_phase", 0.0), ("trail", []),
                       ("hook", False), ("active", False)):
        drone.setdefault(k, default)
    state = state if isinstance(state, dict) else {}
    placed = state.get("placed", {})

    ctx = callback_context
    def _trigger_id(t):
        key = next(iter(t)) if t else ""
        return key.rsplit(".", 1)[0] if "." in key else key
    triggered = [_trigger_id(t) for t in ctx.triggered] if ctx.triggered else []

    active = bool(drone.get("active"))
    if "btn-sim" in triggered:
        active = True
        drone["active"] = True
        drone["event"] = "Autonomy engaged - patrol loop started"
    if "btn-sim-stop" in triggered:
        active = False
        drone["active"] = False
        drone["event"] = "Autonomy suspended by operator"
        drone["trail"] = []

    if active:
        drone = step_autonomy(drone, placed)

    interval = 400 if active else 0
    color = STATE_COLORS.get(drone.get("state", "IDLE"), "#95a5a6")
    pos_str = f"({drone.get('x', 0):.0f}, {drone.get('y', 0):.0f}, {drone.get('z', 0):.0f})"
    event = drone.get("event", "") or "standing by"

    return (
        drone,
        drone.get("state", "IDLE"),
        {"color": color, "fontWeight": "bold", "fontFamily": "monospace",
         "backgroundColor": "rgba(0,0,0,0.35)", "padding": "1px 8px",
         "borderRadius": "4px", "fontSize": "12px"},
        pos_str,
        event,
        interval,
        0,
        0,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("  3D Robot Layout Designer")
    print(f"  URL:  http://127.0.0.1:8050")
    print(f"  Save: {LAYOUT_FILE}")
    print("=" * 50)
    app.run(debug=False, host="127.0.0.1", port=8050)
