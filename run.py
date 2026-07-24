from zenml import pipeline, step
from zenml.logger import get_logger
import requests
from zenml.client import Client
from zenml.integrations.kubeflow.flavors.kubeflow_orchestrator_flavor import (
    KubeflowOrchestratorSettings,
)

NAMESPACE = "kubeflow-user-example-com"  # This is the user namespace for the profile you want to use
USERNAME = "user@example.com"  # This is the username for the profile you want to use
PASSWORD = "12341234"  # This is the password for the profile you want to use

# Use client_username and client_password and ZenML will automatically fetch a session cookie
kubeflow_settings = KubeflowOrchestratorSettings(
    client_username=USERNAME,
    client_password=PASSWORD,
    user_namespace=NAMESPACE
)


logger = get_logger(__name__)


@step(enable_cache=False)
def say_hi() -> str:
    logger.info("Executing say_hi step")
    return "Hello World!"


# You can also pass the cookie in `client_args` directly
# kubeflow_settings = KubeflowOrchestratorSettings(
#     client_args={"cookies": session_cookie}, user_namespace=NAMESPACE
# )

@pipeline(
    enable_cache=False,
    settings={
        "orchestrator": kubeflow_settings
    }
)
def hi_pipeline():
    say_hi()


if __name__ == "__main__":
    run = hi_pipeline()
    out = run.steps["say_hi"].outputs["output"][0].load()
    logger.info(f"▶︎ Step returned: {out}")