#!/usr/bin/env python3
"""
Dependency-Aware Arbitrator - DAG Construction and Analysis
============================================================

This module implements dependency analysis for tool execution planning.
It builds a Directed Acyclic Graph (DAG) from tool calls and creates
optimal execution stages using topological sorting.

Author: Claude Code
Version: 1.0.0
Date: 2025-10-03
"""

from typing import List, Dict, Set, Optional, Any
from collections import defaultdict
import re
import logging

logger = logging.getLogger(__name__)


class DependencyGraph:
    """
    Directed Acyclic Graph for tool execution dependencies.

    Nodes represent tools, edges represent dependencies.
    Edge A → B means "B depends on A" (B must execute after A).
    """

    def __init__(self):
        """Initialize empty dependency graph."""
        self.nodes: Set[str] = set()  # Tool names
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # tool → tools it depends on
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)  # tool → tools that depend on it

    def add_tool(self, tool_name: str):
        """
        Add a tool node to the graph.

        Args:
            tool_name: Name of the tool to add
        """
        self.nodes.add(tool_name)
        logger.debug(f"📊 Added tool to graph: {tool_name}")

    def add_dependency(self, tool: str, depends_on: str):
        """
        Add dependency: tool depends on depends_on.

        Creates edge: depends_on → tool

        Args:
            tool: Tool that has a dependency
            depends_on: Tool that must execute before 'tool'
        """
        self.edges[tool].add(depends_on)
        self.reverse_edges[depends_on].add(tool)
        self.nodes.add(tool)
        self.nodes.add(depends_on)
        logger.debug(f"🔗 Dependency added: {tool} depends on {depends_on}")

    def get_dependencies(self, tool: str) -> Set[str]:
        """
        Get all tools that this tool depends on.

        Args:
            tool: Tool name

        Returns:
            Set of tool names that 'tool' depends on
        """
        return self.edges.get(tool, set())

    def get_dependents(self, tool: str) -> Set[str]:
        """
        Get all tools that depend on this tool.

        Args:
            tool: Tool name

        Returns:
            Set of tool names that depend on 'tool'
        """
        return self.reverse_edges.get(tool, set())

    def has_cycle(self) -> bool:
        """
        Detect cycles in the dependency graph using DFS.

        Returns:
            True if cycle detected, False otherwise
        """
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            """DFS helper for cycle detection."""
            visited.add(node)
            rec_stack.add(node)

            # Visit all dependents (nodes that depend on current node)
            for dependent in self.reverse_edges.get(node, set()):
                if dependent not in visited:
                    if dfs(dependent):
                        return True
                elif dependent in rec_stack:
                    # Back edge found - cycle detected
                    logger.error(f"🔄 CYCLE DETECTED: {node} → {dependent}")
                    return True

            rec_stack.remove(node)
            return False

        # Check all connected components
        for node in self.nodes:
            if node not in visited:
                if dfs(node):
                    return True

        return False

    def get_execution_stages(self) -> List[List[str]]:
        """
        Compute execution stages using Kahn's topological sort algorithm.

        Returns execution stages where each stage is a list of tools that can
        run in parallel (they have no dependencies between them).

        Returns:
            List of stages, where each stage is a list of tool names

        Raises:
            ValueError: If cycle detected or cannot create valid execution order
        """
        # Calculate in-degree (number of dependencies) for each tool
        in_degree = {node: len(self.get_dependencies(node)) for node in self.nodes}

        stages = []

        while in_degree:
            # Find all tools with no remaining dependencies (in-degree = 0)
            ready = [tool for tool, degree in in_degree.items() if degree == 0]

            if not ready:
                # Cycle detected or orphaned nodes
                remaining = list(in_degree.keys())
                logger.error(f"❌ Cannot create execution order - remaining tools: {remaining}")
                raise ValueError(f"Cannot create execution order - possible cycle or orphaned tools: {remaining}")

            stages.append(ready)
            logger.debug(f"📋 Stage {len(stages)}: {ready}")

            # Remove ready tools and update in-degrees
            for tool in ready:
                del in_degree[tool]

                # Decrease in-degree for tools that depend on this one
                for dependent in self.get_dependents(tool):
                    if dependent in in_degree:
                        in_degree[dependent] -= 1

        return stages

    def to_dict(self) -> Dict[str, Any]:
        """
        Export graph to dictionary format for serialization.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "nodes": list(self.nodes),
            "dependencies": {tool: list(deps) for tool, deps in self.edges.items()},
            "dependents": {tool: list(deps) for tool, deps in self.reverse_edges.items()}
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"DependencyGraph(nodes={len(self.nodes)}, edges={sum(len(v) for v in self.edges.values())})"


# =============================================================================
# SYMBOLIC REFERENCE MAPPING
# =============================================================================

# Map symbolic names to tool names
# Some symbols support multiple tool sources (listed in priority order)
SYMBOL_TO_TOOL = {
    'WEBPAGE_CONTENT': ['lookup_website', 'search_web'],  # ✅ FIX: Accept either lookup_website OR search_web
    'SEARCH_RESULTS': 'document_search',
    'FILE_PATH': 'sandboxed_executor',
    'EMAIL_CONTENT': 'email_retriever',
    'STOCK_DATA': 'get_stock_and_company_data',
    'NEWS_DATA': 'get_news_summaries',
    'WIKI_DATA': 'wikipedia_query',
    'FORTUNE_MESSAGE': 'fortune_message',
    'LLM_GENERATED_CONTENT': 'llm_content_generator',  # Special: LLM creative content generation
    'VISUALIZATION_OUTPUT': 'analytical_visualizer',  # Visualization PNG files
    'CHART_IMAGE': 'analytical_visualizer',  # Alternative reference for charts
}


def detect_symbolic_references(param_value: str) -> List[str]:
    """
    Detect {{...}} style symbolic references in parameter values.

    Examples:
        "{{WEBPAGE_CONTENT}}" → ["lookup_website"]
        "{{SEARCH_RESULTS}}" → ["document_search"]
        "Text with {{WEBPAGE_CONTENT}} embedded" → ["lookup_website"]

    Args:
        param_value: Parameter value to analyze

    Returns:
        List of tool names that this parameter depends on
    """
    if not isinstance(param_value, str):
        return []

    pattern = r'\{\{([A-Z_]+)\}\}'
    matches = re.findall(pattern, param_value)

    dependencies = []
    for symbol in matches:
        tool_names = SYMBOL_TO_TOOL.get(symbol)
        if tool_names:
            # ✅ FIX: Handle both single tool name and list of tool names
            if isinstance(tool_names, str):
                tool_names = [tool_names]

            # Add all possible tool sources as dependencies
            for tool_name in tool_names:
                dependencies.append(tool_name)
                logger.debug(f"🔍 Symbolic reference detected: {{{{{{symbol}}}}}} → {tool_name}")
        else:
            logger.warning(f"⚠️ Unknown symbolic reference: {{{{{{symbol}}}}}}")

    return dependencies


# =============================================================================
# SEMANTIC DEPENDENCY RULES
# =============================================================================

def detect_semantic_dependencies(tool_calls: List[dict]) -> Dict[str, List[str]]:
    """
    Apply known semantic dependency rules based on tool types and parameters.

    Semantic rules encode domain knowledge about how tools typically interact.

    Args:
        tool_calls: List of tool call dictionaries from LLM

    Returns:
        Dictionary mapping tool names to their dependencies
    """
    dependencies = {}
    tool_names = [call['function']['name'] for call in tool_calls]

    for call in tool_calls:
        tool_name = call['function']['name']
        params = call['function']['arguments']

        # Parse params if it's a JSON string
        if isinstance(params, str):
            import json
            params = json.loads(params)

        # Rule 1: Email with attachments depends on file creation
        if tool_name == 'secure_email_sender':
            if 'attachments' in params and params['attachments']:
                attachment_file = params['attachments']

                # PRIORITY 1: PNG/image attachments - prefer analytical_visualizer
                if isinstance(attachment_file, str) and attachment_file.endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    if 'analytical_visualizer' in tool_names:
                        dependencies[tool_name] = ['analytical_visualizer']
                        logger.debug(f"📧 Semantic: email with image attachment depends on analytical_visualizer")
                    elif 'sandboxed_executor' in tool_names:
                        dependencies[tool_name] = ['sandboxed_executor']
                        logger.debug(f"📧 Semantic: email with image attachment depends on sandboxed_executor (fallback)")

                # PRIORITY 2: Other attachments - use sandboxed_executor
                elif 'sandboxed_executor' in tool_names:
                    dependencies[tool_name] = ['sandboxed_executor']
                    logger.debug(f"📧 Semantic: email depends on file creation")

        # Rule 2: File creation with HTML content depends on web lookup
        elif tool_name == 'sandboxed_executor':
            action = params.get('action')
            filename = params.get('filename', '')

            if action == 'create_file' and filename.endswith('.html'):
                # If lookup_website is in the tool list, file creation might depend on it
                if 'lookup_website' in tool_names:
                    # Only add if not already detected via symbolic reference
                    if tool_name not in dependencies:
                        dependencies[tool_name] = ['lookup_website']
                        logger.debug(f"📄 Semantic: HTML file creation depends on website lookup")

    return dependencies


# =============================================================================
# MAIN DEPENDENCY ANALYSIS FUNCTION
# =============================================================================

async def analyze_tool_dependencies(
    tool_calls: List[dict],
    tool_registry: Optional[dict] = None
) -> Dict[str, Any]:
    """
    Analyze tool calls to detect dependencies and create execution plan.

    This is the main entry point for dependency analysis. It combines
    multiple detection strategies to build a comprehensive dependency graph.

    Args:
        tool_calls: List of tool call dicts from LLM
        tool_registry: Optional metadata about all available tools

    Returns:
        {
            "graph": DependencyGraph,
            "stages": List[List[str]],  # Execution stages
            "dependencies": Dict[str, List[str]],  # Tool dependencies
            "has_cycle": bool,
            "success": bool
        }
    """
    logger.info(f"🧠 DEPENDENCY ANALYSIS: Analyzing {len(tool_calls)} tool calls")

    graph = DependencyGraph()
    all_dependencies = defaultdict(set)

    # Add all tools to graph first
    for call in tool_calls:
        tool_name = call['function']['name']
        graph.add_tool(tool_name)

    # =========================================================================
    # DETECTION PHASE 1: Symbolic References ({{WEBPAGE_CONTENT}})
    # =========================================================================
    logger.debug("🔍 Phase 1: Detecting symbolic references...")

    for call in tool_calls:
        tool_name = call['function']['name']
        params = call['function']['arguments']

        # Parse params if it's a JSON string
        if isinstance(params, str):
            import json
            params = json.loads(params)

        # Check each parameter value
        for param_name, param_value in params.items():
            if isinstance(param_value, str):
                deps = detect_symbolic_references(param_value)
                for dep in deps:
                    if dep in graph.nodes:
                        graph.add_dependency(tool_name, dep)
                        all_dependencies[tool_name].add(dep)

    # =========================================================================
    # DETECTION PHASE 2: Semantic Rules
    # =========================================================================
    logger.debug("🔍 Phase 2: Applying semantic dependency rules...")

    semantic_deps = detect_semantic_dependencies(tool_calls)
    for tool, deps in semantic_deps.items():
        for dep in deps:
            if dep in graph.nodes:
                graph.add_dependency(tool, dep)
                all_dependencies[tool].add(dep)

    # =========================================================================
    # VALIDATION PHASE: Cycle Detection
    # =========================================================================
    logger.debug("🔍 Validation: Checking for cycles...")

    has_cycle = graph.has_cycle()

    if has_cycle:
        logger.error("❌ CYCLE DETECTED: Cannot create valid execution plan")
        return {
            "success": False,
            "graph": graph,
            "stages": [],
            "dependencies": {k: list(v) for k, v in all_dependencies.items()},
            "has_cycle": True,
            "error": "Circular dependency detected in tool calls"
        }

    # =========================================================================
    # EXECUTION PLANNING: Topological Sort
    # =========================================================================
    logger.debug("📋 Creating execution stages...")

    try:
        stages = graph.get_execution_stages()
    except ValueError as e:
        logger.error(f"❌ Failed to create execution stages: {e}")
        return {
            "success": False,
            "graph": graph,
            "stages": [],
            "dependencies": {k: list(v) for k, v in all_dependencies.items()},
            "has_cycle": False,
            "error": str(e)
        }

    # =========================================================================
    # SUCCESS: Return Execution Plan
    # =========================================================================
    logger.info(f"✅ DEPENDENCY ANALYSIS COMPLETE: {len(stages)} execution stages")

    for i, stage in enumerate(stages, 1):
        parallel_mode = "parallel" if len(stage) > 1 else "sequential"
        logger.info(f"   Stage {i}: {stage} ({parallel_mode})")

    return {
        "success": True,
        "graph": graph,
        "stages": stages,
        "dependencies": {k: list(v) for k, v in all_dependencies.items()},
        "has_cycle": False
    }


# =============================================================================
# DEPENDENCY RESOLUTION (for execution phase)
# =============================================================================

def resolve_dependencies(
    params: dict,
    stage_outputs: Dict[str, Any]
) -> dict:
    """
    Resolve symbolic references in parameters using outputs from previous stages.

    Example:
        params = {"content": "{{WEBPAGE_CONTENT}}"}
        stage_outputs = {"lookup_website": "Article content..."}
        → returns: {"content": "Article content..."}

    Args:
        params: Tool parameters that may contain symbolic references
        stage_outputs: Dictionary mapping tool names to their outputs

    Returns:
        Parameters with symbolic references replaced by actual values
    """
    resolved = params.copy()

    for param_name, param_value in params.items():
        if isinstance(param_value, str):
            # Replace {{SYMBOL}} with actual output
            pattern = r'\{\{([A-Z_]+)\}\}'

            def replacer(match):
                symbol = match.group(1)
                tool_names = SYMBOL_TO_TOOL.get(symbol)

                # ✅ FIX: Handle both single tool name and list of tool names
                if isinstance(tool_names, str):
                    tool_names = [tool_names]
                elif not isinstance(tool_names, list):
                    tool_names = []

                # Try each tool in priority order
                for tool_name in tool_names:
                    if tool_name in stage_outputs:
                        output = stage_outputs[tool_name]
                        logger.info(f"      ✅ Resolved {{{{{{symbol}}}}}} → {tool_name} output ({len(str(output))} chars)")
                        return str(output)

                # None of the tools found
                logger.warning(f"      ⚠️ Cannot resolve {{{{{{symbol}}}}}} - none of {tool_names} in stage_outputs: {list(stage_outputs.keys())}")
                return match.group(0)  # Keep original if cannot resolve

            resolved[param_name] = re.sub(pattern, replacer, param_value)

    return resolved


if __name__ == "__main__":
    # Quick self-test
    import asyncio

    logging.basicConfig(level=logging.DEBUG)

    # Test case: lookup_website → sandboxed_executor → email
    test_calls = [
        {
            "function": {
                "name": "lookup_website",
                "arguments": {"url": "https://example.com"}
            }
        },
        {
            "function": {
                "name": "sandboxed_executor",
                "arguments": {
                    "action": "create_file",
                    "filename": "article.html",
                    "content": "{{WEBPAGE_CONTENT}}"
                }
            }
        },
        {
            "function": {
                "name": "secure_email_sender",
                "arguments": {
                    "to_email": "test@example.com",
                    "attachments": "article.html"
                }
            }
        }
    ]

    async def test():
        result = await analyze_tool_dependencies(test_calls)
        print(f"\n✅ Analysis Result:")
        print(f"   Success: {result['success']}")
        print(f"   Stages: {result['stages']}")
        print(f"   Dependencies: {result['dependencies']}")

    asyncio.run(test())
