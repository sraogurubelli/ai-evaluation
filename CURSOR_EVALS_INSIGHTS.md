# Cursor's Evaluation Framework - Insights

## Overview

Based on public information, Cursor uses **Cursor Bench** - an internal evaluation suite to test and optimize their AI agent.

## Key Components

### 1. **Cursor Bench** (Internal Evaluation Suite)
- Offline evaluation datasets (like "Cursor Context Bench")
- Tests model performance on specific tasks with known correct answers
- Runs across all frequently-used models to compare performance

### 2. **Evaluation Metrics**
- **Success rate** - Task completion percentage
- **Tool-calling ability** - Correctness of tool usage
- **Code retention** - Whether users keep code written by agents
- **User satisfaction** - Feedback on follow-up requests
- **Adoption patterns** - Overall user adoption across different models

### 3. **Evaluation Methods**

#### Offline Evaluations
- Benchmark datasets with known correct answers
- Tests specific capabilities (code generation, comprehension, etc.)
- Runs before deploying models to production

#### Online A/B Testing
- Real-world user experience testing
- Measures actual user outcomes (code retention, satisfaction)
- Tests different models/configurations with real users

### 4. **Agent Harness Customization**

When integrating new models (like OpenAI Codex), Cursor:
1. **Aligns model-specific instructions** with their agent harness
2. **Tunes based on Cursor Bench results**
3. **Customizes tool names/definitions** based on model training
4. **Optimizes prompts** for coding domain (e.g., encouraging tool use over shell commands)

### 5. **Public Resources**

- **GitHub Repository**: `cursor/eval` - Contains evaluation datasets
- **Blog Posts**: 
  - "Improving Cursor's agent for OpenAI Codex models"
  - "Improving agent with semantic search"

## Key Insights for AI Evolution

### What Cursor Does Well

1. **Combines Offline + Online Evaluation**
   - Offline evals catch issues before production
   - A/B testing validates real-world impact

2. **Model-Specific Optimization**
   - Customizes agent harness per model
   - Adapts to model strengths/weaknesses

3. **User-Centric Metrics**
   - Code retention (do users keep the code?)
   - User satisfaction (do users like the results?)
   - Not just technical correctness

4. **Continuous Evaluation**
   - Benchmarks run across all models
   - Regular updates based on results

### Potential Improvements for AI Evolution

1. **Add User Feedback Collection**
   - Code retention tracking
   - User satisfaction scores
   - Follow-up request success

2. **Model-Specific Configuration**
   - Allow adapter customization per model
   - Model-specific prompt templates
   - Tool usage patterns

3. **A/B Testing Support**
   - Compare different models/configurations
   - Track user outcomes
   - Statistical significance testing

4. **Benchmark Datasets**
   - Curated test suites for common tasks
   - Domain-specific benchmarks (like "Cursor Context Bench")
   - Public benchmark datasets

## References

- Cursor Blog: "Improving Cursor's agent for OpenAI Codex models"
- GitHub: `cursor/eval` repository
- Benchmarks: Cursor Context Bench, AdvCUA security benchmark
