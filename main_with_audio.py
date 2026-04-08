"""Convenience entry point — always renders with audio enabled."""

from src.pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline(use_audio=True)
