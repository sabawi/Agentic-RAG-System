# Dependency-Aware Arbitrator Design
**Version:** 1.0
**Author:** Claude Code
**Date:** 2025-10-03
**Status:** Design Phase

---

## Executive Summary

Enhance the Arbitrator System to **proactively analyze tool dependencies** before execution, creating an optimal execution plan (DAG) rather than relying on hardcoded phase separation rules.

**Current Problem:** Tool chaining uses hardcoded rules (`should_run_sequentially`) that only handle email+file dependencies. Cannot detect arbitrary tool chains or symbolic references like `{{WEBPAGE_CONTENT}}`.

**Solution:** Implement dependency-aware arbitrator that analyzes tool call parameters to build a Directed Acyclic Graph (DAG) and execute tools in optimal dependency order.

---

## Architecture Overview

### Current Flow (Reactive)
```
┌─────────────────────────────────────────────────────────────┐
│ 1. Tool-Calling LLM generates:                              │
│    [lookup_website, sandboxed_executor, secure_email_sender]│
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Hardcoded Phase Separation (should_run_sequentially)     │
│    - Phase 1: lookup_website                                │
│    - Phase 2: sandboxed_executor, secure_email_sender       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Execute Phase 1 → Phase 2                                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Arbitrator validates AFTER execution                     │
│    - If failure → regenerate                                │
└─────────────────────────────────────────────────────────────┘
```

### Proposed Flow (Proactive)
```
┌─────────────────────────────────────────────────────────────┐
│ 1. Tool-Calling LLM generates:                              │
│    [lookup_website, sandboxed_executor, secure_email_sender]│
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. ARBITRATOR DEPENDENCY ANALYSIS                           │
│    - Detect: sandboxed_executor.content = {{WEBPAGE_CONTENT}}│
│    - Detect: email.attachments depends on file created      │
│    - Build DAG: lookup_website → sandboxed → email          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Execute in Dependency Order (topological sort)           │
│    - Stage 1: lookup_website                                │
│    - Stage 2: sandboxed_executor (receives website content) │
│    - Stage 3: secure_email_sender (receives file path)      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Arbitrator validates each stage                          │
│    - If failure → regenerate with context                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Dependency Detection Algorithm

### Input Data Structure

```python
# Tool call from LLM (example)
tool_call = {
    "function": {
        "name": "sandboxed_executor",
        "arguments": {
            "action": "create_file",
            "filename": "article.html",
            "content": "{{WEBPAGE_CONTENT}}"  # ← Symbolic reference
        }
    }
}

# Tool metadata (from tool manager)
tool_metadata = {
    "name": "lookup_website",
    "output_fields": ["title", "content", "author", "date"],  # ← Output schema
    "input_parameters": ["url"]
}
```

### Detection Patterns

#### 1. Symbolic Reference Pattern
**Pattern:** `{{TOOL_NAME}}` or `{{TOOL_OUTPUT}}`

```python
def detect_symbolic_references(param_value: str) -> List[str]:
    """
    Detect {{...}} style symbolic references in parameter values.

    Examples:
        "{{WEBPAGE_CONTENT}}" → depends on "lookup_website"
        "{{SEARCH_RESULTS}}" → depends on "document_search"
        "{{FILE_PATH}}" → depends on "sandboxed_executor"
    """
    import re
    pattern = r'\{\{([A-Z_]+)\}\}'
    matches = re.findall(pattern, param_value)

    # Map symbolic names to tool names
    symbol_to_tool = {
        'WEBPAGE_CONTENT': 'lookup_website',
        'SEARCH_RESULTS': 'document_search',
        'FILE_PATH': 'sandboxed_executor',
        'EMAIL_CONTENT': 'email_retriever',
        'STOCK_DATA': 'get_stock_and_company_data'
    }

    return [symbol_to_tool.get(sym) for sym in matches if sym in symbol_to_tool]
