
import streamlit as st
import math
import json
import html
import uuid
from datetime import datetime

from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="VoltForge | AI Engineering Design Assistant",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    .main-title {
        font-size: 38px;
        font-weight: 800;
        color: #1f6feb;
        margin-bottom: 0;
    }
    .subtitle {
        color: #777;
        margin-top: 3px;
        margin-bottom: 25px;
    }
    .metric-card {
        background: #f0f5ff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #d5e2ff;
    }
    .section-title {
        font-size: 22px;
        font-weight: 700;
        margin-top: 12px;
    }
    div[data-testid="stMetric"] {
        background: #f7f9fc;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# COMPONENT CATALOG
# ============================================================

COMPONENTS = {
    "Supply": {
        "category": "Power",
        "description": "Three-phase incoming power supply",
        "rating": "415 V AC",
        "symbol": "SUPPLY",
        "color": "#dbeafe"
    },
    "MPCB": {
        "category": "Protection",
        "description": "Motor protection circuit breaker",
        "rating": "Adjustable",
        "symbol": "MPCB",
        "color": "#fee2e2"
    },
    "Contactor": {
        "category": "Switching",
        "description": "Electromagnetic power contactor",
        "rating": "AC-3 rated",
        "symbol": "KM",
        "color": "#fef3c7"
    },
    "Overload Relay": {
        "category": "Protection",
        "description": "Thermal overload protection relay",
        "rating": "Adjustable",
        "symbol": "OLR",
        "color": "#ffedd5"
    },
    "Motor": {
        "category": "Load",
        "description": "Three-phase induction motor",
        "rating": "As specified",
        "symbol": "M",
        "color": "#dcfce7"
    },
    "Control Supply": {
        "category": "Control",
        "description": "Control circuit supply",
        "rating": "24 V DC",
        "symbol": "PS",
        "color": "#ede9fe"
    },
    "STOP": {
        "category": "Control",
        "description": "Normally closed stop push button",
        "rating": "NC",
        "symbol": "STOP",
        "color": "#fee2e2"
    },
    "START": {
        "category": "Control",
        "description": "Normally open start push button",
        "rating": "NO",
        "symbol": "START",
        "color": "#dcfce7"
    },
    "Contactor Coil": {
        "category": "Control",
        "description": "Contactor operating coil",
        "rating": "24 V DC",
        "symbol": "A1/A2",
        "color": "#e0e7ff"
    },
    "Timer": {
        "category": "Control",
        "description": "Time delay relay",
        "rating": "Adjustable",
        "symbol": "T",
        "color": "#f3e8ff"
    }
}


# ============================================================
# POSITION COMPATIBILITY
# ============================================================

def get_node_position(node):
    """
    Supports Streamlit Flow versions exposing coordinates
    through either 'pos' or 'position'.
    """

    position = getattr(node, "position", None)

    if position is None:
        position = getattr(node, "pos", None)

    if position is None:
        return 0.0, 0.0

    if isinstance(position, dict):
        return (
            float(position.get("x", 0)),
            float(position.get("y", 0))
        )

    if isinstance(position, (tuple, list)):
        return (
            float(position[0]),
            float(position[1])
        )

    if hasattr(position, "x") and hasattr(position, "y"):
        return (
            float(position.x),
            float(position.y)
        )

    return 0.0, 0.0


def get_node_by_id(nodes, node_id):
    for node in nodes:
        if node.id == node_id:
            return node
    return None


# ============================================================
# ELECTRICAL CALCULATIONS
# ============================================================

def calculate_motor_current(power_kw, voltage, power_factor, efficiency, phase):
    """
    Estimates motor full-load current.

    Three phase:
        I = P / (sqrt(3) * V * PF * efficiency)

    Single phase:
        I = P / (V * PF * efficiency)
    """

    power_w = power_kw * 1000

    if phase == "Three Phase":
        current = power_w / (
            math.sqrt(3) * voltage * power_factor * efficiency
        )
    else:
        current = power_w / (
            voltage * power_factor * efficiency
        )

    return current


def recommend_components(current):
    """
    Illustrative component selection.
    Final ratings must be checked against manufacturer data,
    applicable standards, installation conditions and coordination.
    """

    mpcb_options = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100]
    contactor_options = [9, 12, 18, 25, 32, 40, 50, 65, 80, 95]
    olr_options = [1.6, 2.5, 4, 6, 10, 13, 18, 25, 32, 40, 50, 63, 80, 100]

    def next_rating(value, options):
        for rating in options:
            if rating >= value:
                return rating
        return options[-1]

    return {
        "MPCB": next_rating(current * 1.25, mpcb_options),
        "Contactor": next_rating(current * 1.25, contactor_options),
        "Overload Relay": next_rating(current, olr_options)
    }


