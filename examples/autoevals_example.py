"""Example: Using Autoevals-style scorers (Braintrust).

This demonstrates how to use pre-built scorers similar to Braintrust's autoevals library.
"""

import asyncio
from aieval import (
    Experiment,
    DatasetItem,
    HTTPAdapter,
    # Autoevals-style scorers
    FactualityScorer,
    HelpfulnessScorer,
    LevenshteinScorer,
    BLUEScorer,
    EmbeddingSimilarityScorer,
    RAGRelevanceScorer,
)


async def example_factuality_scorer():
    """Using Factuality scorer (LLM-as-judge)."""
    print("=== Example 1: Factuality Scorer ===")
    
    scorer = FactualityScorer(model="gpt-4o-mini")
    
    # Score a response
    score = scorer.score(
        generated="Paris is the capital of France.",
        expected="Paris is the capital of France.",
        metadata={"input": {"prompt": "What is the capital of France?", "context": "France is a country in Europe."}},
    )
    
    print(f"Factuality score: {score.value}")
    print(f"Comment: {score.comment}")


async def example_helpfulness_scorer():
    """Using Helpfulness scorer (LLM-as-judge)."""
    print("\n=== Example 2: Helpfulness Scorer ===")
    
    scorer = HelpfulnessScorer(model="gpt-4o-mini")
    
    score = scorer.score(
        generated="To reset your password, go to Settings > Security > Reset Password.",
        expected="Helpful instructions",
        metadata={"input": {"prompt": "How do I reset my password?"}},
    )
    
    print(f"Helpfulness score: {score.value}")
    print(f"Comment: {score.comment}")


async def example_levenshtein_scorer():
    """Using Levenshtein distance scorer (heuristic)."""
    print("\n=== Example 3: Levenshtein Scorer ===")
    
    scorer = LevenshteinScorer(normalize=True)
    
    score = scorer.score(
        generated="Hello world",
        expected="Hello world!",
        metadata={},
    )
    
    print(f"Levenshtein similarity: {score.value}")
    print(f"Comment: {score.comment}")
    print(f"Distance: {score.metadata.get('distance')}")


async def example_bleu_scorer():
    """Using BLEU scorer (statistical)."""
    print("\n=== Example 4: BLEU Scorer ===")
    
    scorer = BLUEScorer(n=4)
    
    score = scorer.score(
        generated="The cat sat on the mat",
        expected="A cat sat on a mat",
        metadata={},
    )
    
    print(f"BLEU score: {score.value}")
    print(f"Comment: {score.comment}")


async def example_embedding_similarity_scorer():
    """Using Embedding similarity scorer."""
    print("\n=== Example 5: Embedding Similarity Scorer ===")
    
    scorer = EmbeddingSimilarityScorer(model="text-embedding-3-small")
    
    score = scorer.score(
        generated="The weather is nice today",
        expected="It's a beautiful day outside",
        metadata={},
    )
    
    print(f"Embedding similarity: {score.value}")
    print(f"Comment: {score.comment}")


async def example_rag_relevance_scorer():
    """Using RAG relevance scorer."""
    print("\n=== Example 6: RAG Relevance Scorer ===")
    
    scorer = RAGRelevanceScorer(model="gpt-4o-mini")
    
    score = scorer.score(
        generated="Based on the document, the answer is 42.",
        expected="Relevant to context",
        metadata={
            "input": {
                "prompt": "What is the answer?",
                "context": "The document states that the answer to the ultimate question is 42.",
            }
        },
    )
    
    print(f"RAG relevance score: {score.value}")
    print(f"Comment: {score.comment}")


async def example_combined_scorers():
    """Using multiple autoevals-style scorers in an experiment."""
    print("\n=== Example 7: Combined Scorers ===")
    
    # Create dataset
    dataset = [
        DatasetItem(
            id="test-1",
            input={"prompt": "What is 2+2?", "context": "Basic math."},
            expected={"value": "4"},
        ),
    ]
    
    # Create adapter
    adapter = HTTPAdapter(base_url="http://api.com")
    
    # Create experiment with multiple autoevals scorers
    experiment = Experiment(
        name="autoevals_example",
        dataset=dataset,
        scorers=[
            FactualityScorer(),
            HelpfulnessScorer(),
            LevenshteinScorer(),
        ],
    )
    
    # Run experiment
    result = await experiment.run(adapter=adapter, model="gpt-4o")
    
    print(f"Experiment completed: {result.run_id}")
    print(f"Total scores: {len(result.scores)}")
    
    # Group by scorer type
    for score in result.scores:
        print(f"  {score.name}: {score.value}")


async def main():
    """Run all examples."""
    try:
        await example_factuality_scorer()
        await example_helpfulness_scorer()
        await example_levenshtein_scorer()
        await example_bleu_scorer()
        # await example_embedding_similarity_scorer()  # Requires API key
        await example_rag_relevance_scorer()
        # await example_combined_scorers()  # Requires adapter
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