```

#### 2. Output Field Reference Pattern
**Pattern:** Parameter value matches another tool's output field

```python
def detect_field_dependencies(tool_calls: List[dict], tool_registry: dict) -> dict:
    """
    Detect when a parameter might reference another tool's output field.

    Example:
        lookup_website outputs: {"title": "...", "content": "..."}
        sandboxed_executor receives: content="<some long text>"
        → Might depend on lookup_website.content
    """
    dependencies = {}

    for i, call in enumerate(tool_calls):
        tool_name = call['function']['name']
        params = call['function']['arguments']

        # Check each parameter
        for param_name, param_value in params.items():
            # Look for tools executed before this one
            for j in range(i):
                prev_tool = tool_calls[j]['function']['name']
                prev_metadata = tool_registry.get(prev_tool, {})
                output_fields = prev_metadata.get('output_fields', [])

                # If this param name matches an output field
                if param_name in output_fields:
                    dependencies.setdefault(tool_name, []).append(prev_tool)
                    break

    return dependencies
```

#### 3. Semantic Dependency Pattern
**Pattern:** Known tool relationships

```python
SEMANTIC_DEPENDENCIES = {
    # Email always depends on file creation if attachments present
    'secure_email_sender': {
        'depends_on': ['sandboxed_executor'],
        'condition': lambda params: 'attachments' in params
    },

    # File creation with web content depends on lookup_website
    'sandboxed_executor': {
        'depends_on': ['lookup_website'],
        'condition': lambda params: (
            params.get('action') == 'create_file' and
            params.get('filename', '').endswith('.html')
        )
    }
}

def detect_semantic_dependencies(tool_calls: List[dict]) -> dict:
    """Apply known semantic dependency rules."""
    dependencies = {}

    for i, call in enumerate(tool_calls):
        tool_name = call['function']['name']
        params = call['function']['arguments']

        if tool_name in SEMANTIC_DEPENDENCIES:
            rule = SEMANTIC_DEPENDENCIES[tool_name]
            if rule['condition'](params):
                dependencies[tool_name] = rule['depends_on']

    return dependencies
```

---

## DAG Construction Algorithm

### Step 1: Build Dependency Graph

```python
from typing import List, Dict, Set
from collections import defaultdict

class DependencyGraph:
    """Directed Acyclic Graph for tool execution dependencies."""

    def __init__(self):
        self.nodes: Set[str] = set()  # Tool names
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # tool → dependencies
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)  # tool → dependents

    def add_tool(self, tool_name: str):
        """Add a tool node to the graph."""
        self.nodes.add(tool_name)

    def add_dependency(self, tool: str, depends_on: str):
        """
        Add dependency: tool depends on depends_on.

        Creates edge: depends_on → tool
        """
        self.edges[tool].add(depends_on)
        self.reverse_edges[depends_on].add(tool)
        self.nodes.add(tool)
        self.nodes.add(depends_on)

    def get_dependencies(self, tool: str) -> Set[str]:
        """Get all tools that this tool depends on."""
        return self.edges.get(tool, set())

    def get_dependents(self, tool: str) -> Set[str]:
        """Get all tools that depend on this tool."""
        return self.reverse_edges.get(tool, set())

    def has_cycle(self) -> bool:
        """Detect cycles using DFS."""
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)

            for dependent in self.reverse_edges.get(node, set()):
                if dependent not in visited:
                    if dfs(dependent):
                        return True
                elif dependent in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in self.nodes:
            if node not in visited:
                if dfs(node):
                    return True

        return False
```

### Step 2: Topological Sort (Kahn's Algorithm)

```python
def topological_sort(graph: DependencyGraph) -> List[List[str]]:
    """
    Return execution stages (tools that can run in parallel at each stage).

    Returns:
        List of stages, where each stage is a list of tools that can run in parallel.

    Example:
        [[lookup_website, document_search],  # Stage 1: Independent tools
         [sandboxed_executor],                # Stage 2: Depends on stage 1
         [secure_email_sender]]               # Stage 3: Depends on stage 2
    """
    # Calculate in-degree (number of dependencies) for each tool
    in_degree = {node: len(graph.get_dependencies(node)) for node in graph.nodes}

    stages = []

    while in_degree:
        # Find all tools with no remaining dependencies (in-degree = 0)
        ready = [tool for tool, degree in in_degree.items() if degree == 0]

        if not ready:
            # Cycle detected or orphaned nodes
            raise ValueError(f"Cannot create execution order - possible cycle or orphaned tools: {list(in_degree.keys())}")

        stages.append(ready)

        # Remove ready tools and update in-degrees
        for tool in ready:
            del in_degree[tool]

            # Decrease in-degree for tools that depend on this one
            for dependent in graph.get_dependents(tool):
                if dependent in in_degree:
                    in_degree[dependent] -= 1

    return stages
