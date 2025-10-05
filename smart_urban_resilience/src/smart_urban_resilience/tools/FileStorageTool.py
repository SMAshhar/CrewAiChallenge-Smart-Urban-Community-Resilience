import os
import json
from datetime import datetime
from crewai.tools import BaseTool

class FileStorageTool(BaseTool):

    """
    ===============================================================================
    📦 FileStorageTool — Persistent File-Based Memory for CrewAI Agents
    ===============================================================================

    Overview:
    ---------
    The `FileStorageTool` enables CrewAI agents to persist and retrieve their
    data, state, and logs locally — without relying on external databases.

    This tool provides a simple, reliable file-based storage mechanism, allowing
    agents in the Smart Urban Community system to store intermediate results,
    share JSON data across agents, and maintain continuity between runs.

    Key Capabilities:
    -----------------
    ✅ Save structured data (as JSON) under the agent’s directory  
    ✅ Load previously saved files for context recovery or further analysis  
    ✅ List all stored files for quick data lookup  
    ✅ Automatically creates directories per agent and timestamps files

    Typical Use Cases:
    ------------------
    - The **Data Collector Agent** saves raw sensor or citizen input data  
    - The **Validator Agent** loads, cleans, and re-saves the corrected dataset  
    - The **Event Detection Agent** reads validated data to detect anomalies  
    - The **Decision Agent** stores response strategies for later review  
    - The **Feedback Agent** logs outcomes and lessons learned  

    Available Actions:
    ------------------
    - `"save"` → Store a JSON object to disk  
    - `"load"` → Retrieve a previously saved JSON file  
    - `"list"` → List all files saved for a particular agent  

    Method Signature:
    -----------------
    _run(action: str, agent_name: str, data: dict = None, filename: str = None)

    Example Usage:
    --------------
    from custom_tool import FileStorageTool

    storage = FileStorageTool()

    # Save example
    storage._run("save", "data_collector", {"temperature": 27, "humidity": 0.6})

    # Load example
    data = storage._run("load", "data_collector", filename="20251004_153000.json")

    # List files
    files = storage._run("list", "data_collector")

    Integration:
    ------------
    In crew.py, attach the tool to any agent like this:

    @agent
    def data_collector(self) -> Agent:
        return Agent(
            config=self.agents_config['data_collector'],
            verbose=True,
            tools=[FileStorageTool()]
        )

    ===============================================================================
    """

    name: str = "file_storage_tool"
    description: str = "Store and retrieve agent data, logs, and state files locally in JSON format."

    def __init__(self, base_path: str = "./data"):
        super().__init__(name="file_storage_tool", description="Store and retrieve agent data, logs, and state files locally in JSON format.")
        # self.base_path: str = "./data"
        os.makedirs("./data", exist_ok=True)

    def _run(self, action: str, agent_name: str, data: dict = {}, filename: str = ""):
        """Perform read/write actions to persistent file storage."""
        agent_dir = os.path.join("./data", agent_name)
        os.makedirs(agent_dir, exist_ok=True)

        if action == "save" and data:
            filename = filename or f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(agent_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return {"status": "saved", "path": filepath}

        elif action == "load" and filename:
            filepath = os.path.join(agent_dir, filename)
            if not os.path.exists(filepath):
                return {"error": f"File {filename} not found"}
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)

        elif action == "list":
            return os.listdir(agent_dir)

        else:
            return {"error": "Invalid action or parameters"}
