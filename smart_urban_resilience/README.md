# Smart Urban Resilience System

## Project Overview

The Smart Urban Resilience System is an AI-powered platform designed to enhance a city's ability to predict, respond to, and recover from various urban events and crises. Leveraging a multi-agent architecture built with CrewAI, the system continuously collects, normalizes, and validates data from diverse urban sources, including IoT sensors, weather APIs, and citizen reports. It then detects anomalies and events, assesses their impact, recommends optimal resource allocation, and coordinates logistics and communications, all while ensuring data privacy and continuous learning.

## What it Does

This system acts as a digital command center for urban resilience, performing the following key functions:

*   **Data Collection:** Gathers real-time environmental, weather, air quality, and hazard data from various sources.
*   **Data Normalization & Validation:** Cleans, standardizes, enriches, and validates all incoming data to ensure consistency, accuracy, and reliability.
*   **Event Detection:** Identifies and classifies urban events (e.g., power outages, traffic jams, pollution spikes, public safety incidents) using rule-based and machine-learning methods.
*   **Impact Assessment:** Analyzes detected events to evaluate their potential social, environmental, and infrastructural impact, prioritizing response efforts based on severity and affected population.
*   **Resource Recommendation:** Recommends optimal resource deployment strategies, including personnel and equipment, based on event impact and available logistics.
*   **Logistics Planning:** Generates and optimizes routes and schedules for emergency vehicles and public services, considering real-time conditions.
*   **Communication:** Crafts and distributes accurate, timely, and localized updates to citizens, departments, and authorities through multi-channel communication.
*   **Incident Command (Human-in-the-Loop):** Provides human oversight for AI-generated recommendations, allowing for validation or override of decisions in high-impact scenarios.
*   **Continuous Learning:** Analyzes post-action performance, learns from feedback, and retrains AI models to improve predictive accuracy and overall city management.
*   **Privacy Management:** Ensures data privacy, consent management, and anonymization across all data flows, adhering to privacy laws and upholding citizen trust.

## How it Works

The Smart Urban Resilience System is built around a CrewAI framework, orchestrating a team of specialized AI agents to collaboratively manage urban events.

1.  **Agents:** Each agent has a specific role, goal, and backstory, enabling them to perform specialized tasks. Examples include `data_collector`, `data_normalizer`, `event_detector`, `impact_assessor`, and `communicator`.
2.  **Tasks:** Agents are assigned tasks that define their responsibilities and expected outputs. These tasks are chained together in a sequential process to achieve the overall system objective.
3.  **Tools:** Agents utilize a suite of custom tools to interact with external systems and perform complex operations. These tools include:
    *   `DataFetchTool`: Fetches live or simulated environmental data from APIs.
    *   `DataNormalizationTool`: Cleans, standardizes, and enriches raw data.
    *   `ValidationTool`: Validates data integrity and accuracy.
    *   `EventDetectionTool`: Identifies patterns and anomalies corresponding to urban events.
    *   `ImpactAssessmentTool`: Assesses the impact of detected events.
    *   `ResourcePlannerTool`: Recommends optimal resource deployment.
    *   `FileStorageTool`: Manages file operations for data persistence.
    *   `QDrantTool`: Likely for vector database interactions (though not explicitly detailed in the provided code, its presence suggests advanced data handling).
4.  **Workflow:** The system operates in a sequential process:
    *   Data is collected and then normalized and validated.
    *   Validated data is used to detect events.
    *   Detected events are assessed for impact.
    *   Based on impact, resources are recommended and logistics are planned.
    *   Communications are drafted, and human oversight is provided by the `incident_commander`.
    *   Feedback is collected for continuous learning, and privacy compliance is maintained throughout.

## What it Doesn't Do

*   **Real-time Emergency Response (Direct Action):** While it provides recommendations and plans, the system is designed with a "human-in-the-loop" approach. It does not autonomously deploy resources or execute emergency actions without human approval.
*   **Guaranteed Live Data:** The `DataFetchTool` includes simulation fallbacks. While it prioritizes live API data, it will generate realistic synthetic data if external APIs are unavailable, meaning not all data processed is guaranteed to be from live sources at all times.
*   **Comprehensive Global Hazard Detection:** Some hazard data, like flood risk, is currently simulated due to the lack of globally free and reliable APIs. Wildfire risk is based on NASA FIRMS detections, which might have coverage limitations.
*   **Full-fledged UI/Dashboard:** The provided codebase focuses on the backend AI logic and data processing. It does not include a user interface or dashboard for visualization and interaction.
*   **Direct Hardware Control:** The system does not directly control IoT devices or other urban infrastructure. Its role is to analyze data and provide actionable intelligence.