```

---

## Complete Dependency Analysis Function

```python
async def analyze_tool_dependencies(
    tool_calls: List[dict],
    tool_registry: dict
) -> Dict[str, any]:
    """
    Analyze tool calls to detect dependencies and create execution plan.

    Args:
        tool_calls: List of tool call dicts from LLM
        tool_registry: Metadata about all available tools

    Returns:
        {
            "graph": DependencyGraph,
            "stages": List[List[str]],  # Execution stages
            "dependencies": Dict[str, List[str]],  # Tool dependencies
            "has_cycle": bool
        }
    """
    graph = DependencyGraph()
    all_dependencies = {}

    # Add all tools to graph
    for call in tool_calls:
        tool_name = call['function']['name']
        graph.add_tool(tool_name)

    # 1. Detect symbolic references ({{WEBPAGE_CONTENT}})
    for call in tool_calls:
        tool_name = call['function']['name']
        params = call['function']['arguments']

        for param_value in params.values():
            if isinstance(param_value, str):
                deps = detect_symbolic_references(param_value)
                for dep in deps:
                    if dep in graph.nodes:
                        graph.add_dependency(tool_name, dep)
                        all_dependencies.setdefault(tool_name, set()).add(dep)

    # 2. Detect output field references
    field_deps = detect_field_dependencies(tool_calls, tool_registry)
    for tool, deps in field_deps.items():
        for dep in deps:
            graph.add_dependency(tool, dep)
            all_dependencies.setdefault(tool, set()).update(deps)

    # 3. Apply semantic dependency rules
    semantic_deps = detect_semantic_dependencies(tool_calls)
    for tool, deps in semantic_deps.items():
        for dep in deps:
            if dep in graph.nodes:
                graph.add_dependency(tool, dep)
                all_dependencies.setdefault(tool, set()).add(dep)

    # 4. Check for cycles
    has_cycle = graph.has_cycle()

    # 5. Create execution stages
    stages = []
    if not has_cycle:
        try:
            stages = topological_sort(graph)
        except ValueError as e:
            logger.error(f"Failed to create execution order: {e}")

    return {
        "graph": graph,
        "stages": stages,
        "dependencies": {k: list(v) for k, v in all_dependencies.items()},
        "has_cycle": has_cycle
    }
```

---

## Integration with Arbitrator

### New Arbitrator Method

```python
async def arbitrator_plan_execution(
    tool_calls: List[dict],
    tool_registry: dict
) -> Dict[str, any]:
    """
    PROACTIVE ARBITRATOR: Analyze dependencies before execution.

    Returns execution plan with stages and data flow mapping.
    """
    logger.info(f"🧠 ARBITRATOR: Analyzing dependencies for {len(tool_calls)} tools")

    # Analyze dependencies
    analysis = await analyze_tool_dependencies(tool_calls, tool_registry)

    if analysis['has_cycle']:
        logger.error("❌ ARBITRATOR: Detected dependency cycle!")
        return {
            "success": False,
            "error": "Circular dependency detected in tool calls",
            "stages": []
        }

    logger.info(f"✅ ARBITRATOR: Execution plan created with {len(analysis['stages'])} stages")

    for i, stage in enumerate(analysis['stages'], 1):
        logger.info(f"   Stage {i}: {stage} ({'parallel' if len(stage) > 1 else 'sequential'})")

    return {
        "success": True,
        "stages": analysis['stages'],
        "dependencies": analysis['dependencies'],
        "graph": analysis['graph']
    }