# ============================================================
# NODE CREATION
# ============================================================

def make_node(
    component,
    x,
    y,
    rating=None,
    custom_name=None,
    node_id=None
):
    component_info = COMPONENTS.get(
        component,
        {
            "category": "Other",
            "description": "Custom component",
            "rating": "Not specified",
            "symbol": component,
            "color": "#e5e7eb"
        }
    )

    label = custom_name or component

    node_data = {
        "label": label,
        "component": component,
        "rating": str(rating or component_info["rating"]),
        "description": component_info["description"],
        "category": component_info["category"],
        "symbol": component_info["symbol"],
        "color": component_info["color"]
    }

    return StreamlitFlowNode(
        id=node_id or str(uuid.uuid4())[:8],
        pos=(float(x), float(y)),
        data=node_data,
        node_type="default",
        source_position="right",
        target_position="left",
        draggable=True,
        selectable=True,
        connectable=True
    )


def make_edge(source, target, label=""):
    return StreamlitFlowEdge(
        id=str(uuid.uuid4())[:8],
        source=source,
        target=target,
        label=label,
        animated=False
    )


# ============================================================
# DEFAULT CIRCUIT GENERATION
# ============================================================

def generate_design(current, ratings):
    nodes = []
    edges = []

    power_components = [
        ("Supply", 50, 130, "415 V AC"),
        ("MPCB", 270, 130, f'{ratings["MPCB"]} A'),
        ("Contactor", 490, 130, f'{ratings["Contactor"]} A'),
        ("Overload Relay", 710, 130, f'{ratings["Overload Relay"]} A'),
        ("Motor", 930, 130, f"{current:.2f} A FLC")
    ]

    power_ids = []

    for component, x, y, rating in power_components:
        node = make_node(component, x, y, rating)
        nodes.append(node)
        power_ids.append(node.id)

    for i in range(len(power_ids) - 1):
        edges.append(make_edge(power_ids[i], power_ids[i + 1]))

    control_components = [
        ("Control Supply", 50, 390, "24 V DC"),
        ("STOP", 270, 390, "NC"),
        ("START", 490, 390, "NO"),
        ("Contactor Coil", 710, 390, "24 V DC")
    ]

    control_ids = []

    for component, x, y, rating in control_components:
        node = make_node(component, x, y, rating)
        nodes.append(node)
        control_ids.append(node.id)

    for i in range(len(control_ids) - 1):
        edges.append(make_edge(control_ids[i], control_ids[i + 1]))

    return nodes, edges


# ============================================================
# SVG COMPONENT DRAWING
# ============================================================

