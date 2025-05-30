#!/usr/bin/env python3
"""
FastMCP Tool Execution Strategies

This module implements different tool execution strategies based on the DecisionResult
from the decision engine. It handles single tool calls, parallel execution,
sequential chains with result passing, and hybrid approaches.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import core session management
from core.session import FastMCPSession

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionResult:
    """Result of a single tool execution"""

    tool_name: str
    step: int
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    result_variable: Optional[str] = None


@dataclass
class ExecutionPlanResult:
    """Complete result of executing an execution plan"""

    success: bool
    strategy: str
    total_steps: int
    tool_results: List[ToolExecutionResult]
    final_result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    execution_log: List[str] = None

    def __post_init__(self):
        if self.execution_log is None:
            self.execution_log = []


class ToolCallExecutor:
    """
    Tool execution engine that implements different execution strategies
    """

    def __init__(self, session: FastMCPSession):
        """
        Initialize with an active FastMCP session

        Args:
            session: Active FastMCPSession for tool calls
        """
        self.session = session
        self.logger = logging.getLogger(__name__)

    async def execute_single_tool(
        self, tool_call: Dict[str, Any]
    ) -> ToolExecutionResult:
        """
        Execute a single tool call

        Args:
            tool_call: Tool call specification with tool_name, parameters, etc.

        Returns:
            ToolExecutionResult with execution details
        """
        start_time = asyncio.get_event_loop().time()

        try:
            tool_name = tool_call["tool_name"]
            parameters = tool_call["parameters"]
            step = tool_call.get("step", 1)
            result_variable = tool_call.get("result_variable")

            self.logger.info(f"🔧 Executing tool: {tool_name} (step {step})")

            # Call the tool via session
            result = await self.session.call_tool(tool_name, parameters)

            # Extract result text if it's a complex object
            if hasattr(result, "__iter__") and not isinstance(result, str):
                if len(result) > 0 and hasattr(result[0], "text"):
                    final_result = result[0].text
                else:
                    final_result = str(result)
            else:
                final_result = result

            execution_time = asyncio.get_event_loop().time() - start_time

            self.logger.info(f"✅ Tool {tool_name} completed in {execution_time:.2f}s")

            return ToolExecutionResult(
                tool_name=tool_name,
                step=step,
                success=True,
                result=final_result,
                execution_time=execution_time,
                result_variable=result_variable,
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Tool {tool_call.get('tool_name', 'unknown')} failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")

            return ToolExecutionResult(
                tool_name=tool_call.get("tool_name", "unknown"),
                step=tool_call.get("step", 1),
                success=False,
                error=error_msg,
                execution_time=execution_time,
                result_variable=tool_call.get("result_variable"),
            )

    async def execute_parallel_tools(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecutionResult]:
        """
        Execute multiple tools in parallel

        Args:
            tool_calls: List of tool call specifications

        Returns:
            List of ToolExecutionResult objects
        """
        self.logger.info(f"🚀 Executing {len(tool_calls)} tools in parallel")

        # Create tasks for parallel execution
        tasks = [self.execute_single_tool(tc) for tc in tool_calls]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Convert exception to error result
                final_results.append(
                    ToolExecutionResult(
                        tool_name=tool_calls[i].get("tool_name", "unknown"),
                        step=tool_calls[i].get("step", i + 1),
                        success=False,
                        error=str(result),
                        result_variable=tool_calls[i].get("result_variable"),
                    )
                )
            else:
                final_results.append(result)

        return final_results

    def _extract_result_variables(
        self, parameters: Dict[str, Any], previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Replace result variables in parameters with actual values from previous results

        Args:
            parameters: Parameters that may contain result variables like ${{variable_name}}
            previous_results: Dictionary of variable_name -> result_value

        Returns:
            Parameters with variables substituted
        """
        if not previous_results:
            return parameters

        # Convert parameters to string for replacement
        param_str = str(parameters)

        # Replace each variable
        for var_name, var_value in previous_results.items():
            # Look for patterns like ${{var_name}}
            pattern = f"${{{{{var_name}}}}}"
            if pattern in param_str:
                self.logger.info(f"🔄 Substituting {pattern} with {var_value}")
                param_str = param_str.replace(pattern, str(var_value))

        # Try to reconstruct the parameters (simple case)
        try:
            # This is a simplified approach - in reality you'd need more sophisticated parsing
            import ast

            return ast.literal_eval(param_str)
        except Exception:
            # Fallback: try manual JSON-like reconstruction
            # For now, return original parameters if substitution fails
            self.logger.warning(f"Could not substitute variables in {parameters}")
            return parameters

    async def execute_sequential_tools(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecutionResult]:
        """
        Execute tools sequentially, passing results between them

        Args:
            tool_calls: List of tool call specifications in execution order

        Returns:
            List of ToolExecutionResult objects
        """
        self.logger.info(f"🔗 Executing {len(tool_calls)} tools sequentially")

        results = []
        result_variables = {}  # Store results by variable name

        for i, tool_call in enumerate(tool_calls):
            step_num = i + 1
            self.logger.info(f"📍 Sequential step {step_num}/{len(tool_calls)}")

            # Check if this tool depends on previous results
            dependency = tool_call.get("dependency", "none")
            if dependency != "none" and result_variables:
                # Substitute variables in parameters
                original_params = tool_call["parameters"]
                substituted_params = self._extract_result_variables(
                    original_params, result_variables
                )
                tool_call["parameters"] = substituted_params

                if substituted_params != original_params:
                    self.logger.info(
                        f"🔄 Parameters after substitution: {substituted_params}"
                    )

            # Execute the tool
            result = await self.execute_single_tool(tool_call)
            results.append(result)

            # Store result variable if specified
            if result.success and result.result_variable:
                result_variables[result.result_variable] = result.result
                self.logger.info(
                    f"💾 Stored result variable: {result.result_variable} = {result.result}"
                )

            # If tool failed, stop sequential execution
            if not result.success:
                self.logger.error(
                    f"❌ Sequential execution stopped at step {step_num} due to failure"
                )
                break

        return results

    async def execute_hybrid_tools(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecutionResult]:
        """
        Execute tools using hybrid strategy (mix of parallel and sequential)

        This analyzes dependencies and groups tools for optimal execution:
        - Independent tools run in parallel
        - Dependent tools run sequentially

        Args:
            tool_calls: List of tool call specifications

        Returns:
            List of ToolExecutionResult objects
        """
        self.logger.info(f"🎯 Executing {len(tool_calls)} tools using hybrid strategy")

        # Group tools by dependency
        independent_groups = []
        current_group = []

        for tool_call in tool_calls:
            dependency = tool_call.get("dependency", "none")

            if dependency == "none":
                # Independent tool - can run in parallel with others
                current_group.append(tool_call)
            else:
                # Dependent tool - finish current parallel group first
                if current_group:
                    independent_groups.append(("parallel", current_group))
                    current_group = []

                # Add dependent tool as sequential
                independent_groups.append(("sequential", [tool_call]))

        # Add any remaining independent tools
        if current_group:
            independent_groups.append(("parallel", current_group))

        # Execute groups in order
        all_results = []
        result_variables = {}

        for group_type, group_tools in independent_groups:
            self.logger.info(
                f"📦 Executing group of {len(group_tools)} tools ({group_type})"
            )

            if group_type == "parallel":
                group_results = await self.execute_parallel_tools(group_tools)
            else:  # sequential
                # For sequential within hybrid, we need to pass existing variables
                for tool in group_tools:
                    if tool.get("dependency", "none") != "none":
                        original_params = tool["parameters"]
                        substituted_params = self._extract_result_variables(
                            original_params, result_variables
                        )
                        tool["parameters"] = substituted_params

                group_results = await self.execute_sequential_tools(group_tools)

            # Store result variables from this group
            for result in group_results:
                if result.success and result.result_variable:
                    result_variables[result.result_variable] = result.result

            all_results.extend(group_results)

        return all_results

    async def execute_strategy(
        self, strategy: str, tool_calls: List[Dict[str, Any]]
    ) -> ExecutionPlanResult:
        """
        Execute tools based on the specified strategy

        Args:
            strategy: Execution strategy ('single_tool', 'parallel_tools', 'sequential_tools', 'hybrid_tools')
            tool_calls: List of tool call specifications

        Returns:
            ExecutionPlanResult with complete execution details
        """
        start_time = asyncio.get_event_loop().time()
        execution_log = []

        try:
            self.logger.info(f"🎯 Starting execution with strategy: {strategy}")
            execution_log.append(
                f"Starting {strategy} execution with {len(tool_calls)} tools"
            )

            # Normalize strategy name (handle enum format)
            strategy_clean = strategy.lower().replace("executionstrategy.", "")

            # Execute based on strategy
            if strategy_clean == "single_tool":
                if len(tool_calls) != 1:
                    raise ValueError(
                        f"Single tool strategy expects 1 tool, got {len(tool_calls)}"
                    )
                tool_results = [await self.execute_single_tool(tool_calls[0])]

            elif strategy_clean == "parallel_tools":
                tool_results = await self.execute_parallel_tools(tool_calls)

            elif strategy_clean == "sequential_tools":
                tool_results = await self.execute_sequential_tools(tool_calls)

            elif strategy_clean == "hybrid_tools":
                tool_results = await self.execute_hybrid_tools(tool_calls)

            else:
                raise ValueError(f"Unknown execution strategy: {strategy}")

            # Determine overall success
            success = all(result.success for result in tool_results)

            # Generate final result summary
            if success:
                successful_results = [
                    r.result for r in tool_results if r.result is not None
                ]
                if len(successful_results) == 1:
                    final_result = successful_results[0]
                else:
                    final_result = {
                        f"step_{r.step}_{r.tool_name}": r.result
                        for r in tool_results
                        if r.success
                    }
                execution_log.append("Execution completed successfully")
            else:
                final_result = None
                failed_tools = [r.tool_name for r in tool_results if not r.success]
                execution_log.append(f"Execution failed for tools: {failed_tools}")

            execution_time = asyncio.get_event_loop().time() - start_time

            return ExecutionPlanResult(
                success=success,
                strategy=strategy,
                total_steps=len(tool_calls),
                tool_results=tool_results,
                final_result=final_result,
                execution_time=execution_time,
                execution_log=execution_log,
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Strategy execution failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            execution_log.append(error_msg)

            return ExecutionPlanResult(
                success=False,
                strategy=strategy,
                total_steps=len(tool_calls),
                tool_results=[],
                error=error_msg,
                execution_time=execution_time,
                execution_log=execution_log,
            )


async def create_tool_executor(session: FastMCPSession) -> ToolCallExecutor:
    """
    Factory function to create a tool executor

    Args:
        session: Active FastMCPSession

    Returns:
        ToolCallExecutor instance
    """
    return ToolCallExecutor(session)
