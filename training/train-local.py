#!/usr/bin/env python3
"""NEUROS Local Training — Runs on CPU, no GPU needed.
Slow but autonomous. ~2 hours for 94 samples.
"""
import json, os

# Install deps
os.system("pip install -q transformers datasets trl peft accelerate 2>/dev/null")

from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer
from datasets import load_dataset

print("Loading base model (GPT-2 small for CPU training)...")
model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token

print("Loading dataset...")
dataset = load_dataset("json", data_files="/home/openclaw/evez-ecosystem/neuros/training/evez-alpaca.json", split="train")

def format_example(example):
    return f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"

def tokenize(example):
    text = format_example(example)
    return tokenizer(text, truncation=True, padding="max_length", max_length=512)

print("Tokenizing dataset...")
tokenized = dataset.map(tokenize, remove_columns=dataset.column_names)

print("Training...")
training_args = TrainingArguments(
    output_dir="/home/openclaw/evez-ecosystem/neuros/training/neuros-cpu-model",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    save_steps=50,
    save_total_limit=2,
    logging_steps=10,
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    processing_class=tokenizer,
)

trainer.train()
model.save_pretrained("/home/openclaw/evez-ecosystem/neuros/training/neuros-cpu-model")
tokenizer.save_pretrained("/home/openclaw/evez-ecosystem/neuros/training/neuros-cpu-model")
print("✅ Local training complete!")