def component_svg(component, x, y, rating, label=None):
    """
    Generates a small visual component illustration for
    the exported circuit diagram.
    """

    label = label or component
    safe_label = html.escape(str(label))
    safe_rating = html.escape(str(rating))

    colors = {
        "Supply": "#2563eb",
        "MPCB": "#dc2626",
        "Contactor": "#d97706",
        "Overload Relay": "#ea580c",
        "Motor": "#16a34a",
        "Control Supply": "#7c3aed",
        "STOP": "#dc2626",
        "START": "#16a34a",
        "Contactor Coil": "#4f46e5",
        "Timer": "#9333ea"
    }

    color = colors.get(component, "#475569")

    shapes = {
        "Supply": """
            <rect x="0" y="0" width="68" height="48" rx="5"
                  fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
            <path d="M15 12 V36 M34 12 V36 M53 12 V36"
                  stroke="#2563eb" stroke-width="3"/>
        """,
        "MPCB": """
            <rect x="0" y="0" width="68" height="48" rx="5"
                  fill="#fee2e2" stroke="#dc2626" stroke-width="2"/>
            <path d="M13 12 L29 30 L44 12 L56 30"
                  fill="none" stroke="#dc2626" stroke-width="3"/>
            <circle cx="34" cy="10" r="3" fill="#dc2626"/>
        """,
        "Contactor": """
            <rect x="0" y="0" width="68" height="48" rx="5"
                  fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
            <rect x="10" y="10" width="48" height="28"
                  fill="none" stroke="#d97706" stroke-width="2"/>
            <path d="M18 24 H50 M34 10 V38"
                  stroke="#d97706" stroke-width="2"/>
        """,
        "Overload Relay": """
            <rect x="0" y="0" width="68" height="48" rx="5"
                  fill="#ffedd5" stroke="#ea580c" stroke-width="2"/>
            <path d="M12 12 Q20 38 28 12 Q36 38 44 12 Q52 38 58 12"
                  fill="none" stroke="#ea580c" stroke-width="2"/>
        """,
        "Motor": """
            <circle cx="34" cy="24" r="22"
                    fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
            <text x="34" y="30" text-anchor="middle"
                  font-size="18" font-weight="bold" fill="#16a34a">M</text>
        """,
        "Control Supply": """
            <rect x="0" y="0" width="68" height="48" rx="5"
                  fill="#ede9fe" stroke="#7c3aed" stroke-width="2"/>
            <path d="M12 24 H25 L34 12 L43 36 L52 24 H58"
                  fill="none" stroke="#7c3aed" stroke-width="2"/>
        """,
        "STOP": """
            <circle cx="34" cy="24" r="20"
                    fill="#fee2e2" stroke="#dc2626" stroke-width="2"/>
            <path d="M20 24 H48" stroke="#dc2626" stroke-width="4"/>
        """,
        "START": """
            <circle cx="34" cy="24" r="20"
                    fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
            <path d="M34 12 V36 M22 24 H46"
                  stroke="#16a34a" stroke-width="3"/>
        """,
        "Contactor Coil": """
            <rect x="0" y="0" width="68" height="48" rx="5"
                  fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
            <path d="M12 24 Q18 8 24 24 Q30 40 36 24 Q42 8 48 24"
                  fill="none" stroke="#4f46e5" stroke-width="2"/>
        """,
        "Timer": """
            <circle cx="34" cy="24" r="21"
                    fill="#f3e8ff" stroke="#9333ea" stroke-width="2"/>
            <path d="M34 12 V24 L45 30"
                  stroke="#9333ea" stroke-width="2.5" fill="none"/>
        """
    }

    shape = shapes.get(
        component,
        f'<rect x="0" y="0" width="68" height="48" rx="5" fill="#f1f5f9" stroke="{color}" stroke-width="2"/>'
    )

    return f"""
    <g transform="translate({x},{y})">
        {shape}
        <text x="34" y="64" text-anchor="middle"
              font-size="12" font-weight="bold" fill="#172554">
              {safe_label}
        </text>
        <text x="34" y="79" text-anchor="middle"
              font-size="10" fill="#475569">
              {safe_rating}
        </text>
    </g>
    """


# ============================================================
# CIRCUIT SVG GENERATION
# ============================================================

