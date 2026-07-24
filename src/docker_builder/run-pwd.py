from zenml import pipeline, step
from zenml.logger import get_logger
from zenml.integrations.kubeflow.flavors.kubeflow_orchestrator_flavor import (
    KubeflowOrchestratorSettings,
)

# kubeflow-stack-v601

# ---------------------------------------------------------------------------
# 认证配置（已实测通过）
#   - Profile namespace 与 Dex 用户必须配对：
#       kubeflow-user-example-com  <->  user@example.com
#   - KFP_HOST 必须是 Istio 入口网关地址，且要带 /pipeline 前缀，
#     不能直连 ml-pipeline.kubeflow.svc:8888（那样会缺 userid 头 -> 401）。
# ---------------------------------------------------------------------------

USERNAME = "user@example.com"
PASSWORD = "12341234"
USER_NAMESPACE = "kubeflow-user-example-com"

logger = get_logger(__name__)

# Use client_username and client_password and ZenML will automatically fetch a session cookie
kubeflow_settings = KubeflowOrchestratorSettings(
    client_username=USERNAME,
    client_password=PASSWORD,
    user_namespace=USER_NAMESPACE
)

@step(enable_cache=False)
def say_hi() -> str:
    logger.info("Executing say_hi step")
    return "Hello World!"

@pipeline(
    enable_cache=False,
    settings={"orchestrator": kubeflow_settings}
)
def hi_pipeline():
    say_hi()


if __name__ == "__main__":
    run = hi_pipeline()
    out = run.steps["say_hi"].outputs["output"][0].load()
    logger.info(f"▶︎ Step returned: {out}")