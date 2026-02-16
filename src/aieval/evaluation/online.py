"""Online evaluation agent for evaluating production traces."""

from typing import Any
import structlog

from aieval.agents.base import BaseEvaluationAgent
from aieval.core.types import EvalResult, Score, DatasetItem
from aieval.core.eval import Eval
from aieval.scorers.base import Scorer
from aieval.adapters.base import Adapter

logger = structlog.get_logger(__name__)


class OnlineEvaluationAgent(BaseEvaluationAgent):
    """
    Agent for evaluating production traces.
    
    Supports evaluating traces from Langfuse, OpenTelemetry, and other tracing systems.
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize online evaluation agent.
        
        Args:
            config: Agent configuration
        """
        super().__init__(config)
        self.trace_sources: dict[str, Any] = {}
        self._initialize_trace_sources()
    
    def _initialize_trace_sources(self) -> None:
        """Initialize trace source connections."""
        # Langfuse support
        try:
            from langfuse import Langfuse
            langfuse_api_key = self.config.get("langfuse_api_key")
            langfuse_host = self.config.get("langfuse_host", "https://cloud.langfuse.com")
            if langfuse_api_key:
                self.trace_sources["langfuse"] = Langfuse(
                    api_key=langfuse_api_key,
                    host=langfuse_host,
                )
                logger.info("Langfuse trace source initialized")
        except ImportError:
            logger.debug("Langfuse not available")
        except Exception as e:
            logger.warning("Failed to initialize Langfuse", error=str(e))
    
    async def evaluate_trace(
        self,
        trace_id: str,
        trace_source: str = "langfuse",
        scorers: list[Scorer] | None = None,
        **kwargs: Any,
    ) -> EvalResult:
        """
        Evaluate a single trace.
        
        Args:
            trace_id: Trace ID from tracing system
            trace_source: Trace source ("langfuse", "otel", etc.)
            scorers: List of scorers to apply
            **kwargs: Additional parameters
            
        Returns:
            Run with evaluation results
        """
        if scorers is None:
            raise ValueError("scorers must be provided")
        
        # Fetch trace
        trace = await self._fetch_trace(trace_id, trace_source)
        if trace is None:
            raise ValueError(f"Trace {trace_id} not found in {trace_source}")
        
        # Extract input/output from trace
        trace_input, trace_output = self._extract_trace_data(trace, trace_source)
        
        # Create dataset item
        dataset_item = DatasetItem(
            id=trace_id,
            input=trace_input,
            output=trace_output,
            expected=None,  # No expected output for online evaluation
            metadata={
                "trace_id": trace_id,
                "trace_source": trace_source,
                **trace.get("metadata", {}),
            },
        )
        
        # Create eval
        eval_ = Eval(
            name=f"online_eval_{trace_source}",
            dataset=[dataset_item],
            scorers=scorers,
        )
        
        # Run evaluation (no adapter needed - output already exists)
        # Create a dummy adapter that returns the existing output
        class DummyAdapter(Adapter):
            async def generate(self, input_data: dict[str, Any], model: str | None = None, **kwargs: Any) -> Any:
                return dataset_item.output
        
        adapter = DummyAdapter()
        run = await eval_.run(adapter=adapter, **kwargs)
        
        return run
    
    async def _fetch_trace(self, trace_id: str, trace_source: str) -> dict[str, Any] | None:
        """Fetch trace from tracing system."""
        if trace_source == "langfuse":
            return await self._fetch_langfuse_trace(trace_id)
        elif trace_source == "otel":
            return await self._fetch_otel_trace(trace_id)
        else:
            raise ValueError(f"Unknown trace source: {trace_source}")
    
    async def _fetch_langfuse_trace(self, trace_id: str) -> dict[str, Any] | None:
        """Fetch trace from Langfuse."""
        if "langfuse" not in self.trace_sources:
            raise ValueError("Langfuse not configured")
        
        langfuse = self.trace_sources["langfuse"]
        try:
            # Use Langfuse API to fetch trace
            # Note: This is a simplified version - actual implementation would use Langfuse SDK
            trace = langfuse.fetch_trace(trace_id)
            return {
                "trace_id": trace_id,
                "input": trace.input if hasattr(trace, "input") else {},
                "output": trace.output if hasattr(trace, "output") else None,
                "metadata": trace.metadata if hasattr(trace, "metadata") else {},
            }
        except Exception as e:
            logger.error("Failed to fetch Langfuse trace", trace_id=trace_id, error=str(e))
            return None
    
    async def _fetch_otel_trace(self, trace_id: str) -> dict[str, Any] | None:
        """Fetch trace from OpenTelemetry."""
        # Placeholder for OTel implementation
        raise NotImplementedError("OpenTelemetry trace fetching not yet implemented")
    
    def _extract_trace_data(self, trace: dict[str, Any], trace_source: str) -> tuple[dict[str, Any], Any]:
        """Extract input and output from trace."""
        if trace_source == "langfuse":
            return trace.get("input", {}), trace.get("output")
        else:
            return trace.get("input", {}), trace.get("output")
    
    async def run(self, query: str, **kwargs: Any) -> Any:
        """
        Run agent with query (implements BaseEvaluationAgent interface).
        
        Args:
            query: Operation ("evaluate_trace", etc.)
            **kwargs: Operation-specific parameters
            
        Returns:
            Operation result
        """
        if query == "evaluate_trace":
            return await self.evaluate_trace(**kwargs)
        else:
            raise ValueError(f"Unknown query: {query}")