def create_circuit_svg(state):
    nodes = list(state.nodes)
    edges = list(state.edges)

    if not nodes:
        return None

    positions = {
        node.id: get_node_position(node)
        for node in nodes
    }

    min_x = min(pos[0] for pos in positions.values())
    min_y = min(pos[1] for pos in positions.values())
    max_x = max(pos[0] for pos in positions.values())
    max_y = max(pos[1] for pos in positions.values())

    width = max(1100, int(max_x - min_x + 250))
    height = max(650, int(max_y - min_y + 200))

    offset_x = 80 - min_x
    offset_y = 90 - min_y

    svg_parts = []

    svg_parts.append(f"""
    <svg xmlns="http://www.w3.org/2000/svg"
         width="{width}" height="{height}"
         viewBox="0 0 {width} {height}">

        <rect width="100%" height="100%" fill="#ffffff"/>

        <text x="40" y="38" font-size="24"
              font-weight="bold" fill="#1e3a8a">
              VoltForge - Generated Circuit Diagram
        </text>

        <text x="40" y="62" font-size="12" fill="#64748b">
              Generated: {datetime.now().strftime("%d-%m-%Y %H:%M")}
        </text>
    """)

    # Draw connections first, behind components.
    for edge in edges:
        source_pos = positions.get(edge.source)
        target_pos = positions.get(edge.target)

        if source_pos is None or target_pos is None:
            continue

        sx = source_pos[0] + offset_x + 68
        sy = source_pos[1] + offset_y + 24
        tx = target_pos[0] + offset_x
        ty = target_pos[1] + offset_y + 24

        mid_x = (sx + tx) / 2

        svg_parts.append(f"""
            <path d="M {sx} {sy} H {mid_x} V {ty} H {tx}"
                  stroke="#334155" stroke-width="2.5"
                  fill="none"/>
            <circle cx="{tx}" cy="{ty}" r="3" fill="#334155"/>
        """)

    # Draw components.
    for node in nodes:
        x, y = positions[node.id]

        data = node.data or {}

        component = data.get("component", "Custom")
        label = data.get("label", component)
        rating = data.get("rating", "")

        svg_parts.append(
            component_svg(
                component,
                x + offset_x,
                y + offset_y,
                rating,
                label
            )
        )

    svg_parts.append("""
        <text x="40" y="620" font-size="11" fill="#64748b">
            Conceptual engineering layout only. Verify electrical ratings,
            protection coordination, wiring and applicable standards before implementation.
        </text>
    </svg>
    """)

    return "\n".join(svg_parts)


# ============================================================
# JSON EXPORT
# ============================================================

def export_design_json(state, specifications):
    result = {
        "project": "VoltForge",
        "generated_at": datetime.now().isoformat(),
        "specifications": specifications,
        "components": [],
        "connections": []
    }

    for node in state.nodes:
        data = node.data or {}
        x, y = get_node_position(node)

        result["components"].append({
            "id": node.id,
            "component": data.get("component", ""),
            "label": data.get("label", ""),
            "rating": data.get("rating", ""),
            "description": data.get("description", ""),
            "position": {
                "x": x,
                "y": y
            }
        })

    for edge in state.edges:
        result["connections"].append({
            "id": edge.id,
            "source": edge.source,
            "target": edge.target,
            "label": getattr(edge, "label", "")
        })

    return json.dumps(result, indent=4)


# ============================================================
# INITIAL SESSION STATE
# ============================================================

if "flow_state" not in st.session_state:
    initial_nodes, initial_edges = generate_design(
        10.0,
        {
            "MPCB": 16,
            "Contactor": 18,
            "Overload Relay": 10
        }
    )

    st.session_state.flow_state = StreamlitFlowState(
        nodes=initial_nodes,
        edges=initial_edges
    )

if "specifications" not in st.session_state:
    st.session_state.specifications = {}

if "calculated_current" not in st.session_state:
    st.session_state.calculated_current = 10.0

if "recommended_ratings" not in st.session_state:
    st.session_state.recommended_ratings = {
        "MPCB": 16,
        "Contactor": 18,
        "Overload Relay": 10
    }


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">⚡ VoltForge</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">AI-Assisted Electrical Engineering Design Assistant</div>',
    unsafe_allow_html=True
)

st.info(
    "VoltForge converts motor specifications into an editable "
    "starter-panel design concept with component recommendations "
    "and downloadable design evidence."
)


# ============================================================
# TABS
# ============================================================

tab_design, tab_editor, tab_catalog, tab_evidence, tab_architecture = st.tabs([
    "Design Workspace",
    "Circuit Editor",
    "Component Catalog",
    "Design Evidence",
    "System Architecture"
])


# ============================================================
# TAB 1 - DESIGN WORKSPACE
# ============================================================

