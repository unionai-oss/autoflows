<div align="center">
<img src="static/logo.png" width="250px"></img>

<h1>Autoflows</h1>

<i>Automated Flyte Workflows using LLMs</i>
</div>

The `autoflows` package allows you to run Flyte workflows that are powered by
LLMs. These workflows use LLMs to determine which task to run in a suite of
user-defined, trusted Flyte tasks.

## Installation

```bash
pip install autoflows
```

## Usage

First we can define some Flyte tasks as usual:

```python
# example.py

from flytekit import task
from autoflows import autoflow


image_spec = ImageSpec(
    "auto-workflows",
    registry="ghcr.io/unionai-oss",
    requirements="requirements.txt",
    python_version="3.10",
)


@task(container_image=image_spec)
def add_numbers(x: float, y: float) -> FlyteFile: ...


@task(container_image=image_spec)
def concat_strings(strings: List[str]) -> FlyteFile: ...


@task(container_image=image_spec)
def train_classifier(data: List[dict], target_column: str) -> FlyteFile:
    ...
```

Then, in the same file, we define a `FlyteRemote` object that we want to use to
run our autoflow.

```python
# example.py

remote = FlyteRemote(
    config=Config(
        platform=PlatformConfig(
            endpoint="<my_endpoitn>",
            client_id="<my_client_id>",
        ),
    ),
    default_project="flytesnacks",
    default_domain="development",
)
```

Finally, we define the `autoflow` function:

```python
# example.py

@autoflow(
    tasks=[add_numbers, concat_strings, train_classifier],
    model="gpt-3.5-turbo-1106",
    remote=remote,
    openai_secret_group="<OPENAI_API_SECRET_GROUP>",
    openai_secret_key="<OPENAI_API_SECRET_KEY>",
    client_secret_group="<CLIENT_SECRET_GROUP>",
    client_secret_key="<CLIENT_SECRET_KEY>",
    container_image=image_spec,
)
async def main(prompt: str, inputs: dict) -> FlyteFile:
    """You are a helpful bot that picks functions based on a prompt and a set of inputs.

    What tool should I use for completing the task '{prompt}' using the following inputs?
    {inputs}
    """

```

## Running on Flyte or Union

Then, you can register the workflow along with all of the tasks:

```bash
pyflyte --config config.yaml register example.py
```

Where `config.yaml` is the Flyte configuration file pointing to your Flyte or
Union cluster.

Finally, you can run the workflow, and let the `autoflow` function decide which
task to run based on the prompt and inputs. For example, to add two numbers, you
would do:

```bash
pyflyte --config config.yaml run example.py main \
    --prompt "Add these two numbers" \
    --inputs '{"x": 1, "y": 2}'
```

To concatenate two strings, you would do:

```bash
pyflyte run \
    test_auto_workflow.py auto_wf \
    --prompt "Combine these two strings together" \
    --inputs '{"strings": ["hello", " ", "world"]}'
```

And to train a classifier based on data:

```bash
pyflyte run \
    test_auto_workflow.py auto_wf \
    --prompt "Train a classifier on this small dataset" \
    --inputs "{\"target_column\": \"y\", \"training_data\": $(cat data.json)}"
```

Where `data.json` contains json objects that looks something like:

```
[
    {"x": 5, "y": 10},
    {"x": 3, "y": 5},
    {"x": 10, "y": 19},
]
```
