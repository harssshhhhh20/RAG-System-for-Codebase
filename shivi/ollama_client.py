"""Minimal Ollama HTTP client (stdlib only).

Used for routing and intent classification, where we need control over
thinking, structured output and timing metadata. The same function is
used by the CLI and by the evaluation harness, so measured behaviour is
the behaviour users get.
"""
import json
import os
import time
import urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
if not OLLAMA_URL.startswith("http"):
    OLLAMA_URL = "http://" + OLLAMA_URL


def chat(model, prompt, *, schema=None, think=False, num_predict=None,
         seed=0, temperature=0.0, timeout=600):
    """Send one user message. Returns (content, meta).

    meta holds wall-clock latency plus Ollama's own token counts and
    durations (nanoseconds) so experiments can separate model load time
    from generation time.
    """
    options = {"temperature": temperature, "seed": seed}
    if num_predict is not None:
        options["num_predict"] = num_predict
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": options,
    }
    # think=None leaves the model's default behaviour (what a plain
    # LangChain ChatOllama call gets).
    if think is not None:
        body["think"] = think
    if schema is not None:
        body["format"] = schema

    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.load(response)
    latency = time.perf_counter() - start

    meta = {
        "latency_s": latency,
        "prompt_tokens": data.get("prompt_eval_count"),
        "output_tokens": data.get("eval_count"),
        "load_ns": data.get("load_duration"),
        "total_ns": data.get("total_duration"),
    }
    return data["message"].get("content", ""), meta


def show(model):
    """Return model metadata (digest, quantization) for experiment logs."""
    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/show",
        data=json.dumps({"model": model}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def version():
    with urllib.request.urlopen(f"{OLLAMA_URL}/api/version", timeout=10) as response:
        return json.load(response).get("version")
