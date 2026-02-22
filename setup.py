from setuptools import setup, find_packages

setup(
    name="comfycode",
    version="0.1.0",
    description="Programmatic AI image generation framework built on ComfyUI and RunPod",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "websocket-client>=1.7.0",
        "Pillow>=10.0.0",
    ],
)
