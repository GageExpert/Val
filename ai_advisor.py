"""AI advisor for assumptions and narratives."""
from __future__ import annotations

import json
import os
from typing import Dict, List

import numpy as np


def build_recommendations(profile: Dict[str, str], history: Dict[str, float]) -> Dict[str, object]:
    base_growth = 0.06
    stage = profile.get("stage", "mature").lower()
    if "high" in stage:
        base_growth = 0.12
    elif "turnaround" in stage:
        base_growth = 0.04
    margin = history.get("gross_margin", 0.45)
    wacc = 0.09 if profile.get("size", "mid").lower() in {"large", "mega"} else 0.11

    recommendations = {
        "revenue_growth": {
            "value": base_growth,
            "range": [base_growth - 0.03, base_growth + 0.03],
            "rationale": "Growth reflects stage and historical trend.",
        },
        "gross_margin": {
            "value": margin,
            "range": [max(0.1, margin - 0.1), min(0.9, margin + 0.1)],
            "rationale": "Margin anchored to history with profile adjustment.",
        },
        "wacc": {
            "value": wacc,
            "range": [wacc - 0.02, wacc + 0.02],
            "rationale": "WACC based on size and stability.",
        },
    }

    return {
        "recommended_assumptions": recommendations,
        "valuation_method_recommendation": {
            "method": "Both",
            "reasons": ["Blend DCF and comps for balanced view."],
        },
        "key_value_drivers": [
            "Revenue growth trajectory",
            "Margin expansion",
            "Reinvestment intensity",
        ],
        "risks": ["Macro slowdown", "Execution risk"],
        "plausibility_score": 72,
        "plausibility_reasons": ["Assumptions in line with recent history."],
    }


def ai_enhance_recommendations(base_payload: Dict[str, object]) -> Dict[str, object]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return base_payload
    try:
        import openai

        client = openai.OpenAI(api_key=api_key)
        prompt = (
            "Enhance these valuation recommendations with concise rationales."
            " Return JSON only.\n" + json.dumps(base_payload)
        )
        response = client.responses.create(model="gpt-4o-mini", input=prompt)
        content = response.output_text
        return json.loads(content)
    except Exception:
        return base_payload
