from dataclasses import dataclass

@dataclass
class AgentRegistry:
    commodity_classifier = None

registry = AgentRegistry()