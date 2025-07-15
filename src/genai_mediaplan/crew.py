from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class GenaiMediaplan():
    """GenaiMediaplan crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def definition_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['definition_agent'],  # type: ignore[index]
            verbose=True
        )
        
    @agent
    def data_signals_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['data_signals_agent'],  # type: ignore[index]
            verbose=True
        )
        
    @agent
    def persona_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['persona_agent'],  # type: ignore[index]
            verbose=True
        )
        
    @agent
    def insight_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['insight_agent'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def recommendation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['recommendation_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def formatter_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['formatter_agent'], # type: ignore[index]
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def definition_task(self) -> Task:
        return Task(
            config=self.tasks_config['definition_task'], # type: ignore[index]
        )

    @task
    def data_signals_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_signals_task'], # type: ignore[index]
            # output_file='report.md'
        )

    @task
    def persona_task(self) -> Task:
        return Task(
            config=self.tasks_config['persona_task'], # type: ignore[index]
            # output_file='report.md'
        )

    @task
    def insight_task(self) -> Task:
        return Task(
            config=self.tasks_config['insight_task'], # type: ignore[index]
            # output_file='report.md'
        )

    @task
    def recommendation_task(self) -> Task:
        return Task(
            config=self.tasks_config['recommendation_task'], # type: ignore[index]
            # output_file='report.md'
        )

    @task
    def formatting_task(self) -> Task:
        return Task(
            config=self.tasks_config['formatting_task'], # type: ignore[index]
            output_file='final_report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the GenaiMediaplan crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )

