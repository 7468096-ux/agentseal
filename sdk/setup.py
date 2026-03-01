from setuptools import setup


setup(
    name="agentseal",
    version="0.1.0",
    description="AgentSeal Python SDK",
    py_modules=["agentseal"],
    install_requires=["httpx>=0.27.0"],
    python_requires=">=3.9",
)
