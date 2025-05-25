#!/usr/bin/env python3
"""
MCP SSE Server with Addition Tool
A simple MCP server that provides a tool to add two numbers.
"""

import argparse
import os
from mcp.server.fastmcp import FastMCP

# Parse arguments first
parser = argparse.ArgumentParser(description="Addition MCP Server")
parser.add_argument("--port", type=int, default=8002, help="Port to run the server on")
args = parser.parse_args()

# Create an MCP server instance with port configuration
mcp = FastMCP("Addition Server", port=args.port)


# Define the addition tool
@mcp.tool()
def add(a: float, b: float) -> float:
    """
    Add two numbers together.
    
    Args:
        a: The first number
        b: The second number
        
    Returns:
        The sum of a and b
    """
    return a + b


# Optional: Add a resource that shows the last calculation
last_calculation = {"a": 0, "b": 0, "result": 0}


@mcp.resource("calculation://last")
def get_last_calculation() -> str:
    """Get the last calculation performed"""
    return f"Last calculation: {last_calculation['a']} + {last_calculation['b']} = {last_calculation['result']}"


# Enhanced addition tool that tracks calculations
@mcp.tool()
def add_with_history(a: float, b: float) -> dict:
    """
    Add two numbers and keep track of the calculation.
    
    Args:
        a: The first number
        b: The second number
        
    Returns:
        A dictionary containing the inputs and result
    """
    result = a + b
    
    # Update the last calculation
    last_calculation["a"] = a
    last_calculation["b"] = b
    last_calculation["result"] = result
    
    return {
        "a": a,
        "b": b,
        "result": result,
        "message": f"The sum of {a} and {b} is {result}"
    }


# Optional: Add a prompt for addition
@mcp.prompt()
def addition_prompt(a: float, b: float) -> str:
    """Create a prompt for addition calculation"""
    return f"Please calculate the sum of {a} and {b}, and explain the calculation step by step."


# Run the server
if __name__ == "__main__":
    # Run with SSE transport
    mcp.run(transport="sse")