with tab_design:

    st.markdown("## Motor and Panel Specifications")

    with st.form("motor_specification_form"):

        col1, col2, col3 = st.columns(3)

        with col1:
            motor_power = st.number_input(
                "Motor Power (kW)",
                min_value=0.1,
                max_value=500.0,
                value=7.5,
                step=0.5
            )

            voltage = st.selectbox(
                "Supply Voltage (V)",
                [230, 400, 415, 440, 690],
                index=2
            )

        with col2:
            phase = st.selectbox(
                "Phase",
                ["Three Phase", "Single Phase"]
            )

            power_factor = st.slider(
                "Power Factor",
                min_value=0.50,
                max_value=1.00,
                value=0.85,
                step=0.01
            )

        with col3:
            efficiency_percent = st.slider(
                "Motor Efficiency (%)",
                min_value=50,
                max_value=99,
                value=90
            )

            control_voltage = st.selectbox(
                "Control Voltage",
                ["24 V DC", "110 V AC", "230 V AC"]
            )

        submitted = st.form_submit_button(
            "Generate Design",
            type="primary",
            use_container_width=True
        )

    if submitted:

        efficiency = efficiency_percent / 100

        current = calculate_motor_current(
            motor_power,
            voltage,
            power_factor,
            efficiency,
            phase
        )

        ratings = recommend_components(current)

        st.session_state.calculated_current = current
        st.session_state.recommended_ratings = ratings

        st.session_state.specifications = {
            "motor_power_kw": motor_power,
            "voltage": voltage,
            "phase": phase,
            "power_factor": power_factor,
            "efficiency_percent": efficiency_percent,
            "control_voltage": control_voltage,
            "estimated_full_load_current_A": round(current, 2)
        }

        nodes, edges = generate_design(current, ratings)

        # Apply the selected control voltage to the control devices.
        for node in nodes:
            data = node.data or {}
            if data.get("component") in [
                "Control Supply",
                "Contactor Coil"
            ]:
                data["rating"] = control_voltage
                node.data = data

        st.session_state.flow_state = StreamlitFlowState(
            nodes=nodes,
            edges=edges
        )

        st.success("Design generated successfully.")

    if st.session_state.specifications:

        st.markdown("### Calculated Design Summary")

        current = st.session_state.calculated_current
        ratings = st.session_state.recommended_ratings

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Motor Power", f'{st.session_state.specifications["motor_power_kw"]} kW')
        c2.metric("Supply Voltage", f'{st.session_state.specifications["voltage"]} V')
        c3.metric("Estimated FLC", f"{current:.2f} A")
        c4.metric("Phase", st.session_state.specifications["phase"])

        st.markdown("### Suggested Components")

        component_table = [
            {
                "Component": "MPCB",
                "Suggested Rating": f'{ratings["MPCB"]} A',
                "Purpose": "Motor short-circuit and overload protection"
            },
            {
                "Component": "Contactor",
                "Suggested Rating": f'{ratings["Contactor"]} A',
                "Purpose": "Motor switching"
            },
            {
                "Component": "Overload Relay",
                "Suggested Rating": f'{ratings["Overload Relay"]} A',
                "Purpose": "Thermal overload protection"
            },
            {
                "Component": "Control Supply",
                "Suggested Rating": st.session_state.specifications["control_voltage"],
                "Purpose": "Control circuit supply"
            }
        ]

        st.table(component_table)

        st.warning(
            "These are preliminary illustrative selections, not certified "
            "electrical design ratings. Confirm motor nameplate current, "
            "starting method, fault level, cable sizing, ambient conditions, "
            "manufacturer coordination tables and applicable standards."
        )

    else:
        st.caption(
            "Enter the motor details and click Generate Design "
            "to create a circuit concept."
        )


# ============================================================
# TAB 2 - CIRCUIT EDITOR
# ============================================================

