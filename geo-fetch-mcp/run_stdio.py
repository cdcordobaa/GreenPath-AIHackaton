from app import mcp


if __name__ == "__main__":
    # FastMCP 1.13+ supports selecting transport via string
    mcp.run("stdio")


