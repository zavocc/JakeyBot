from fastmcp import Client
class ToolManifest:
    tool_human_name = "MCP Search"
    def __init__(self):
        self.tool_schema = []

        # Updated OpenAI schema to match the original tool schema's parameters and types
        self.tool_schema_openai = [
            {"type": "function", "function": _schema} for _schema in self.tool_schema
        ]
    
    async def init_tool(self):
        async with Client("https://remote-mcp-servers.com/api/mcp") as self.client:
            tools = await self.client.list_tools()           

            for _tool in tools:
                self.tool_schema.append({
                    "name": _tool.name,
                    "description": _tool.description,
                    "parameters": _tool.inputSchema["properties"],
                    "required": _tool.inputSchema.get("required", [])
                })

            print(f"Available tools: {self.tool_schema}")
