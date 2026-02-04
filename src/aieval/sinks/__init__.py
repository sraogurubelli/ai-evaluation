"""Sinks for outputting evaluation results."""

from aieval.sinks.base import Sink
from aieval.sinks.stdout import StdoutSink
from aieval.sinks.csv import CSVSink
from aieval.sinks.json import JSONSink
from aieval.sinks.langfuse import LangfuseSink

__all__ = ["Sink", "StdoutSink", "CSVSink", "JSONSink", "LangfuseSink"]
