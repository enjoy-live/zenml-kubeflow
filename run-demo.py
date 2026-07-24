from zenml import step, pipeline
from zenml.config import DockerSettings
import logging


logger = logging.getLogger(__name__)
docker_settings = DockerSettings(environment={
                            "ZENML_DISABLE_STEP_LOGS_STORAGE": "true", 
                            "ZENML_LOGGING_VERBOSITY": "INFO", 
                            "ZENML_DISABLE_STEP_NAMES_IN_LOGS": "false"
                                              })

@step
def basic_step() -> str:
    logger.info(
        "training.started",
        extra={"dataset": "mnist", "epochs": 10},
    )
    logger.info("A simple step that returns a greeting message.")
    return "Hello World!"

# Either add it to the decorator
@pipeline(settings={"docker": docker_settings})
def basic_pipeline() -> str:
    logger.info("A simple pipeline with just one step.")
    greeting = basic_step()
    return greeting


if __name__ == "__main__":
    basic_pipeline()

