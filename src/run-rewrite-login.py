import html
import re

import requests
from zenml import pipeline, step
from zenml.client import Client
from zenml.config import DockerSettings
from zenml.enums import StackComponentType
from zenml.logger import get_logger
from zenml.integrations.kubeflow.flavors.kubeflow_orchestrator_flavor import (
    KubeflowOrchestratorSettings,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# 认证配置（已实测通过）
#   - Profile namespace 与 Dex 用户必须配对：
#       kubeflow-user-example-com  <->  user@example.com
#   - KFP_HOST 必须是 Istio 入口网关地址，且要带 /pipeline 前缀，
#     不能直连 ml-pipeline.kubeflow.svc:8888（那样会缺 userid 头 -> 401）。
#   - 该 host 需与 orchestrator 注册时的 --kubeflow_hostname 保持一致：
#       zenml orchestrator register kubeflow_orch --flavor=kubeflow \
#           --kubeflow_hostname=http://172.16.1.72:30080/pipeline
# ---------------------------------------------------------------------------
KFP_HOST = "http://172.16.1.72:30080"  # 入口网关（内网），不要加 /pipeline
KFP_HOSTNAME = f"{KFP_HOST}/pipeline"  # orchestrator 应使用的 KFP API 地址
NAMESPACE = "kubeflow-user-example-com"
USERNAME = "user@example.com"
PASSWORD = "12341234"


def get_kubeflow_session_cookie(host: str, username: str, password: str) -> str:
    """走一遍 oauth2-proxy + Dex 登录流程，返回可直接用于 KFP 的 Cookie 字符串。

    这套集群前端是 oauth2-proxy（会话 cookie 名为 oauth2_proxy_kubeflow），
    因此这里显式复现浏览器登录流程，避免依赖 ZenML 内置登录对 oauth2-proxy 的兼容性。
    """
    session = requests.Session()
    session.max_redirects = 20

    # 1) 触发 oauth2-proxy 登录，跟随跳转直到落在 Dex 本地登录表单
    resp = session.get(
        f"{host}/oauth2/start", params={"rd": "/pipeline"}, timeout=15
    )
    match = re.search(r'action="([^"]*)"', resp.text)
    if not match:
        raise RuntimeError("未找到 Dex 登录表单，请检查 KFP_HOST 是否正确")
    action = html.unescape(match.group(1))
    if action.startswith("/"):
        action = host + action

    # 2) 提交用户名 / 密码
    resp = session.post(
        action, data={"login": username, "password": password}, timeout=15
    )

    # 3) 若出现授权确认页则自动 approve（部分 Dex 配置需要）
    if "approval" in resp.text.lower():
        m2 = re.search(r'action="([^"]*approval[^"]*)"', resp.text)
        if m2:
            approval = html.unescape(m2.group(1))
            if approval.startswith("/"):
                approval = host + approval
            session.post(approval, data={"approval": "approve"}, timeout=15)

    if not session.cookies:
        raise RuntimeError("登录失败：未获取到任何会话 cookie，请检查用户名/密码")

    cookie_str = "; ".join(f"{c.name}={c.value}" for c in session.cookies)
    logger.info(f"已获取 Kubeflow 会话 cookie: {list(session.cookies.keys())}")
    return cookie_str


def ensure_orchestrator_hostname(desired_hostname: str) -> None:
    """确保当前 stack 里的 kubeflow orchestrator 指向正确的 KFP 入口地址。

    kubeflow_hostname 是 orchestrator 组件级配置（不能通过 pipeline settings 覆盖），
    若指向了 ml-pipeline service 会缺少 userid 头导致 401。这里自动校正，免去手动
    执行 `zenml orchestrator update`。校正失败不阻断运行，仅记录告警。
    """
    try:
        client = Client()
        orchestrators = client.active_stack_model.components.get(
            StackComponentType.ORCHESTRATOR, []
        )
        if not orchestrators:
            logger.warning("当前 stack 无 orchestrator 组件，跳过 hostname 自动校正")
            return
        orch = orchestrators[0]
        if "kubeflow" not in (orch.flavor_name or "").lower():
            logger.warning(
                f"当前 orchestrator flavor 为 {orch.flavor_name}，非 kubeflow，跳过校正"
            )
            return
        current = (orch.configuration or {}).get("kubeflow_hostname")
        if current == desired_hostname:
            logger.info(f"orchestrator hostname 已正确：{current}")
            return
        logger.info(
            f"自动更新 orchestrator hostname：{current} -> {desired_hostname}"
        )
        client.update_stack_component(
            name_id_or_prefix=orch.id,
            component_type=StackComponentType.ORCHESTRATOR,
            configuration={"kubeflow_hostname": desired_hostname},
        )
        logger.info("orchestrator hostname 更新完成")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"自动校正 orchestrator hostname 失败（沿用现有配置）：{exc}")


session_cookie = get_kubeflow_session_cookie(KFP_HOST, USERNAME, PASSWORD)

kubeflow_settings = KubeflowOrchestratorSettings(
    client_args={"cookies": session_cookie},
    user_namespace=NAMESPACE,
)

# 集群无法访问 dockerhub 拉取 zenml 基础镜像（i/o timeout）。
# 直接复用内网 harbor 里已构建好的 orchestrator 镜像并跳过构建。
# 说明：若后续修改了 step 代码，需要重新构建镜像时，应把
# zenmldocker/zenml:0.96.1-py3.10 预先推入 harbor 作为 parent_image，
# 见文件末尾注释。
PARENT_IMAGE = "172.16.1.72:30002/zenml/zenml:hi_pipeline-orchestrator"
docker_settings = DockerSettings(
    parent_image=PARENT_IMAGE,
    skip_build=True,
)


@step(enable_cache=False)
def say_hi() -> str:
    logger.info("Executing say_hi step")
    return "Hello World!"


@pipeline(
    enable_cache=False,
    settings={"orchestrator": kubeflow_settings, "docker": docker_settings},
)
def hi_pipeline():
    say_hi()


if __name__ == "__main__":
    ensure_orchestrator_hostname(KFP_HOSTNAME)
    run = hi_pipeline()
    out = run.steps["say_hi"].outputs["output"][0].load()
    logger.info(f"▶︎ Step returned: {out}")
