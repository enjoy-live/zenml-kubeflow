import pandas as pd
from typing import Tuple, Dict, Any
from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

from zenml import pipeline, step
from zenml.config import DockerSettings
from zenml.logger import get_logger

logger = get_logger(__name__)

# kubeflow-token-stack-100

# 1. 定义镜像的 Docker 设置：告诉 ZenML 容器里需要安装这些包
docker_settings = DockerSettings(
    requirements="requirements.txt", # 告诉容器需要依赖哪些包, 尽量手动配置越少越好，否则镜像构建过程会很长。
    # 强制不使用 uv，改用常规 pip 参数
    # install_options=["--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple", "--default-timeout=120"],
    environment={
        "UV_INDEX_URL": "https://pypi.tuna.tsinghua.edu.cn/simple",
        # 如果依然下载慢，可以适当放宽超时限制
        "UV_HTTP_TIMEOUT": "120"
    }
    # requirements=["pandas", "scikit-learn"]  # 告诉容器需要依赖哪些包
)

@step
def load_data() -> Tuple[pd.DataFrame, pd.Series]:
    """1. 加载数据集 (以 Iris/示例数据为例)"""
    logger.info("Loading raw dataset...")
    # 替换为你的真实读取逻辑，比如：pd.read_csv(...) 或从数据库读取
    df = pd.DataFrame({
        "feature1": [1.0, 2.0, 5.0, 6.0],
        "feature2": [0.5, 1.5, 4.5, 5.5],
        "label": [0, 0, 1, 1]
    })
    X = df[["feature1", "feature2"]]
    y = df["label"]
    return X, y


@step
def preprocess(X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
    """2. 数据预处理与特征工程"""
    logger.info("Preprocessing data...")
    # 比如：缺失值填充、标准化、特征衍生等
    X_processed = X.fillna(0)
    return X_processed, y


@step
def train_model(X: pd.DataFrame, y: pd.Series) -> BaseEstimator:
    """3. 训练模型并直接返回模型对象 (ZenML 会自动存储模型 Artifact)"""
    logger.info("Training Scikit-Learn Model...")
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    return model


@step
def evaluate_model(model: BaseEstimator, X: pd.DataFrame, y: pd.Series) -> float:
    """4. 评估模型性能"""
    logger.info("Evaluating model...")
    predictions = model.predict(X)
    acc = float(accuracy_score(y, predictions))
    logger.info(f"Model Accuracy: {acc:.4f}")
    return acc


@pipeline(settings={"docker": docker_settings})
def poc_training_pipeline():
    X, y = load_data()
    X_processed, y = preprocess(X, y)
    model = train_model(X_processed, y)
    acc = evaluate_model(model, X_processed, y)


if __name__ == "__main__":
    logger.info("Executing updated ZenML training pipeline...")
    poc_training_pipeline()