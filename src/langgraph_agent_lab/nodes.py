"""Node skeletons for the LangGraph workflow.

Each function should be small, testable, and return a partial state update. Avoid mutating the
input state in place.
"""

from __future__ import annotations

from .state import AgentState, ApprovalDecision, Route, make_event


def intake_node(state: AgentState) -> dict:
    """Normalize raw query into state fields.

    TODO(student): add normalization, PII checks, and metadata extraction.
    """
    query = state.get("query", "").strip()
    return {
        "query": query,
        "messages": [f"intake:{query[:40]}"],
        "events": [make_event("intake", "completed", "query normalized")],
    }


def classify_node(state: AgentState) -> dict:
    """Classify the query into a route using keyword-based heuristics.

    Priority: Risky > Tool > Missing Info > Error > Simple.
    """
    import re
    query = state.get("query", "").lower()
    # Normalize by removing punctuation for word boundary matching
    clean_query = re.sub(r'[^\w\s]', '', query)
    words = set(clean_query.split())

    risky_keywords = {"refund", "delete", "send", "cancel", "remove", "revoke", "account"}
    tool_keywords = {"status", "order", "lookup", "check", "track", "find", "search"}
    error_keywords = {"timeout", "fail", "failure", "error", "crash", "unavailable"}

    route = Route.SIMPLE
    risk_level = "low"

    # 1. Check Risky (Highest priority)
    if any(k in words for k in risky_keywords):
        route = Route.RISKY
        risk_level = "high"
    # 2. Check Tool
    elif any(k in words for k in tool_keywords):
        route = Route.TOOL
    # 3. Check Missing Info (e.g., "Can you fix it?")
    elif len(words) < 5 and "it" in words:
        route = Route.MISSING_INFO
    # 4. Check Error
    elif any(k in words for k in error_keywords):
        route = Route.ERROR

    return {
        "route": route.value,
        "risk_level": risk_level,
        "events": [make_event("classify", "completed", f"route={route.value}")],
    }


def ask_clarification_node(state: AgentState) -> dict:
    """Ask for missing information instead of hallucinating."""
    query = state.get("query", "")
    question = f"I'm sorry, I'm not sure what you mean by '{query}'. Could you please provide more details, such as an order ID or specific issue?"
    return {
        "pending_question": question,
        "final_answer": question,
        "events": [make_event("clarify", "completed", "missing information requested")],
    }


def tool_node(state: AgentState) -> dict:
    """Call a mock tool.

    Simulates transient failures for error-route scenarios to demonstrate retry loops.
    """
    attempt = int(state.get("attempt", 0))
    scenario_id = state.get("scenario_id", "unknown")
    route = state.get("route")

    # Simulate failure for ERROR route scenarios on first few attempts
    if route == Route.ERROR.value and attempt < 2:
        result = f"ERROR: System timed out while processing {scenario_id} (attempt {attempt})"
    else:
        result = f"SUCCESS: Action completed for {scenario_id}. Details: Mock data retrieved successfully."

    return {
        "tool_results": [result],
        "events": [make_event("tool", "completed", f"tool executed attempt={attempt}")],
    }


def risky_action_node(state: AgentState) -> dict:
    """Prepare a risky action for approval."""
    query = state.get("query", "")
    return {
        "proposed_action": f"Execute sensitive operation: '{query}'",
        "events": [make_event("risky_action", "pending_approval", "approval required")],
    }


def approval_node(state: AgentState) -> dict:
    """Human approval step with optional LangGraph interrupt().

    Set LANGGRAPH_INTERRUPT=true to use real interrupt() for HITL demos.
    Default uses mock decision so tests and CI run offline.

    TODO(student): implement reject/edit decisions and timeout escalation.
    """
    import os

    if os.getenv("LANGGRAPH_INTERRUPT", "").lower() == "true":
        from langgraph.types import interrupt

        value = interrupt({
            "proposed_action": state.get("proposed_action"),
            "risk_level": state.get("risk_level"),
        })
        if isinstance(value, dict):
            decision = ApprovalDecision(**value)
        else:
            decision = ApprovalDecision(approved=bool(value))
    else:
        decision = ApprovalDecision(approved=True, comment="mock approval for lab")
    return {
        "approval": decision.model_dump(),
        "events": [make_event("approval", "completed", f"approved={decision.approved}")],
    }


def retry_or_fallback_node(state: AgentState) -> dict:
    """Record a retry attempt or fallback decision.

    TODO(student): implement bounded retry, exponential backoff metadata, and fallback route.
    """
    attempt = int(state.get("attempt", 0)) + 1
    errors = [f"transient failure attempt={attempt}"]
    return {
        "attempt": attempt,
        "errors": errors,
        "events": [make_event("retry", "completed", "retry attempt recorded", attempt=attempt)],
    }


def answer_node(state: AgentState) -> dict:
    """Produce a final response grounded in tool results or classification."""
    tool_results = state.get("tool_results", [])
    if tool_results:
        latest = tool_results[-1]
        if "SUCCESS" in latest:
            answer = f"I have processed your request. {latest}"
        else:
            answer = f"There was an issue processing your request: {latest}"
    else:
        answer = "Your request has been processed successfully."

    return {
        "final_answer": answer,
        "events": [make_event("answer", "completed", "answer generated")],
    }


def evaluate_node(state: AgentState) -> dict:
    """Evaluate tool results — the 'done?' check that enables retry loops.

    TODO(student): replace heuristic with LLM-as-judge or structured validation.
    """
    tool_results = state.get("tool_results", [])
    latest = tool_results[-1] if tool_results else ""
    if "ERROR" in latest:
        return {
            "evaluation_result": "needs_retry",
            "events": [make_event("evaluate", "completed", "tool result indicates failure, retry needed")],
        }
    return {
        "evaluation_result": "success",
        "events": [make_event("evaluate", "completed", "tool result satisfactory")],
    }


def dead_letter_node(state: AgentState) -> dict:
    """Log unresolvable failures for manual review.

    Third layer of error strategy: retry -> fallback -> dead letter.
    TODO(student): persist to dead-letter queue, alert on-call, or create support ticket.
    """
    return {
        "final_answer": "Request could not be completed after maximum retry attempts. Logged for manual review.",
        "events": [make_event("dead_letter", "completed", f"max retries exceeded, attempt={state.get('attempt', 0)}")],
    }


def finalize_node(state: AgentState) -> dict:
    """Finalize the run and emit a final audit event."""
    return {"events": [make_event("finalize", "completed", "workflow finished")]}
