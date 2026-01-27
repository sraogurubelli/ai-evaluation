"""Function-based dataset (Braintrust pattern)."""

from typing import Callable, Any

from ai_evolution.core.types import DatasetItem


class FunctionDataset:
    """
    Dataset that generates items from a function.
    
    This allows dynamic dataset generation, useful for:
    - Generating test cases programmatically
    - Loading from external APIs
    - Filtering/transforming existing datasets
    """
    
    def __init__(self, generator: Callable[[], list[dict[str, Any]]]):
        """
        Initialize function-based dataset.
        
        Args:
            generator: Function that returns a list of dictionaries,
                      each representing a DatasetItem
        """
        self.generator = generator
    
    def load(self) -> list[DatasetItem]:
        """
        Load dataset items by calling the generator function.
        
        Returns:
            List of DatasetItem objects
        """
        data_list = self.generator()
        items = []
        
        for data in data_list:
            if isinstance(data, DatasetItem):
                items.append(data)
            else:
                # Convert dict to DatasetItem
                items.append(DatasetItem(
                    id=data.get("id", ""),
                    input=data.get("input", {}),
                    output=data.get("output"),
                    expected=data.get("expected"),
                    tags=data.get("tags", []),
                    metadata=data.get("metadata", {}),
                ))
        
        return items
