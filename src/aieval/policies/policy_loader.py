"""Policy loader for YAML/JSON policy files."""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from aieval.policies.models import Policy, RuleConfig

logger = logging.getLogger(__name__)


class PolicyLoader:
    """Loads policies from YAML or JSON files."""
    
    @staticmethod
    def load_from_file(file_path: str | Path) -> Policy:
        """
        Load policy from YAML or JSON file.
        
        Args:
            file_path: Path to policy file
            
        Returns:
            Policy object
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Policy file not found: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            elif path.suffix == ".json":
                data = json.load(f)
            else:
                # Try YAML first, then JSON
                try:
                    f.seek(0)
                    data = yaml.safe_load(f)
                except Exception:
                    f.seek(0)
                    data = json.load(f)
        
        return PolicyLoader.load_from_dict(data)
    
    @staticmethod
    def load_from_dict(data: dict[str, Any]) -> Policy:
        """
        Load policy from dictionary.
        
        Args:
            data: Policy data dictionary
            
        Returns:
            Policy object
        """
        # Parse rules
        rules = []
        for rule_data in data.get("rules", []):
            rule = RuleConfig(**rule_data)
            rules.append(rule)
        
        return Policy(
            name=data.get("name", "unnamed"),
            version=data.get("version", "v1"),
            description=data.get("description"),
            rules=rules,
        )
    
    @staticmethod
    def load_from_string(content: str, format: str = "yaml") -> Policy:
        """
        Load policy from string content.
        
        Args:
            content: Policy content as string
            format: Format ("yaml" or "json")
            
        Returns:
            Policy object
        """
        if format.lower() == "yaml":
            data = yaml.safe_load(content)
        elif format.lower() == "json":
            data = json.loads(content)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return PolicyLoader.load_from_dict(data)
