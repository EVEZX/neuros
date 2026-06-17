#!/usr/bin/env python3
"""EVEZ Colab Training - Headless Runner
Usage: Run on any machine with GPU access (Colab, Kaggle, local)
1. Upload this script + training data
2. python3 evez-colab-headless.py
3. Adapter weights saved to ./evez-adapter/
"""
import json
import os
import sys

def main():
    print("🧬 EVEZ Self-Training Pipeline - Headless Mode")
    
    # Install deps
    os.system("pip install -q transformers datasets peft trl torch accelerate")
    
    import torch
    if not torch.cuda.is_available():
        print("❌ No GPU detected. This needs CUDA.")
        sys.exit(1)
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model
    from trl import SFTTrainer, SFTConfig
    from datasets import Dataset
    
    # Load training data
    data_url = "https://raw.githubusercontent.com/EVEZX/neuros/main/training/evez-alpaca.json"
    try:
        import urllib.request
        urllib.request.urlretrieve(data_url, "evez-alpaca.json")
        with open("evez-alpaca.json") as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data)} instruction pairs")
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        sys.exit(1)
    
    # Format dataset
    formatted = []
    for d in data:
        text = f"### Instruction:\n{d['instruction']}\n### Input:\n{d.get('input','')}\n### Response:\n{d['output']}"
        formatted.append({"text": text})
    dataset = Dataset.from_list(formatted)
    
    # Load model
    model_name = "HuggingFaceTB/SmolLM2-135M"  # Tiny model for free tier
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")
    
    # LoRA config
    lora_config = LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"],
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Train
    training_args = SFTConfig(
        output_dir="./evez-adapter",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        learning_rate=2e-4,
        logging_steps=10,
        save_steps=100,
        max_seq_length=512,
        dataset_text_field="text",
    )
    
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )
    
    print("🚀 Starting training...")
    trainer.train()
    
    # Save adapter
    model.save_pretrained("./evez-adapter")
    tokenizer.save_pretrained("./evez-adapter")
    print("✅ Adapter saved to ./evez-adapter/")
    
    # Optional: push to HF Hub
    if os.environ.get("PUSH_TO_HUB"):
        model.push_to_hub("evez420/EVEZ", token=os.environ.get("HF_TOKEN"))
        tokenizer.push_to_hub("evez420/EVEZ", token=os.environ.get("HF_TOKEN"))
        print("✅ Pushed to HF Hub: evez420/EVEZ")

if __name__ == "__main__":
    main()