with tab_editor:

    st.markdown("## Editable Circuit Design")

    st.caption(
        "Drag components to reposition them. Use the controls below "
        "to add, edit, remove and connect components."
    )

    state = st.session_state.flow_state

    try:
        updated_state = streamlit_flow(
            key="voltforge_flow_editor",
            state=state,
            fit_view=True,
            show_minimap=True,
            show_controls=True,
            allow_zoom=True,
            pan_on_drag=True
        )

        if updated_state is not None:
            st.session_state.flow_state = updated_state

    except Exception as error:
        st.error("The circuit editor could not render.")
        st.exception(error)

    state = st.session_state.flow_state
    nodes = list(state.nodes)

    st.divider()
    st.markdown("### Add Component")

    add_col1, add_col2 = st.columns([2, 1])

    with add_col1:
        new_component = st.selectbox(
            "Select component to add",
            list(COMPONENTS.keys()),
            key="add_component_select"
        )

    with add_col2:
        if st.button("＋ Add Component", use_container_width=True):

            x = 150 + (len(nodes) % 4) * 190
            y = 550 + (len(nodes) // 4) * 150

            new_node = make_node(
                new_component,
                x,
                y
            )

            state.nodes.append(new_node)
            st.session_state.flow_state = state

            st.success(f"{new_component} added.")
            st.rerun()

    st.divider()
    st.markdown("### Edit or Remove Component")

    state = st.session_state.flow_state
    nodes = list(state.nodes)

    if nodes:

        node_options = {
            f'{(node.data or {}).get("label", node.id)} ({node.id})': node.id
            for node in nodes
        }

        selected_label = st.selectbox(
            "Select component",
            list(node_options.keys()),
            key="selected_component_for_edit"
        )

        selected_id = node_options[selected_label]
        selected_node = get_node_by_id(nodes, selected_id)

        if selected_node is not None:

            selected_data = selected_node.data or {}

            edit_col1, edit_col2 = st.columns(2)

            with edit_col1:
                edited_label = st.text_input(
                    "Component name",
                    value=str(selected_data.get("label", "")),
                    key="edit_component_label"
                )

            with edit_col2:
                edited_rating = st.text_input(
                    "Component rating",
                    value=str(selected_data.get("rating", "")),
                    key="edit_component_rating"
                )

            save_col, delete_col = st.columns(2)

            with save_col:
                if st.button(
                    "Save Component Changes",
                    type="primary",
                    use_container_width=True
                ):

                    selected_data["label"] = edited_label
                    selected_data["rating"] = edited_rating
                    selected_node.data = selected_data

                    st.session_state.flow_state = state
                    st.success("Component updated.")
                    st.rerun()

            with delete_col:
                if st.button(
                    "Delete Component",
                    use_container_width=True
                ):

                    state.nodes = [
                        node for node in state.nodes
                        if node.id != selected_id
                    ]

                    state.edges = [
                        edge for edge in state.edges
                        if edge.source != selected_id
                        and edge.target != selected_id
                    ]

                    st.session_state.flow_state = state
                    st.success("Component deleted.")
                    st.rerun()

    else:
        st.info("No components in the circuit.")

    st.divider()
    st.markdown("### Connect Components")

    state = st.session_state.flow_state
    nodes = list(state.nodes)

    if len(nodes) >= 2:

        node_options = {
            f'{(node.data or {}).get("label", node.id)} ({node.id})': node.id
            for node in nodes
        }

        connect_col1, connect_col2 = st.columns(2)

        with connect_col1:
            source_label = st.selectbox(
                "From component",
                list(node_options.keys()),
                key="edge_source"
            )

        with connect_col2:
            target_label = st.selectbox(
                "To component",
                list(node_options.keys()),
                index=1,
                key="edge_target"
            )

        if st.button("Connect Components", use_container_width=True):

            source_id = node_options[source_label]
            target_id = node_options[target_label]

            if source_id == target_id:
                st.error("A component cannot connect to itself.")

            else:
                existing = any(
                    edge.source == source_id and edge.target == target_id
                    for edge in state.edges
                )

                if existing:
                    st.warning("This connection already exists.")
                else:
                    state.edges.append(
                        make_edge(source_id, target_id)
                    )

                    st.session_state.flow_state = state
                    st.success("Connection added.")
                    st.rerun()

    else:
        st.caption("Add at least two components to create a connection.")

    st.divider()

    if st.button("Reset to Generated Design", use_container_width=True):

        if st.session_state.specifications:

            current = st.session_state.calculated_current
            ratings = st.session_state.recommended_ratings

            nodes, edges = generate_design(current, ratings)

            control_voltage = st.session_state.specifications.get(
                "control_voltage",
                "24 V DC"
            )

            for node in nodes:
                data = node.data or {}

                if data.get("component") in [
                    "Control Supply",
                    "Contactor Coil"
                ]:
                    data["rating"] = control_voltage
                    node.data = data

            st.session_state.flow_state = StreamlitFlowState(
                nodes=nodes,
                edges=edges
            )

        else:
            nodes, edges = generate_design(
                10.0,
                {
                    "MPCB": 16,
                    "Contactor": 18,
                    "Overload Relay": 10
                }
            )

            st.session_state.flow_state = StreamlitFlowState(
                nodes=nodes,
                edges=edges
            )

        st.rerun()


# ============================================================
# TAB 3 - COMPONENT CATALOG
# ============================================================

with tab_catalog:

    st.markdown("## Component Catalog")

    for component, details in COMPONENTS.items():

        with st.expander(component):

            col1, col2 = st.columns([1, 3])

            with col1:
                st.markdown(
                    f"""
                    <div style="
                        background:{details["color"]};
                        border:1px solid #cbd5e1;
                        border-radius:10px;
                        height:85px;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        font-size:22px;
                        font-weight:bold;">
                        {html.escape(details["symbol"])}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.write(f'**Category:** {details["category"]}')
                st.write(f'**Description:** {details["description"]}')
                st.write(f'**Default rating:** {details["rating"]}')


# ============================================================
# TAB 4 - DESIGN EVIDENCE
# ============================================================

with tab_evidence:

    st.markdown("## Design Evidence and Export")

    state = st.session_state.flow_state

    svg = create_circuit_svg(state)

    if svg:

        st.markdown("### Generated Circuit Image")

        st.components.v1.html(
            svg,
            height=680,
            scrolling=True
        )

        st.download_button(
            label="Download Circuit SVG",
            data=svg,
            file_name="voltforge_circuit.svg",
            mime="image/svg+xml",
            use_container_width=True
        )

        design_json = export_design_json(
            state,
            st.session_state.specifications
        )

        st.download_button(
            label="Download Design JSON",
            data=design_json,
            file_name="voltforge_design.json",
            mime="application/json",
            use_container_width=True
        )

        st.markdown("### Design Summary")

        st.write(f"**Number of components:** {len(state.nodes)}")
        st.write(f"**Number of connections:** {len(state.edges)}")

        st.write("**Components in current design:**")

        for node in state.nodes:
            data = node.data or {}

            st.write(
                f'- {data.get("label", "Component")} — '
                f'{data.get("rating", "Rating not specified")}'
            )

    else:
        st.info("Add components to generate a circuit image.")


# ============================================================
# TAB 5 - SYSTEM ARCHITECTURE
# ============================================================

with tab_architecture:

    st.markdown("## VoltForge System Architecture")

    st.markdown("""
    ```text
    ┌──────────────────────────────┐
    │      Engineer Input          │
    │  Motor and Panel Parameters  │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │   Electrical Calculation     │
    │  Full Load Current Estimate  │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │   Component Recommendation   │
    │  MPCB / Contactor / OLR       │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │     Circuit Editor           │
    │  Add / Edit / Move / Connect │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │      Design Evidence         │
    │       SVG + JSON Export      │
    └──────────────────────────────┘
    ```
    """)

    st.markdown("### Current Capabilities")

    capabilities = [
        "Motor specification input",
        "Deterministic full-load current estimation",
        "Preliminary component recommendations",
        "Drag-and-drop circuit editor",
        "Component editing and deletion",
        "Manual component connections",
        "SVG circuit image export",
        "JSON design export"
    ]

    for capability in capabilities:
        st.write(f"✓ {capability}")

    st.markdown("### Important Engineering Limitation")

    st.warning(
        "VoltForge currently creates an illustrative low-voltage motor "
        "starter design concept. It does not perform electrical simulation, "
        "short-circuit calculations, cable sizing, protection coordination, "
        "or certified IEC/UL compliance verification. An electrical engineer "
        "must validate the design before real-world use."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "VoltForge | TECHgium Prototype | AI-Assisted Engineering Design"
)