## Installation

To set up and run the Smart Urban Resilience System, follow these steps:

### Prerequisites

*   Python 3.9+
*   `pip` (Python package installer)

### 1. Clone the Repository

First, clone the project repository to your local machine:

```bash
git clone https://github.com/SMAshhar/CrewAiChallenge-Smart-Urban-Community-Resilience.git
cd CrewAiChallenge-Smart-Urban-Community-Resilience
```

### 2. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

*   **On Windows:**
    ```bash
    .venv\Scripts\activate
    ```
*   **On macOS/Linux:**
    ```bash
    source .venv/bin/activate
    ```

### 4. Install Dependencies

Install all required Python libraries using `pip`:

```bash
pip install -r smart_urban_resilience/requirments.txt
```

The `requirments.txt` file specifies the following libraries:
*   `timezonefinder`: For determining timezones from geographical coordinates.
*   `geopy`: For geocoding services (e.g., reverse geocoding to get city names from coordinates).
*   `scikit-learn`: A machine learning library, likely used for event detection or data validation.
*   `qdrant-client`: A client for Qdrant, an open-source vector similarity search engine, indicating advanced data storage and retrieval capabilities.
*   `openai`: For interacting with OpenAI's API, suggesting the use of large language models for agent reasoning.

### 5. Environment Variables

The project may require API keys or other sensitive information. Create a `.env` file in the `smart_urban_resilience` directory (e.g., `smart_urban_resilience/.env`) and add your environment variables.

Example `.env` content (replace with your actual keys):

```
OPENAI_API_KEY="your_openai_api_key_here"
# Add other environment variables as needed by your tools or agents
```

## How to Run

The `main.py` script provides entry points for running, training, replaying, and testing the CrewAI system.

### Running the Crew

To run the Smart Urban Resilience System with predefined inputs (e.g., for a specific city):

```bash
python smart_urban_resilience/src/smart_urban_resilience/main.py run
```

The default `city` input is 'Karachi'. You can modify the `inputs` dictionary in `main.py` to test with different cities or parameters.

### Training the Crew

To train the crew for a specified number of iterations:

```bash
python smart_urban_resilience/src/smart_urban_resilience/main.py train <n_iterations> <filename>
```

Replace `<n_iterations>` with the number of training iterations and `<filename>` with the desired output file for training results.

### Replaying Crew Execution

To replay a previous crew execution from a specific task ID:

```bash
python smart_urban_resilience/src/smart_urban_resilience/main.py replay <task_id>
```

Replace `<task_id>` with the ID of the task you wish to replay.

### Testing the Crew

To test the crew execution:

```bash
python smart_urban_resilience/src/smart_urban_resilience/main.py test <n_iterations> <eval_llm>
```

Replace `<n_iterations>` with the number of test iterations and `<eval_llm>` with the LLM to use for evaluation.

## Project Structure

The project is organized as follows:

```
CrewAiChallenge-Smart-Urban-Community-Resilience/
├── .gitignore
├── architecture.md
├── README.md                 <- This file
└── smart_urban_resilience/
    ├── .env                  <- Environment variables (create this file)
    ├── .gitignore
    ├── pyproject.toml
    ├── README.md             <- (Old README, will be replaced by this one)
    ├── requirments.txt       <- Project dependencies
    ├── test.py
    ├── uv.lock
    ├── data/                 <- Stores output data from tasks
    │   ├── 1-normalized_data.json
    │   ├── ...
    │   └── Urban Sensor Data Collector/
    │       └── karachi_data.json
    ├── knowledge/            <- Stores knowledge base files
    │   └── user_preference.txt
    └── src/
        └── smart_urban_resilience/
            ├── __init__.py
            ├── crew.py       <- Defines agents, tasks, and the CrewAI workflow
            ├── main.py       <- Entry point for running the system
            ├── config/
            │   ├── agents.yaml   <- Agent configurations
            │   └── tasks.yaml    <- Task configurations
            ├── schema/
            │   └── DataNormalizationSchema.py <- Pydantic schemas for data validation
            └── tools/            <- Custom tools used by agents
                ├── __init__.py
                ├── custom_tool.py
                ├── DataFetchTool.py
                ├── DataNormalizationTool.py
                ├── EventDetectionTool.py
                ├── FileStorageTool.py
                ├── ImpactAcessorTool.py
                ├── QDrantToo.py
                ├── ResourcePlannerTool.py
                └── ValidationTool.py
