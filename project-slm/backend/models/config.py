"""
Model Config — Recommended models, hardware estimates, and defaults.
"""


class ModelConfig:
    """Static config for recommended models and their hardware profiles."""

    RECOMMENDED_MODELS = [
        {
            "name": "qwen3:4b",
            "display_name": "Qwen 3 4B",
            "params": "4B",
            "quant": "Q4_K_M",
            "size_gb": 2.5,
            "ram_needed_gb": 4.5,
            "strengths": "Reasoning, coding, multilingual, math, tool-use",
            "tier": "local_lite",
            "recommended": True,
            "label": "⭐ Recommended for most users",
        },
        {
            "name": "phi4-mini",
            "display_name": "Phi-4 Mini",
            "params": "3.8B",
            "quant": "Q4_K_M",
            "size_gb": 2.2,
            "ram_needed_gb": 4.0,
            "strengths": "Logic, math, reasoning, long context (128K)",
            "tier": "local_lite",
            "recommended": False,
            "label": "Best for logic & math",
        },
        {
            "name": "llama3.2:3b",
            "display_name": "Llama 3.2 3B",
            "params": "3B",
            "quant": "Q4_K_M",
            "size_gb": 1.8,
            "ram_needed_gb": 3.5,
            "strengths": "Lightweight, multilingual, fast, summarization",
            "tier": "local_lite",
            "recommended": False,
            "label": "Lightest — for very old hardware",
        },
        {
            "name": "gemma3:4b",
            "display_name": "Gemma 3 4B",
            "params": "4B",
            "quant": "Q4_K_M",
            "size_gb": 2.5,
            "ram_needed_gb": 4.5,
            "strengths": "General purpose, creative writing, explanations",
            "tier": "local_lite",
            "recommended": False,
            "label": "Good all-rounder",
        },
        {
            "name": "llama3.2:1b",
            "display_name": "Llama 3.2 1B",
            "params": "1B",
            "quant": "Q4_K_M",
            "size_gb": 0.8,
            "ram_needed_gb": 2.0,
            "strengths": "Ultra-light, basic tasks, edge devices",
            "tier": "pi",
            "recommended": False,
            "label": "For Raspberry Pi / <4GB RAM",
        },
    ]

    # Hardware tier thresholds
    TIER_RECOMMENDATIONS = {
        "pi": {"min_ram_gb": 2, "max_ram_gb": 4, "description": "Raspberry Pi / ultra-low spec"},
        "local_lite": {"min_ram_gb": 6, "max_ram_gb": 8, "description": "Old laptop, no GPU"},
        "local_power": {"min_ram_gb": 16, "max_ram_gb": None, "description": "Decent hardware"},
        "cloud": {"min_ram_gb": 0, "max_ram_gb": None, "description": "Any device with internet"},
    }

    @classmethod
    def recommend_for_ram(cls, available_ram_gb: float) -> list:
        """Recommend models based on available RAM."""
        suitable = []
        for model in cls.RECOMMENDED_MODELS:
            if model["ram_needed_gb"] <= available_ram_gb * 0.7:  # leave 30% for OS
                suitable.append(model)
        return suitable or [cls.RECOMMENDED_MODELS[-1]]  # fallback to smallest
