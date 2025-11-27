from fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Calculator Server")


@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The sum of a and b
    """
    result = a + b
    return result


if __name__ == "__main__":
    # Run the server as a remote MCP server with SSE transport
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
