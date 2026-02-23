"""
LoRA Training Workflow for ComfyCode

This workflow trains a LoRA adapter from a directory of images and a captions file.
"""
from pathlib import Path
from comfycode.workflows.builder import Workflow


def build_lora_training_workflow(
    images_dir: str,
    captions_file: str,
    base_model: str,
    lora_name: str,
    learning_rate: float = 1e-4,
    batch_size: int = 4,
    epochs: int = 10,
    resolution: int = 1024,
    output_dir: str = "loras/"
) -> Workflow:
    """
    Build a LoRA training workflow from image-caption pairs.
    """
    wf = Workflow()

    # 1. Load images
    img_loader = wf.add_node(
        "LoadImageBatch",
        directory=images_dir
    )

    # 2. Load captions
    cap_loader = wf.add_node(
        "LoadCaptions",
        file=captions_file
    )

    # 3. Preprocess images
    preprocess = wf.add_node(
        "PreprocessImage",
        image=img_loader.output(),
        size=resolution
    )

    # 4. Pair images and captions
    pair = wf.add_node(
        "PairDataset",
        images=preprocess.output(),
        captions=cap_loader.output()
    )

    # 5. Load base model
    ckpt = wf.add_node(
        "CheckpointLoaderSimple",
        ckpt_name=base_model
    )

    # 6. LoRA Trainer
    trainer = wf.add_node(
        "LoRATrainer",
        dataset=pair.output(),
        base_model=ckpt.output(),
        learning_rate=learning_rate,
        batch_size=batch_size,
        epochs=epochs,
        output_path=f"{output_dir}/{lora_name}.safetensors"
    )

    # 7. Save LoRA
    wf.add_node(
        "SaveLoRA",
        lora=trainer.output(),
        path=f"{output_dir}/{lora_name}.safetensors"
    )

    return wf
