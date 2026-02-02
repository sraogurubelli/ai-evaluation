"""SSE Streaming adapter that collects events, tools, and metrics.

This adapter captures all SSE events from streaming APIs and returns enriched
output containing the final YAML plus collected metrics, tool calls, and events.
"""

import json
import logging
import time
import uuid as uuid_module
from typing import Any, Callable

import aiohttp

from ai_evolution.adapters.base import Adapter

logger = logging.getLogger(__name__)


class SSEStreamingAdapter(Adapter):
    """
    SSE Streaming adapter that collects events and metrics.
    
    This adapter streams SSE events from an API and collects:
    - All events with timestamps
    - Tool calls and parameters
    - Performance metrics (latency, tokens)
    
    Returns enriched JSON containing:
    {
        "final_yaml": "...",
        "events": [{"event": "...", "data": {...}, "timestamp": 0.123}],
        "tools_called": [{"tool": "...", "parameters": {...}, "timestamp": 0.5}],
        "metrics": {
            "latency_ms": 1234,
            "total_events": 10,
            "total_tokens": 500,
            "prompt_tokens": 100,
            "completion_tokens": 400
        }
    }
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        headers: dict[str, str] | None = None,
        context_data: dict[str, Any] | None = None,
        endpoint: str = "/chat/stream",
        completion_events: list[str] | None = None,
        tool_call_events: list[str] | None = None,
        usage_event: str = "usage",
        payload_builder: Callable[[dict[str, Any], str | None], dict[str, Any]] | None = None,
        payload_template: dict[str, Any] | None = None,
        include_uuids: bool = False,
    ):
        """
        Initialize SSE streaming adapter.
        
        Args:
            base_url: Base URL for the API server
            headers: Custom headers dict (Authorization, X-API-Key, etc.)
            context_data: Context data (account_id, org_id, etc.)
            endpoint: SSE streaming endpoint path
            completion_events: Event names that indicate completion with final output
            tool_call_events: Event names that indicate tool calls
            usage_event: Event name that contains token usage information
            payload_builder: Optional custom function to build payload.
                Signature: (input_data, model) -> payload_dict
            payload_template: Optional template with static/dynamic fields.
                Special values: "__uuid__", "__timestamp__", "__input__.<field>", "__model__"
            include_uuids: If True, adds conversation_id and interaction_id (HTTPAdapter style)
        """
        self.base_url = base_url.rstrip("/")
        self.context_data = context_data or {}
        self.endpoint = endpoint
        self.completion_events = completion_events or [
            "complete",
            "dashboard_complete",
            "kg_complete",
            "done",
        ]
        self.tool_call_events = tool_call_events or [
            "tool_call",
            "function_call",
            "tool_execution",
        ]
        self.usage_event = usage_event
        self.payload_builder = payload_builder
        self.payload_template = payload_template or {}
        self.include_uuids = include_uuids
        
        # Build headers with defaults
        self.headers = {
            "Content-Type": "application/json",
        }
        
        # Merge custom headers (overrides defaults)
        if headers:
            self.headers.update(headers)
    
    def _apply_template(
        self,
        template: dict[str, Any],
        input_data: dict[str, Any],
        model: str | None,
    ) -> dict[str, Any]:
        """Apply template with special value substitution."""
        payload = {}
        
        for key, value in template.items():
            if isinstance(value, str):
                # Handle special template values
                if value == "__uuid__":
                    payload[key] = str(uuid_module.uuid4())
                elif value == "__timestamp__":
                    payload[key] = int(time.time() * 1000)
                elif value.startswith("__input__."):
                    # Extract from input_data: "__input__.prompt"
                    field = value.replace("__input__.", "")
                    payload[key] = input_data.get(field, "")
                elif value == "__model__":
                    payload[key] = model
                else:
                    payload[key] = value
            elif isinstance(value, dict):
                # Recursively apply template to nested dicts
                payload[key] = self._apply_template(value, input_data, model)
            elif isinstance(value, list):
                # Process lists (may contain dicts)
                payload[key] = [
                    self._apply_template(item, input_data, model) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                # Static value
                payload[key] = value
        
        return payload
    
    def _generate_payload(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
    ) -> dict[str, Any]:
        """Generate payload for API request."""
        # Use custom payload builder if provided
        if self.payload_builder:
            return self.payload_builder(input_data, model)
        
        # Build payload using template or defaults
        payload = {}
        
        # Apply template if provided
        if self.payload_template:
            payload = self._apply_template(self.payload_template, input_data, model)
        else:
            # Default payload building (current implementation)
            payload = {
                "prompt": input_data.get("prompt", ""),
                "stream": True,
            }
            
            # Add model if specified
            if model:
                payload["model"] = model
            
            # Copy standard fields from input_data
            for field in ["entity_type", "operation_type", "old_yaml", "schema_context"]:
                if field in input_data:
                    payload[field] = input_data[field]
        
        # Add UUIDs if requested (HTTPAdapter compatibility)
        if self.include_uuids:
            payload["conversation_id"] = str(uuid_module.uuid4())
            payload["interaction_id"] = str(uuid_module.uuid4())
        
        # Add context data if configured
        if self.context_data:
            payload["context"] = self.context_data
        
        return payload
    
    async def generate(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate output by streaming SSE events.
        
        Args:
            input_data: Input data with prompt and other parameters
            model: Model name (optional)
            **kwargs: Additional parameters
            
        Returns:
            JSON string with enriched output containing:
            - final_yaml: The final YAML/output
            - events: List of all events with timestamps
            - tools_called: List of tool calls with parameters
            - metrics: Performance metrics (latency, tokens, etc.)
        """
        logger.info("SSE streaming adapter (ml-infra adapter) invoked")
        # Generate payload
        payload = self._generate_payload(input_data, model)
        logger.debug(f"Generated payload: {json.dumps(payload, indent=2)}")
        
        # Track metrics
        start_time = time.time()
        all_events = []
        tools_called = []
        final_yaml = None
        token_usage = {}
        
        # Make API call
        endpoint_url = f"{self.base_url}{self.endpoint}"
        timeout = aiohttp.ClientTimeout(total=300)
        logger.info(f"Connecting to SSE endpoint: {endpoint_url}")
        logger.debug(f"Headers: {self.headers}")
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    endpoint_url,
                    json=payload,
                    headers=self.headers,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(
                            f"API error {response.status}: {error_text}"
                        )
                    
                    logger.info("SSE events receiving")
                    # Parse SSE stream
                    current_event = None
                    event_count = 0
                    line_count = 0 
                    async for line in response.content:
                        line_count += 1
                        line = line.decode("utf-8").strip()

                        if line_count <= 5:
                            logger.debug(f"Raw line {line_count}: {repr(line)}")
                        if not line:
                            continue
                        
                        if line.startswith("event:"):
                            current_event = line[6:].strip()
                            logger.debug(f"SSE event received: {current_event}")
                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                            
                            # Skip empty data
                            if not data_str:
                                continue
                            
                            try:
                                event_data = json.loads(data_str)
                                event_count += 1
                                if event_count == 1:
                                    logger.info(f"SSE events receiving - first event: {current_event}")
                                elif event_count % 10 == 0:
                                    logger.debug(f"SSE events receiving - {event_count} events received so far")
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse SSE data: {e}")
                                continue
                            
                            # Calculate relative timestamp
                            timestamp = time.time() - start_time
                            
                            # Store all events
                            all_events.append({
                                "event": current_event,
                                "data": event_data,
                                "timestamp": timestamp,
                            })
                            
                            # Extract tool calls
                            if current_event in self.tool_call_events:
                                tool_info = {
                                    "tool": event_data.get("tool_name") or event_data.get("function_name") or event_data.get("tool"),
                                    "parameters": event_data.get("parameters") or event_data.get("arguments") or event_data.get("input", {}),
                                    "timestamp": timestamp,
                                }
                                tools_called.append(tool_info)
                            
                            # Extract final YAML from completion events
                            if current_event in self.completion_events:
                                # Try multiple possible fields for the output
                                final_yaml = (
                                    event_data.get("yaml") or
                                    event_data.get("output") or
                                    event_data.get("result") or
                                    json.dumps(event_data)
                                )
                            
                            # Extract token usage
                            if current_event == self.usage_event or "usage" in event_data:
                                usage = event_data.get("usage", event_data)
                                if isinstance(usage, dict):
                                    # Check if this is a nested structure with model names
                                    for key, value in usage.items():
                                        if isinstance(value, dict) and ("prompt_tokens" in value or "completion_tokens" in value):
                                            # Found nested model usage data
                                            token_usage.update(value)
                                            break
                                    else:
                                        # Flat structure
                                        token_usage.update(usage)
            
            # Calculate final metrics
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            metrics = {
                "latency_ms": latency_ms,
                "total_events": len(all_events),
            }
            
            # Add token usage if available
            if token_usage:
                prompt_tokens = token_usage.get("prompt_tokens", 0)
                completion_tokens = token_usage.get("completion_tokens", 0)
                total_tokens = prompt_tokens + completion_tokens
                metrics.update({
                    "total_tokens": total_tokens,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                })
            
            logger.info(f"SSE streaming completed - received {len(all_events)} events, latency: {latency_ms}ms")
            logger.debug(f"Final YAML length: {len(final_yaml) if final_yaml else 0}")
            logger.debug(f"First 200 chars of final_yaml: {final_yaml[:200] if final_yaml else ''}")
            # Build enriched output
            enriched_output = {
                "final_yaml": final_yaml or "",
                "events": all_events,
                "tools_called": tools_called,
                "metrics": metrics,
            }
            logger.debug(f"Enriched output: {json.dumps(enriched_output, indent=2)}")
            return json.dumps(enriched_output)
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error during SSE streaming: {e}")
            raise RuntimeError(f"Network error: {e}") from e
        except Exception as e:
            logger.error(f"Error during SSE streaming: {e}")
            raise

