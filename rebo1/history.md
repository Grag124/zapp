# Current Directive
**BUILD_ADVANCED_3D_ROBOT_DESIGNER**

> **CRITICAL WORKSPACE INSTRUCTION:** We are building a massive, long-term robotics project. Every time the user starts a new task and says "check history.md", you must automatically read this file, look at the Active Backlog, and pick up exactly where we left off, writing the code entirely hands-free.

## Strict Logging Protocol (ENFORCED)

These rules are **mandatory** and take effect immediately:

1. **PRE-LOGGING REQ:** Before you create any new file or rewrite an existing file, you must IMMEDIATELY open `history.md` and log what you are about to do under "Active Backlog" with an `[IN PROGRESS]` tag.
2. **CLEANUP REQ:** The very second a module or fix is completed and tested, you must immediately remove the `[IN PROGRESS]` tag, move that exact item down into the `# Completed Logs` section with a green checkmark, and write a summary of what you accomplished.
3. **FLUSH REQ:** Never leave ghost files or dead items in the progress pool. If a task fails or is paused, it must immediately be updated to `[NOT FINISHED]` with a technical breakdown of the roadblock.

---

## 3D Layout Designer - Sub-Goal

> **Sub-Goal:** Build a Dash/Plotly 3D robot layout designer in `robot_3d_designer/` that lets users visually place chassis, motors, sensors, battery, and wing components on a 3D robot canvas. This is the "designer" half of the ultimate goal - a design tool before physical build.

**Next development phase:**
- Create `robot_3d_designer/` folder
- Build `designer_app.py` - Dash app with Plotly 3D scene
- Interactive component palette: chassis, motors, wheels, sensor, battery, wing, servo, wooden stick axle
- Each component has a 3D geometry, default position, and editable color
- Save/load layout to JSON

---

**CONTINUE_WORK_ON_UNFINISHED_TASKS**

> **Resumption note:** AERO-1 upgraded to a fully autonomous flying robot in the 3D designer: patrol + wall avoidance + object grabbing + emergency collision response. All flows verified in-process + via live Dash server. Remaining: physical build + H-bridge/sensor acquisition.

---

# Project State

- **Ultimate Goal:** The most advanced cardboard robot ever built - flying cardboard robot with AI-powered obstacle avoidance.
- **Workspace:** `/home/bekawakesa10/.cline/data/workspaces/chat/rebo1/`

**Current `/rebo1/robot_brain.py` file setup:**
- `Robot` class with auto mode detection (simulation/hardware)
- `control_wheels(direction)` - drives motors (hardware) or logs (sim)
- `calculate_lift_power(mass_grams)` - physics: thrust (N) = mass (kg) x 9.81
- Console loop: W/A/S/D/Q/M/R/L via `input().strip().lower()`, invalid-command handling, `time.sleep(0.1)` throttle
- `RobotMotors`, `ObstacleSensor`, `AIBrain` all wired in

**Current `/rebo1/robot_3d_designer/designer_app.py` file setup:**
- Dash 2.18.2 + Plotly 7.x web app (downgraded from 4.4.1 to fix dcc.Store-as-Output bug)
- 16 component library entries (chassis, 4x motors, 4x wheels, sensor, battery, brain, wing, servo, 2x axles)
- 3D Mesh3d scene: floor grid, arena wireframe cage, green home pad, axis labels
- Plain-id palette buttons (btn-*) to add components; click in 3D scene selects a part
- Selected part gets a yellow Mesh3d highlight overlay + yellow label; X/Y/Z + rotation sliders
  enable automatically when a part is selected (render_editor_ui toggles `disabled`)
- Save/Load layout to `layout.json`; Clear + Remove buttons
- AERO-1: a four-rotor flying robot (drone body + prop blades + claw + sensor dome) that
  runs a behavior state machine (IDLE -> PATROL -> GRAB -> TRANSPORT -> EVASION -> LANDING):
  patrols a corridor sized to the largest placed part, repels off arena walls,
  grabs transportable parts and carries them, and on collision triggers an
  emergency evasion burst + cargo drop, then recovers to patrol.
  A dcc.Interval heartbeat (sim_heartbeat, 400 ms) drives it; a telemetry bar
  shows live state badge, position and last event.
