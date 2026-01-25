"""AI Ops Scorecard dashboard page for Streamlit."""

from datetime import date, timedelta
from typing import List, Optional

import streamlit as st

from test_ai.ops import OpsEventManager, OpsEvent, WeeklyAgg, ProjectType, ArtifactType
from test_ai.state import get_database


@st.cache_resource
def get_ops_manager():
    """Get cached ops manager."""
    backend = get_database()
    return OpsEventManager(backend=backend)


def render_weekly_score_card(agg: WeeklyAgg):
    """Render the main weekly score card."""
    score = agg.weekly_score
    score_color = "green" if score >= 70 else "orange" if score >= 50 else "red"

    st.markdown(
        f"""
        <div style="
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 1rem;
            margin-bottom: 1rem;
        ">
            <div style="font-size: 5rem; font-weight: bold; color: {score_color};">
                {score}
            </div>
            <div style="font-size: 1.2rem; color: #888;">
                Weekly AI Ops Score
            </div>
            <div style="font-size: 0.9rem; color: #666;">
                {agg.week_start} to {agg.week_end}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_component_scores(agg: WeeklyAgg):
    """Render the four component scores."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Output",
            f"{agg.output_score:.0f}",
            delta="35% weight",
            delta_color="off",
        )
        st.caption(f"Artifacts: {agg.artifacts} | Decisions: {agg.decisions} | Executions: {agg.executions}")

    with col2:
        st.metric(
            "Efficiency",
            f"{agg.efficiency_score:.0f}",
            delta="20% weight",
            delta_color="off",
        )
        st.caption(f"Hours saved: {agg.hours_saved:.1f} | Loop rate: {agg.loop_rate:.3f}")

    with col3:
        st.metric(
            "Impact",
            f"{agg.impact_score:.0f}",
            delta="35% weight",
            delta_color="off",
        )
        st.caption(f"Total points: {agg.impact_points}")

    with col4:
        st.metric(
            "Quality",
            f"{agg.quality_score:.0f}",
            delta="10% weight",
            delta_color="off",
        )
        st.caption(f"SNR: {agg.snr:.3f}")


def render_ops_funnel(agg: WeeklyAgg):
    """Render the ops funnel visualization."""
    st.subheader("Ops Funnel")

    # Simple bar chart data
    funnel_data = {
        "Stage": ["Sessions", "Artifacts", "Decisions", "Executions"],
        "Count": [agg.sessions, agg.artifacts, agg.decisions, agg.executions],
    }

    st.bar_chart(funnel_data, x="Stage", y="Count")


def render_impact_breakdown(agg: WeeklyAgg):
    """Render impact points by area."""
    st.subheader("Impact Breakdown")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Career", agg.career_points)
    with col2:
        st.metric("Legal", agg.legal_points)
    with col3:
        st.metric("Revenue", agg.revenue_points)

    # Simple visualization
    if agg.impact_points > 0:
        impact_data = {
            "Area": ["Career", "Legal", "Revenue"],
            "Points": [agg.career_points, agg.legal_points, agg.revenue_points],
        }
        st.bar_chart(impact_data, x="Area", y="Points")


def render_control_metrics(agg: WeeklyAgg):
    """Render loop rate and SNR control metrics."""
    st.subheader("Control Metrics")

    col1, col2 = st.columns(2)

    with col1:
        # Loop rate - lower is better
        loop_status = "Good" if agg.loop_rate < 0.1 else "Warning" if agg.loop_rate < 0.2 else "High"
        st.metric(
            "Loop Rate",
            f"{agg.loop_rate:.1%}",
            delta=f"{agg.loops} loops",
            delta_color="inverse",
        )
        st.caption(f"Status: {loop_status} (target < 20%)")

    with col2:
        # SNR - higher is better
        snr_status = "Good" if agg.snr >= 0.6 else "Warning" if agg.snr >= 0.3 else "Low"
        st.metric(
            "Signal-to-Noise Ratio",
            f"{agg.snr:.2f}",
            delta=f"outputs/sessions",
            delta_color="off",
        )
        st.caption(f"Status: {snr_status} (target >= 0.6)")


def render_weekly_trend(aggregates: List[WeeklyAgg]):
    """Render weekly score trend chart."""
    if len(aggregates) < 2:
        return

    st.subheader("Weekly Score Trend")

    trend_data = {
        "Week": [a.week_start for a in reversed(aggregates)],
        "Score": [a.weekly_score for a in reversed(aggregates)],
    }

    st.line_chart(trend_data, x="Week", y="Score")