```

### Modified Execution Flow

```python
async def execute_tools_with_dependencies(tool_calls: List[dict]):
    """
    Execute tools in dependency-aware stages.

    Replaces: execute_tools_with_email_dependency()
    """
    # 1. Get execution plan from arbitrator
    plan = await arbitrator_plan_execution(tool_calls, tool_manager.tool_registry)

    if not plan['success']:
        logger.error(f"Failed to create execution plan: {plan['error']}")
        # Fallback to sequential execution
        return await execute_tools_sequential(tool_calls)

    all_results = []
    stage_outputs = {}  # Store outputs for dependency resolution

    # 2. Execute each stage
    for stage_num, stage_tools in enumerate(plan['stages'], 1):
        logger.info(f"🚀 STAGE {stage_num}: Executing {len(stage_tools)} tool(s)")

        # Get tool calls for this stage
        stage_calls = [tc for tc in tool_calls if tc['function']['name'] in stage_tools]

        # 3. Resolve dependencies for this stage
        for call in stage_calls:
            tool_name = call['function']['name']
            params = call['function']['arguments']

            # Replace symbolic references with actual outputs
            params = resolve_dependencies(params, stage_outputs, plan['dependencies'])
            call['function']['arguments'] = params

        # 4. Execute stage tools (in parallel if multiple)
        if len(stage_calls) > 1:
            logger.info(f"   ⚡ Parallel execution: {[tc['function']['name'] for tc in stage_calls]}")
            tasks = [execute_single_tool(call) for call in stage_calls]
            stage_results = await asyncio.gather(*tasks)
        else:
            logger.info(f"   → Sequential execution: {stage_calls[0]['function']['name']}")
            stage_results = [await execute_single_tool(stage_calls[0])]

        # 5. Store outputs for next stage
        for call, result in zip(stage_calls, stage_results):
            tool_name = call['function']['name']
            stage_outputs[tool_name] = result

        all_results.extend(stage_results)
        logger.info(f"✅ STAGE {stage_num} COMPLETE")

    return all_results

def resolve_dependencies(
    params: dict,
    stage_outputs: dict,
    dependencies: dict
) -> dict:
    """
    Resolve symbolic references and dependency mappings.

    Example:
        params = {"content": "{{WEBPAGE_CONTENT}}"}
        stage_outputs = {"lookup_website": "Article content..."}
        → params = {"content": "Article content..."}
    """
    resolved = params.copy()

    for param_name, param_value in params.items():
        if isinstance(param_value, str):
            # Replace {{SYMBOL}} with actual output
            import re
            pattern = r'\{\{([A-Z_]+)\}\}'

            def replacer(match):
                symbol = match.group(1)
                tool_name = SYMBOL_TO_TOOL.get(symbol)
                if tool_name and tool_name in stage_outputs:
                    return str(stage_outputs[tool_name])
                return match.group(0)

            resolved[param_name] = re.sub(pattern, replacer, param_value)

    return resolved
```

---

## Tool Metadata Schema

Each tool should declare its inputs and outputs for dependency analysis:

```python
# Example: lookup_website metadata
{
    "name": "lookup_website",
    "description": "Fetch web content",
    "input_parameters": {
        "url": {"type": "string", "required": True}
    },
    "output_schema": {
        "title": "string",
        "content": "string",  # ← Can be referenced by {{WEBPAGE_CONTENT}}
        "author": "string",
        "date": "string"
    },
    "output_symbols": ["WEBPAGE_CONTENT"]  # Symbolic names that map to this tool
}
```

---

## Implementation Phases

### Phase 1: Foundation (Current Sprint)
- [x] Design dependency analysis algorithm ← **YOU ARE HERE**
- [ ] Implement DependencyGraph class
- [ ] Implement symbolic reference detection
- [ ] Unit tests for dependency detection

### Phase 2: Core Execution
- [ ] Implement topological sort
- [ ] Implement dependency resolution
- [ ] Update execute_tools_with_dependencies()
- [ ] Integration tests

### Phase 3: Tool Metadata
- [ ] Add output_schema to tool definitions
- [ ] Create tool registry with metadata
- [ ] Update all tools with metadata

### Phase 4: Validation & Optimization
- [ ] Cycle detection and error handling
- [ ] Parallel execution optimization
- [ ] Performance benchmarking
- [ ] Update ARBITRATOR_SYSTEM_ARCHITECTURE.md

---

## Benefits

1. **Truly Agentic**: Arbitrator intelligently orchestrates workflows
2. **Flexible**: Works with ANY tool combination, not just hardcoded pairs
3. **Efficient**: Parallel execution of independent tools
4. **Robust**: Cycle detection prevents infinite loops
5. **Maintainable**: No hardcoded dependency rules
6. **Extensible**: New tools automatically integrated

---

## Example Execution Plan

### Input
```json
[
  {"function": {"name": "lookup_website", "arguments": {"url": "..."}}},
  {"function": {"name": "document_search", "arguments": {"query": "..."}}},
  {"function": {"name": "sandboxed_executor", "arguments": {
    "action": "create_file",
    "filename": "article.html",
    "content": "{{WEBPAGE_CONTENT}}"
  }}},
  {"function": {"name": "secure_email_sender", "arguments": {
    "to_email": "...",
    "attachments": "article.html"
  }}}
]
```

### Dependency Analysis Output
```python
{
  "dependencies": {
    "sandboxed_executor": ["lookup_website"],
    "secure_email_sender": ["sandboxed_executor"]
  },
  "stages": [
    ["lookup_website", "document_search"],  # Stage 1: Parallel
    ["sandboxed_executor"],                  # Stage 2: After lookup_website
    ["secure_email_sender"]                  # Stage 3: After sandboxed_executor
  ]
}
```

### Execution Flow
```
Stage 1: ⚡ Parallel
  ├─ lookup_website(url) → content
  └─ document_search(query) → results