- Architecture: store-state (designer) + store-drone (autonomy); on_action /
  render_figure / render_editor_ui / sim_heartbeat read stores only (no loops).
- Run: `cd robot_3d_designer && python3 designer_app.py` -> http://127.0.0.1:8050

---

# Active Backlog & Bugs

- [NOT FINISHED] Physical cardboard robot build (chassis, motors, wheels, flying wing, servo).
- [NOT FINISHED] Motor controller (H-bridge) acquisition; sensors/camera acquisition.

---

# Completed Logs

- Created `robot_brain.py` - simulation console control (W/A/S/D/Q) + lift physics. OK
- Created `ai_brain.py` - `AIBrain` decision layer (manual/autonomous). OK
- Created `motor_control.py` - `RobotMotors` (gpiozero, L298N/TB6612, safe fallback). OK
- Created `sensors.py` - `ObstacleSensor` (gpiozero, HC-SR04, safe fallback). OK
- Integrated `RobotMotors` + `ObstacleSensor` + `AIBrain` into `robot_brain.py` - simulation/hardware auto-detection, console + autonomous mode. OK
- Updated console commands: W/A/S/D/Q + M (toggle autonomous), R (read distance), L (lift power test). OK
- Updated `history.md` - backlog refreshed, resumption note cleared. OK

- Created `build_plan.md` and `shopping_list.md`. OK
- Local imports validated (see `__pycache__/`). OK
- Created `history.md` - persistent memory initialized. OK

- Added Strict Logging Protocol (PRE-LOGGING / CLEANUP / FLUSH) to `history.md`. OK
- Created `robot_3d_designer/` folder. OK
- Built `robot_3d_designer/designer_app.py` code (16-component palette, X/Y/Z sliders, JSON save/load, Mesh3d scene, figure builder + JSON round-trip tested). **INTERACTIVE CALLBACKS UNVERIFIED — blocked by Dash 4.4.1 `dcc.Store`-as-Output validation bug (white screen).**

- Downgraded Dash 4.4.1 → 2.18.2 (fixes dcc.Store-as-Output "Wrong length output_spec" bug). OK
- Rewrote `robot_3d_designer/designer_app.py` for Dash 2.18.2:
  - Sliders always present in layout (hidden when no selection) — fixes "nonexistent object in Input" white screen
  - 16 plain-id palette buttons (replaced broken pattern-matching approach)
  - One dcc.Store holds all state; on_action writes store+status+sliders;
    render_figure / render_editor_ui read store only (no self-referential Input/Output loops)
  - All 4 interactive flows verified via HTTP POST: add component, move with slider, save JSON, load JSON. OK

- Fixed `dict(mesh)` crash on selected-component highlight (rebuilds a fresh go.Mesh3d overlay). OK
- Added `dcc.Store(id="store-state")` explicitly to the layout tree (Dash 2.18.2 raises "nonexistent object" otherwise). OK
- Fixed `on_action` missing keyword-only `state` arg: signature is now `def on_action(*args)` with state at `args[27]` (27 Inputs + 1 State). OK
- Enabled sliders: removed permanent `disabled=True`; `render_editor_ui` now also outputs the 4 slider `disabled` props so they toggle with selection. OK
- Added AERO-1 autonomous flying robot to the 3D designer:
  - `step_autonomy()`: finite-state machine (IDLE/PATROL/GRAB/TRANSPORT/EVASION/LANDING) with
    wall repulsion, part collision detection, emergency evasion + cargo drop, motion trail
  - `_drone_body()`: X-quad drone (fuselage, 4 motor hubs, prop blades, claw, sensor dome)
  - `sim_heartbeat` callback + `dcc.Interval` (400 ms) drive the simulation; Start/Stop buttons +
    telemetry HUD (state badge, position, event log)
  - Arena wireframe + home pad rendered in `build_figure`; drone/trail/cargo overlay when active
- Verified in-process (mocked callback context): palette add, slider move/rotate, scene-click select,
  remove, save/load round-trip, 25-tick flight loop, collision→EVASION+drop, render figures with
  drone + trail serialize to JSON, all 4 callbacks + layout component ids present. OK
- Verified live: `GET /` -> 200, 4 callbacks registered on the running Dash 2.18.2 server. OK
