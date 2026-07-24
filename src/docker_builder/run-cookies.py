import requests
import html
import re

from zenml import pipeline, step
from zenml.logger import get_logger
from zenml.integrations.kubeflow.flavors.kubeflow_orchestrator_flavor import (
    KubeflowOrchestratorSettings,
)

# kubeflow-stack-v701

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
USERNAME = "user@example.com"
PASSWORD = "12341234"
USER_NAMESPACE = "kubeflow-user-example-com"

logger = get_logger(__name__)

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

session_cookie = get_kubeflow_session_cookie(KFP_HOST, USERNAME, PASSWORD)

kubeflow_settings = KubeflowOrchestratorSettings(
    client_args={"cookies": session_cookie},
    user_namespace=USER_NAMESPACE,
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