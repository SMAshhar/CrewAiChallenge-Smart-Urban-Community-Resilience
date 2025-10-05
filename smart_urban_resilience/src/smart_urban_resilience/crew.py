from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
# from .tools.FileStorageTool import FileStorageTool


# Initialize shared tools
# storage_tool = FileStorageTool()


@CrewBase
class SmartUrbanResilience():
    """SmartUrbanCommunity crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # ============ AGENTS ============

    @agent
    def data_collector(self) -> Agent:
        """Collects live city data from IoT, weather APIs, and citizen reports."""
        return Agent(
            config=self.agents_config['data_collector'],  # type: ignore[index]
            verbose=True,
            # tools=[storage_tool]
        )

    @agent
    def data_normalizer(self) -> Agent:
        """Normalizes and enriches incoming data to maintain schema consistency."""
        return Agent(
            config=self.agents_config['data_normalizer'],  # type: ignore[index]
            verbose=True,
            # tools=[storage_tool]
        )

    @agent
    def data_validator(self) -> Agent:
        """Validates data integrity, accuracy, and format."""
        return Agent(
            config=self.agents_config['data_validator'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def event_detector(self) -> Agent:
        """Detects anomalies or city-level events from validated data."""
        return Agent(
            config=self.agents_config['event_detector'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def impact_assessor(self) -> Agent:
        """Assesses the impact of detected events based on severity and population density."""
        return Agent(
            config=self.agents_config['impact_assessor'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def resource_recommender(self) -> Agent:
        """Recommends optimal resources and response priorities."""
        return Agent(
            config=self.agents_config['resource_recommender'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def logistics_agent(self) -> Agent:
        """Plans optimal routing and scheduling for emergency responses."""
        return Agent(
            config=self.agents_config['logistics_agent'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def communicator(self) -> Agent:
        """Crafts and distributes citizen and department communications."""
        return Agent(
            config=self.agents_config['communicator'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def incident_commander(self) -> Agent:
        """Oversees AI-generated actions for human approval and ethical validation."""
        return Agent(
            config=self.agents_config['incident_commander'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def learning_agent(self) -> Agent:
        """Learns from feedback and retrains the system for continuous improvement."""
        return Agent(
            config=self.agents_config['learning_agent'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def privacy_manager(self) -> Agent:
        """Ensures data privacy, consent management, and anonymization."""
        return Agent(
            config=self.agents_config['privacy_manager'],  # type: ignore[index]
            verbose=True
        )

    # ============ TASKS ============

    @task
    def data_collection_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_collection_task'],  # type: ignore[index]
        )

    @task
    def data_normalization_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_normalization_task'],  # type: ignore[index]
        )

    @task
    def data_validation_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_validation_task'],  # type: ignore[index]
        )

    @task
    def event_detection_task(self) -> Task:
        return Task(
            config=self.tasks_config['event_detection_task'],  # type: ignore[index]
        )

    @task
    def impact_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config['impact_assessment_task'],  # type: ignore[index]
        )

    @task
    def resource_recommendation_task(self) -> Task:
        return Task(
            config=self.tasks_config['resource_recommendation_task'],  # type: ignore[index]
        )

    @task
    def logistics_planning_task(self) -> Task:
        return Task(
            config=self.tasks_config['logistics_planning_task'],  # type: ignore[index]
        )

    @task
    def communication_task(self) -> Task:
        return Task(
            config=self.tasks_config['communication_task'],  # type: ignore[index]
        )

    @task
    def incident_command_task(self) -> Task:
        return Task(
            config=self.tasks_config['incident_command_task'],  # type: ignore[index]
        )

    @task
    def learning_feedback_task(self) -> Task:
        return Task(
            config=self.tasks_config['learning_feedback_task'],  # type: ignore[index]
            output_file='feedback_report.md'
        )

    @task
    def privacy_compliance_task(self) -> Task:
        return Task(
            config=self.tasks_config['privacy_compliance_task'],  # type: ignore[index]
            output_file='privacy_audit.md'
        )

    # ============ CREW ============

    @crew
    def crew(self) -> Crew:
        """Creates the SmartUrbanCommunity crew"""

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True
        )
