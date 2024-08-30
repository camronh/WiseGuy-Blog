---
date: 2024-08-30
title: Should You Even Trust Gemini’s Million-Token Context Window?
description: Discover how Gemini 1.5 Flash aced our million-token App Store data challenge. Learn about its 100% accuracy and the future of large-scale AI analysis.
keywords:
  - Long Context LLMs
  - AI Applications
  - Natural Language Processing
  - Machine Learning
categories:
  - LLMs
  - Evals
  - Gemini
  - OpenAI
  - LangChain
---

# Should You Even Trust Gemini’s Million-Token Context Window?

![Haystack Made with GPT-4o](../../img/haystack.png)

[📖 Read On Medium](https://medium.com/@camronhaider/should-geminis-million-token-context-be-trusted-30be97c5109d)

Imagine you’re tasked with analyzing your company’s entire database — millions of customer interactions, years of financial data, and countless product reviews — to extract meaningful insights. You turn to AI for help. You shove all of the data into Google Gemini 1.5, with its new 1 million token context length and start making requests, which it seems to be solving. But a nagging question persists: Can you trust the AI to accurately process and understand all of this information? How confident can you be in its analysis when it’s dealing with such a vast amount of data? Are you going to have to dig through a million tokens worth of data to validate each answer?

Traditional AI tests, like the well-known [“needle-in-a-haystack” tests](https://arize.com/blog-course/the-needle-in-a-haystack-test-evaluating-the-performance-of-llm-rag-systems/), fall short in truly assessing an AI’s ability to reason across large, cohesive bodies of information. These tests often involve hiding unrelated information (needles) in an otherwise homogeneous context (haystack). The problem is that it makes the focus on information retrieval and anomaly detection rather than comprehensive understanding and synthesis. Our goal wasn’t just to see if it could find a needle in a haystack, but to evaluate if it could understand the entire haystack itself.

Using a [real-world dataset of App Store information](https://www.kaggle.com/datasets/ramamet4/app-store-apple-data-set-10k-apps), we systematically tested [Gemini 1.5 Flash](https://deepmind.google/technologies/gemini/flash/) across increasing context lengths. We asked it to compare app prices, recall specific privacy policy details, and evaluate app ratings — tasks that required both information retrieval and reasoning capabilities. For our evaluation platform, we used [LangSmith](https://www.langchain.com/langsmith) by [LangChain](https://www.langchain.com/), which proved to be an invaluable tool in this experiment.

The results were nothing short of amazing! Lets dive in.

## Setting Up the Experiment

You can follow along with our full experiment in this [Jupyter notebook](https://github.com/camronh/WiseGuy-Blog/blob/main/docs/experiments/Context_Length_AppStoreV2.ipynb).

### Choosing Our Datasets

We need 3 datasets for our experiment:

1.  [**App Data Dataset**:](https://www.kaggle.com/datasets/ramamet4/app-store-apple-data-set-10k-apps) We used the Apple App Store Data Set, a real-world collection of information about 10,000 apps. This dataset provided rich, varied information for us to analyze.
2.  **Golden Dataset:** We selected 5 apps arbitrarily that we will use to craft our Evaluation Dataset questions and ground truth answers. These 5 apps will need to be included in the context in every step of the experiment.
3.  [**Evaluation Dataset**:](https://smith.langchain.com/public/0f86f6ab-aaf0-4262-b38d-bed96e243a15/d?tab=2&paginationState=%7B%22pageIndex%22%3A0%2C%22pageSize%22%3A10%7D) We crafted a set of three questions and answers based on the Golden Dataset. These are the questions we will ask Gemini Flash and we will evaluate it’s answer against the ground truth answer we have written.

```python
examples = [
    {
        "question": "Do the 'Sago Mini Superhero' and 'Disney Channel  Watch Full Episodes Movies  TV' apps require internet connection?",
        "answer": "You can play Sago Mini Superhero without wi-fi or internet. Internet is required for Disney Channel  Watch Full Episodes Movies  TV"
    },
    {
        "question": "Where can I find the privacy policy for the 'Disney Channel  Watch Full Episodes Movies  TV' app?",
        "answer": "http://disneyprivacycenter.com/"
    },
    {
        "question": "Which one costs less? The 'KQ MiniSynth' app or the 'Sago Mini Superhero' app?",
        "answer": "The 'KQ MiniSynth' app costs $5.99, the 'Sago Mini Superhero' app costs $2.99. So 'Sago Mini Superhero' is cheaper"
    }
]
```

## Leveraging [Gemini 1.5 Flash](https://deepmind.google/technologies/gemini/flash/)

For our AI model, we utilized Google’s Gemini 1.5 Flash. This model allows up to 1 million tokens in it’s context window, which is roughly 700,000 words! At the time of writing this, [Gemini 1.5 Flash costs](https://ai.google.dev/pricing) ~$0.70/million input tokens, and thats without caching. That is comparable to GPT-3.5 or Claude Haiku pricing.

### [LangSmith](https://www.langchain.com/langsmith): Our Evaluation Platform

For managing our experiment and evaluating results, we turned to [LangSmith](https://www.langchain.com/langsmith) by [LangChain](https://www.langchain.com/). LangSmith offers gives us access to a few features that are perfect for this kind of experiment:

1.  When we upload our evaluation dataset to LangSmith, we can version control, split, and even generate synthetic data, all from the LangSmith console.
2.  All of our experimentation results and traces are tracked in LangSmith for every dataset. The dashboard allows us to visualize the performance across different context lengths.

When running our experiment, it is not required but it is quite convenient to use automatic evaluations using an LLM as a judge. In our case that means for each question in our dataset:

1.  Gemini Flash takes a whack at answering the question
2.  We have GPT-4o score if Flash’s answer is correct based on the ground truth answer we have written in the dataset.

This functionality happens through [LangSmith Custom Evaluators](https://docs.smith.langchain.com/how_to_guides/evaluation/evaluate_llm_application#use-custom-evaluators), which are simple python functions that return a score for the evaluation:

```python
# We define the scoring schema for the LLM to respond in
# using Pydantic
class EvaluationSchema(BaseModel):
    """An evaluation schema for assessing the correctness of an answer"""
    reasoning: str = Field(
        description="Detailed reasoning for the evaluation score")
    correct: bool = Field(
        description="Whether the user's answer is correct or not")

# Our evaluation function
def qa_eval(root_run: Run, example: Example):
    """Evaluate the correctness of an answer to a given question"""
    # The question from the dataset example
    question = example.inputs["question"]

    # Gemini's answer
    flash_answer = root_run.outputs["output"]

    # Ground truth answer from the dataset
    correct_answer = example.outputs["answer"]

    # Force GPT-4o to respond in the scoring schema
    llm = ChatOpenAI(model="gpt-4o", temperature=0.4).with_structured_output(EvaluationSchema)

    system_prompt = f"""You are a judge tasked with evaluating a user's answer to a given question.
You will be provided with the question, the correct answer, and the user's thought process and answer.

Question:
{question}

Correct Answer:
{correct_answer}

Your job is to assess the user's answer and provide:
1. Detailed reasoning for your evaluation, comparing the user's answer to the correct answer
2. A boolean judgment on whether the user's answer is correct or not

Be thorough in your reasoning and accurate in your judgment. Consider partial correctness and any nuances in the answers."""

    # Invoke the model with all of the context
    evaluation: EvaluationSchema = llm.invoke(
        [SystemMessage(content=system_prompt),
         HumanMessage(content=flash_answer)]
    )

    score = 1 if evaluation.correct else 0

    return {
        "score": score,
        "key": "correctness",
        "comment": evaluation.reasoning
    }
```

If you’re not familiar with [LangChain](https://www.langchain.com/) or Python, we are simply writing a function (`qa_eval`) that takes the question from the dataset, Flash’s answer, and the correct answer and putting them all into a prompt for GPT-4o. We use `.with_structured_output` to ensure that the LLM responds in a specific schema that we can use to return the score in the schema that [LangSmith](https://www.langchain.com/langsmith) expects.

## Running the Experiment

We gradually increased the context length up to the full million-token capacity in 50,000 token increments. To generate these varying context lengths, we wrote a function `get_context` that would:

1.  Start with our “golden dataset” of 5 apps
2.  Add additional app data until we reached the desired token count
3.  Randomize the order of apps in the context to avoid any positional bias

### Target Function

We use this `get_context` function in our “[target function](https://docs.smith.langchain.com/how_to_guides/evaluation/evaluate_llm_application#step-1-define-your-target-task)”. The target function describes the function that will be used to produce the output that needs to be evaluated. In our case the target function:

1.  Fills up the context window with app data up to the number of tokens we are testing in that step
2.  Puts the context into a prompt for Gemini Flash
3.  Queries Gemini Flash with the question from the dataset and returns the model’s response

Here’s a simplified version of our target function:

```python
def predict(inputs: dict):
    tokens = (max_context_limit / total_steps) * current_step
    context = get_context(tokens)

    system_prompt = f"""You are tasked with answering user questions based on the App Store data inside <APP STORE DATA>.
    Use ONLY the information provided in the context. Be as accurate as possible."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=inputs["question"])
    ])

    return {"output": response.content}
```

We wrap all of this up into a custom Python class just to make it easy to keep track of the steps and control each experiment and we are ready to run!

```python
result = evaluate(
    self.predict, # Our predict function
    data=client.list_examples(dataset_name=dataset_name), # Our evaluation dataset
    evaluators=[qa_eval], # Our custom evaluator
    experiment_prefix=f"{self.model}-{tokens}" # Prefixes the experiments in Langsmith for readability
)
```

## Results

The results of our experiment with Gemini 1.5 Flash were nothing short of amazing! Across all context lengths, from 50,000 tokens all the way up to the full million-token capacity, Gemini 1.5 Flash achieved 100% accuracy in answering our test questions!

Experiment Results in LangSmith

You can view the full test results on LangSmith [here](https://smith.langchain.com/public/0f86f6ab-aaf0-4262-b38d-bed96e243a15/d?paginationState=%7B%22pageIndex%22%3A0%2C%22pageSize%22%3A10%7D).

Let’s break down what this means:

1.  **🔬 Perfect Accuracy**: Regardless of whether we gave Gemini 1.5 Flash 50,000 tokens of context or 1,000,000 tokens, it consistently provided correct answers to our questions. This level of consistency is impressive and suggests that the model can effectively process and utilize information from extremely large contexts.
2.  **🧠 Information Synthesis**: Our questions required more than just information retrieval. They involved comparing data points from different parts of the context. Gemini 1.5 Flash’s perfect score indicates a strong ability to understand information across a huge context, not just locate specific strings.

To put this in perspective, at the maximum context length, Gemini 1.5 Flash was accurately answering questions while processing the equivalent of a 400-page book in a single query. This is a significant leap beyond traditional document analysis capabilities.

However, it’s important to note some limitations of our experiment:

1.  **Question Complexity**: Our questions, while requiring synthesis, are relatively straightforward. We deliberately avoided questions requiring complex numerical reasoning or identifying trends across the entire dataset.
2.  **Limited Question Set**: We used a small set of questions for each evaluation. A larger, more diverse set of questions could provide even more robust insights into the model’s capabilities.

Despite these limitations, the results are extremely promising. They suggest that Gemini 1.5 Flash can maintain high accuracy and information synthesis capabilities with very low costs, even when dealing with massive amounts of context. This opens up exciting possibilities for applications in various fields, from business analytics to scientific research.
