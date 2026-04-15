import net_bootstrap  # noqa: F401 (must run before SSL/network imports)

import httpx

class MCPRegistry:
    def __init__(self, agents):
        self.agents = agents
        self.tools = {}

    async def discover_tools(self):
        """
        Dynamically fetch tools from all agents
        """
        async with httpx.AsyncClient(trust_env=False) as client:
            for agent_name, url in self.agents.items():
                try:
                    response = await client.get(f"{url}/mcp/tools")
                    data = response.json()

                    for tool in data["tools"]:
                        self.tools[tool["name"]] = {
                            "agent": agent_name,
                            "url": f"{url}/tools/{tool['name']}",
                            "description": tool["description"],
                            "input_schema": tool["input_schema"]
                        }

                except Exception as e:
                    print(f"[Discovery Failed] {agent_name}: {e}")

    def list_tools(self):
        return self.tools

    async def call_tool(self, client, tool_name, payload=None):
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}

        tool = self.tools[tool_name]

        try:
            response = await client.post(
                tool["url"],
                json=payload or {}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}