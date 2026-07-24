from zenml import pipeline, step
from zenml.logger import get_logger
# from zenml.integrations.kubeflow.flavors.kubeflow_orchestrator_flavor import (
#     KubeflowOrchestratorSettings,
# )

# kubeflow-token-stack

# 以下代码中的配置，都通过命令行注册
# zenml orchestrator register kubeflow_token_orchestrator \
#     --flavor=kubeflow \
#     --kubeflow_hostname=http://172.16.1.72:30080/pipeline \
#     --client_args='{
#         "host": "http://172.16.1.72:30080/pipeline",
#         "namespace": "kubeflow-user-example-com",
#         "existing_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImQteE5fSS1Rb1d6TzhRYlo5QWZlbnVSbm5mM3ZfUGx3eU1uN0Q3ZHI5c00ifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlZmxvdy11c2VyLWV4YW1wbGUtY29tIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtZWRpdG9yLXRva2VuIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImRlZmF1bHQtZWRpdG9yIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiMmJhM2ZjMTEtNTk0ZC00MTQzLThlMmQtOTA3ZDE4NzExYjU2Iiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50Omt1YmVmbG93LXVzZXItZXhhbXBsZS1jb206ZGVmYXVsdC1lZGl0b3IifQ.NlExtE0ddrIlc4LIaV0i-VQGWJHctwfp2zibDpNdemFsihb3rpQCOiMW1vzIBTkntlFc5AF5zuQ_tYCsT3vqHiz7HRegxdHXW5D65pFoDY7t-7Nimp6kSqFkVIhNXweNcHETGpnUx8KuVjktSTU3cRmI3Krd_nvH1FGl3xRuh0VA76cWafm1pQNfotcjWFX31ujUVhSXyx1V0J-PZVfO0ZQaqz-4h-T6z1PkN9T4fwVEd7QXrDREJFR4NcqR-eP9ov-aoaSaSQOuiAkNAv1C7S3UC5zaAYEGoHrlAejj-_jdlsMmiILMQyCzPWwxXfX4ihdvqp_p51Fci7GsFgQ7mw"
#     }' \
#     --kubeflow_namespace=kubeflow-user-example-com
# --------------------------------------------------------------------------
# KFP_HOST = "http://172.16.1.72:30080"  # 入口网关（内网），不要加 /pipeline
# KFP_HOSTNAME = f"{KFP_HOST}/pipeline"  # orchestrator 应使用的 KFP API 地址
# USER_NAMESPACE = "kubeflow-user-example-com"
# # api-key的方式
# kubeflow_settings = KubeflowOrchestratorSettings(
#     client_args = {
#         "host": KFP_HOSTNAME,
#         "namespace": USER_NAMESPACE,
#         "existing_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImQteE5fSS1Rb1d6TzhRYlo5QWZlbnVSbm5mM3ZfUGx3eU1uN0Q3ZHI5c00ifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlZmxvdy11c2VyLWV4YW1wbGUtY29tIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtZWRpdG9yLXRva2VuIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImRlZmF1bHQtZWRpdG9yIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiMmJhM2ZjMTEtNTk0ZC00MTQzLThlMmQtOTA3ZDE4NzExYjU2Iiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50Omt1YmVmbG93LXVzZXItZXhhbXBsZS1jb206ZGVmYXVsdC1lZGl0b3IifQ.NlExtE0ddrIlc4LIaV0i-VQGWJHctwfp2zibDpNdemFsihb3rpQCOiMW1vzIBTkntlFc5AF5zuQ_tYCsT3vqHiz7HRegxdHXW5D65pFoDY7t-7Nimp6kSqFkVIhNXweNcHETGpnUx8KuVjktSTU3cRmI3Krd_nvH1FGl3xRuh0VA76cWafm1pQNfotcjWFX31ujUVhSXyx1V0J-PZVfO0ZQaqz-4h-T6z1PkN9T4fwVEd7QXrDREJFR4NcqR-eP9ov-aoaSaSQOuiAkNAv1C7S3UC5zaAYEGoHrlAejj-_jdlsMmiILMQyCzPWwxXfX4ihdvqp_p51Fci7GsFgQ7mw"
#     },
#     user_namespace=USER_NAMESPACE
# )

logger = get_logger(__name__)

@step(enable_cache=False)
def say_hi() -> str:
    logger.info("Executing say_hi step")
    return "Hello World!"


@pipeline(
    enable_cache=False,
    # settings={"orchestrator": kubeflow_settings}
)
def hi_pipeline():
    say_hi()

if __name__ == "__main__":
    run = hi_pipeline()
    out = run.steps["say_hi"].outputs["output"][0].load()
    logger.info(f"▶︎ Step returned: {out}")