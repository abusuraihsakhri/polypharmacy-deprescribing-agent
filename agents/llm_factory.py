"""
Deterministic test mock. No local or external LLM integration is implemented.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Polypharmacy Deprescribing Agent"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} mock]: No clinical analysis performed. Synthetic query received: '{prompt[:60]}...'."


class LLMFactory:
    """Creates configured LLM client instances with zero-PHI protection."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Polypharmacy Deprescribing Agent"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError("Only the deterministic mock provider is implemented.")
