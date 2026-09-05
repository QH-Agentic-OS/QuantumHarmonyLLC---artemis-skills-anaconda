"""<MODULE_NAME> tool module.

One short paragraph describing what this group of tools is for. Read by
humans, not by the agent — the agent reads each individual @tool docstring.
"""

from anaconda_agent_runtime.tools import tool


# =============================================================================
# Tool authoring quick rules (delete this block before shipping):
#
#  1. Function name = tool name. Use lowercase_with_underscores, verb-first.
#  2. Every argument needs a type hint. The agent sees the schema generated
#     from these — fuzzy types = fuzzy tool calls.
#  3. The docstring IS the tool description. Write it for the model:
#       - Lead with the verb in present tense.
#       - Args: what to pass, with format constraints inline.
#       - Returns: what the result is and how to use it.
#  4. One tool = one logical action. Splitting beats combining.
#  5. Destructive tools should have "delete_", "send_", "create_" etc. in
#     the name and warn in the first sentence of the docstring.
# =============================================================================


@tool
def example_read(path: str) -> str:
    """Read a text file from the sandbox filesystem and return its contents.

    Args:
        path: Absolute path inside the agent sandbox. Mounted host directories
              appear under /work/ (e.g. /work/input/notes.txt).

    Returns:
        The full file contents as a UTF-8 string. Raises FileNotFoundError if
        the path does not exist; the agent should handle that by asking the
        user to check the path.
    """
    with open(path, encoding="utf-8") as f:
        return f.read()


@tool
def example_count(items: list[str], filter_prefix: str = "") -> int:
    """Count how many items match an optional prefix filter.

    Args:
        items: List of strings to count.
        filter_prefix: Only count items starting with this prefix. Default
                       empty string means count all items.

    Returns:
        Integer count of matching items. Returns 0 if no items match.
    """
    if not filter_prefix:
        return len(items)
    return sum(1 for item in items if item.startswith(filter_prefix))


# Add more @tool functions below. Keep them small, focused, and well-documented.