def render_ops_event_form():
    """Render the quick ops event logging form."""
    st.subheader("Log Ops Event")

    with st.form("ops_event_form"):
        col1, col2 = st.columns(2)

        with col1:
            session_id = st.text_input("Session ID", placeholder="abc123")
            project = st.selectbox(
                "Project",
                options=[p.value for p in ProjectType],
                index=4,  # 'other' default
            )

        with col2:
            minutes_saved = st.number_input("Minutes Saved", min_value=0, value=0, step=5)
            loop = st.checkbox("Loop (redo)")

        st.markdown("**Output Flags**")
        flag_col1, flag_col2, flag_col3 = st.columns(3)

        with flag_col1:
            artifact = st.checkbox("Artifact")
            artifact_type = st.selectbox(
                "Artifact Type",
                options=[a.value for a in ArtifactType],
                disabled=not artifact,
            ) if artifact else None

        with flag_col2:
            decision_closed = st.checkbox("Decision Closed")

        with flag_col3:
            execution_done = st.checkbox("Execution Done")

        st.markdown("**Impact Points**")
        impact_col1, impact_col2, impact_col3 = st.columns(3)

        with impact_col1:
            impact_career = st.number_input("Career", min_value=0, value=0, step=1)
        with impact_col2:
            impact_legal = st.number_input("Legal", min_value=0, value=0, step=1)
        with impact_col3:
            impact_revenue = st.number_input("Revenue", min_value=0, value=0, step=1)

        submitted = st.form_submit_button("Save Event", type="primary")

        if submitted:
            if not session_id:
                st.error("Session ID is required")
                return

            if artifact and not artifact_type:
                st.error("Artifact type is required when artifact is checked")
                return

            try:
                manager = get_ops_manager()
                event = OpsEvent(
                    session_id=session_id,
                    project=project,
                    artifact=artifact,
                    artifact_type=artifact_type if artifact else None,
                    reusable=False,
                    decision_closed=decision_closed,
                    execution_done=execution_done,
                    minutes_saved=minutes_saved,
                    loop=loop,
                    impact_career=impact_career,
                    impact_legal=impact_legal,
                    impact_revenue=impact_revenue,
                )
                created = manager.create_ops_event(event)
                st.success(f"Event logged: {created.id[:8]}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to log event: {e}")


def render_recent_events(events: List[OpsEvent]):
    """Render recent ops events table."""
    st.subheader("Recent Events")

    if not events:
        st.info("No ops events found")
        return

    for event in events[:10]:
        flags = []
        if event.artifact:
            flags.append(f"artifact ({event.artifact_type})")
        if event.decision_closed:
            flags.append("decision")
        if event.execution_done:
            flags.append("execution")

        loop_badge = " [LOOP]" if event.loop else ""

        with st.expander(
            f"{event.session_id[:8]} - {event.project}{loop_badge} | Impact: {event.impact_total}"
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**ID:** {event.id[:8]}")
                st.write(f"**Session:** {event.session_id}")
                st.write(f"**Project:** {event.project}")
                st.write(f"**Flags:** {', '.join(flags) if flags else 'none'}")
            with col2:
                st.write(f"**Minutes Saved:** {event.minutes_saved}")
                st.write(f"**Career Points:** {event.impact_career}")
                st.write(f"**Legal Points:** {event.impact_legal}")
                st.write(f"**Revenue Points:** {event.impact_revenue}")


def render_ops_scorecard_page():
    """Render the main AI Ops Scorecard page."""
    st.title("AI Ops Scorecard")

    manager = get_ops_manager()

    # Week selector
    col1, col2 = st.columns([3, 1])

    with col1:
        # Get list of available weeks
        aggregates = manager.list_weekly_aggregates(limit=12)
        week_options = [a.week_start for a in aggregates] if aggregates else []

        # Add current week if not in list
        today = date.today()
        current_week_start = today - timedelta(days=today.weekday())
        current_week_str = current_week_start.isoformat()

        if current_week_str not in week_options:
            week_options.insert(0, current_week_str)

        selected_week = st.selectbox(
            "Select Week",
            options=week_options,
            index=0,
        )

    with col2:
        if st.button("Compute/Refresh", type="primary"):
            with st.spinner("Computing aggregate..."):
                week_date = date.fromisoformat(selected_week)
                manager.compute_weekly_aggregate(week_date)
                st.rerun()

    # Get the selected week's aggregate
    selected_date = date.fromisoformat(selected_week)
    agg = manager.get_weekly_aggregate(selected_date)

    if not agg:
        st.warning(f"No data for week {selected_week}. Click 'Compute/Refresh' to generate.")

        # Show event logging form even without aggregate
        st.divider()
        render_ops_event_form()
        return

    # Main score display
    render_weekly_score_card(agg)

    # Component scores
    render_component_scores(agg)

    st.divider()

    # Two-column layout for funnel and impact
    col1, col2 = st.columns(2)

    with col1:
        render_ops_funnel(agg)

    with col2:
        render_impact_breakdown(agg)

    st.divider()

    # Control metrics
    render_control_metrics(agg)

    # Weekly trend
    if len(aggregates) >= 2:
        st.divider()
        render_weekly_trend(aggregates)

    st.divider()

    # Tabs for event logging and recent events
    tab1, tab2 = st.tabs(["Log Event", "Recent Events"])

    with tab1:
        render_ops_event_form()

    with tab2:
        events = manager.list_ops_events(week_start=selected_date, limit=20)
        render_recent_events(events)
