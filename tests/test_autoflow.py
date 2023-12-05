"""A toy hackathon project for gpt-powered workflows.
"""

import inspect
import json
import os
from typing import Callable, List, Type

import docstring_parser
import joblib
import openai
import pandas as pd
from sklearn.linear_model import LogisticRegression

from flytekit import current_context, task, Deck, ImageSpec, Secret
from flytekit.configuration import Config, PlatformConfig
from flytekit.remote import FlyteRemote
from flytekit.types.file import FlyteFile
from flytekit.experimental import eager

from auto_workflow import auto


image_spec = ImageSpec(
    "auto-workflows",
    registry="ghcr.io/unionai-oss",
    requirements="requirements.txt",
    python_version="3.10",
)


CLIENT_SECRET_GROUP = "arn:aws:secretsmanager:us-east-2:356633062068:secret:"
CLIENT_SECRET_KEY = "eager-workflow-LhHnqo"
OPENAI_API_SECRET_GROUP = "arn:aws:secretsmanager:us-east-2:356633062068:secret:"
OPENAI_API_SECRET_KEY = "openai_secret_key-1QGSZb"


@task(container_image=image_spec)
def add_numbers(x: float, y: float) -> FlyteFile:
    """Gets the sum of two numbers.
    
    :param x: The first number.
    :param y: The second number.
    """
    print(f"Adding numbers {x} and {y}")
    out = x + y
    output_path = os.path.join(current_context().working_directory, "result.txt")
    with open(output_path, "w") as f:
        f.write(str(out))
    return FlyteFile(output_path)


@task(container_image=image_spec)
def multiply_numbers(x: float, y: float) -> FlyteFile:
    """Gets the product of two numbers.
    
    :param x: The first number.
    :param y: The second number.
    """
    print(f"Multiplying numbers {x} and {y}")
    out = x * y
    output_path = os.path.join(current_context().working_directory, "result.txt")
    with open(output_path, "w") as f:
        f.write(str(out))
    return FlyteFile(output_path)


@task(container_image=image_spec)
def concat_strings(strings: List[str]) -> FlyteFile:
    """Concatenates a list of strings into one.
    
    :param strings: A list of strings to concatenate
    """
    print(f"Concatenating strings {strings}")
    result = "".join(strings)
    output_path = os.path.join(current_context().working_directory, "result.txt")
    with open(output_path, "w") as f:
        f.write(result)
    return FlyteFile(output_path)


@task(container_image=image_spec)
def train_classifier(
    training_data: List[dict],
    target_column: str,
) -> FlyteFile:
    """Trains a classifier on the training data.
    
    :param training_data: A list of dictionaries, where each dictionary is a row of the training data.
    :param target_column: The name of the column to use as the target.
    """
    print(f"Training a classifier on training data: {training_data[:3]}")
    training_data = pd.DataFrame.from_records(training_data)
    features, target = training_data.drop(target_column, axis="columns"), training_data[target_column]
    model = LogisticRegression(max_iter=10_000)
    model.fit(features, target)
    output_path = os.path.join(current_context().working_directory, "result.pkl")
    joblib.dump(model, output_path)
    return FlyteFile(output_path)


remote = FlyteRemote(
    config=Config(
        platform=PlatformConfig(
            endpoint="demo.hosted.unionai.cloud",
            client_id="eager-workflows",
        ),
    ),
    default_project="flytesnacks",
    default_domain="development",
)


@autoflow(
    remote=remote,
    client_secret_group=CLIENT_SECRET_GROUP,
    client_secret_key=CLIENT_SECRET_KEY,
    tasks=[add_numbers, multiply_numbers, concat_strings, train_classifier],
    model="gpt-3.5-turbo-1106",
    openai_secret_group=OPENAI_API_SECRET_GROUP,
    openai_secret_key=OPENAI_API_SECRET_KEY,
    container_image=image_spec,
    local_entrypoint=False,
)
async def auto_wf(prompt: str, inputs: dict) -> FlyteFile:
    """You are a helpful bot that picks functions based on a prompt and a set of inputs.

    What tool should I use for completing the task '{prompt}' using the following inputs?
    {inputs}
    """