Stage 2: → Sequential
  └─ sandboxed_executor(content=<from lookup_website>) → file_path

Stage 3: → Sequential
  └─ secure_email_sender(attachments=<from sandboxed_executor>) → success
```

---

## POST-PROCESSING Email Workflow

### Email Interception and File Cleanup

The dependency-aware arbitrator integrates with the POST-PROCESSING email workflow to handle file attachments properly:

#### Workflow Pattern

```
Stage 1: Data Collection
  └─ lookup_website → retrieves content

Stage 2: File Creation
  └─ sandboxed_executor → creates file with resolved content

Stage 3: Email Interception (POST-PROCESSING)
  └─ secure_email_sender → INTERCEPTED (deferred for post-processing)

POST-PROCESSING Phase:
  1. Primary LLM processes tool outputs
  2. LLM generates final response content
  3. Deferred email tool executes with LLM content
  4. Email sent with file attachments
  5. 🧹 Auto-cleanup: Files deleted after successful email (if auto_cleanup_attachments: true)
```

#### Implementation Details

**Email Interception** (`fastapi_server_complete.py:7787-7817`):
```python
# Both parallel and sequential execution paths intercept secure_email_sender
if function_name == "secure_email_sender":
    logger.info(f"📧 TOOL DEFERRED: {function_name} - Email intercepted for post-processing")
    result = "Email scheduled for sending after content generation"
    return (function_name, result, start_time, True, function_args.copy())
```

**File Cleanup Behavior**:
- Files created in sandbox are automatically deleted after successful email delivery
- Controlled by `auto_cleanup_attachments` configuration (default: `true`)
- Prevents file accumulation in sandbox workspace
- See `config/llm_config.yaml` and DEVELOPER_GUIDE.md for configuration details

**Dependency Resolution** (`dependency_analyzer.py:440-450`):
- Symbolic references like `{{WEBPAGE_CONTENT}}` are resolved before tool execution
- `resolve_dependencies()` replaces symbolic placeholders with actual tool outputs
- Resolution happens at each stage using outputs from previous stages

---

## Implementation Status

### ✅ Completed (v1.0.2.109-111)

**Phase 1-2: Foundation & Core Execution**
- [x] Design dependency analysis algorithm
- [x] Implement DependencyGraph class (`dependency_analyzer.py`)
- [x] Implement symbolic reference detection
- [x] Implement topological sort (Kahn's algorithm)
- [x] Implement dependency resolution
- [x] Update execute_with_dependency_stages()
- [x] Email interception integration
- [x] POST-PROCESSING workflow support

### 🚧 Phase 3-4: Remaining Work

**Phase 3: Tool Metadata**
- [ ] Add output_schema to tool definitions
- [ ] Create comprehensive tool registry with metadata
- [ ] Update all tools with metadata

**Phase 4: Validation & Optimization**
- [x] Cycle detection and error handling
- [ ] Parallel execution optimization improvements
- [ ] Performance benchmarking
- [ ] Update ARBITRATOR_SYSTEM_ARCHITECTURE.md

---

## Next Steps

1. ~~Review and approve this design~~ ✅ APPROVED & IMPLEMENTED
2. ~~Implement DependencyGraph class~~ ✅ COMPLETE
3. ~~Create unit tests for dependency detection~~ ✅ TESTED
4. ~~Integrate with existing arbitrator system~~ ✅ INTEGRATED
5. **TODO**: Complete tool metadata schema (Phase 3)
6. **TODO**: Performance optimization and benchmarking (Phase 4)

**Status:** Core implementation complete. Email POST-PROCESSING workflow operational.
