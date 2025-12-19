# Evaluation Report

This document outlines the evaluation criteria used to validate the Voice Agent's performance and provides transcripts of test scenarios covering successful operations, failures, and edge cases.

## 📊 Evaluation Criteria

The system is evaluated against the following key metrics:

1.  **Latency**:
    *   **Target**: < 2 seconds from end-of-speech to start-of-audio.
    *   **Measurement**: Time taken for STT + Planning + TTS generation.
2.  **Intent Recognition Accuracy**:
    *   **Target**: > 95% success rate in identifying user intent (e.g., Eligibility Check vs. General Info vs. Chitchat).
3.  **Tool Usage Correctness**:
    *   **Target**: 100% correct parameter extraction (e.g., extracting "5 acres" accurately).
4.  **Resilience (Error Handling)**:
    *   **Target**: System should never crash on invalid input; must degrade gracefully with a polite fallback message.
5.  **Language Naturalness**:
    *   **Metric**: Qualitative assessment of Telugu response fluency (avoiding robotic "Google Translate" phrasing).

---

## 📝 Test Transcripts

### 1. ✅ Successful Interaction (Happy Path)
**Scenario**: User checks eligibility for the "Rythu Bandhu" scheme.

> **User**: "నమస్తే, నేను రైతు బంధు పథకానికి అర్హుడినా అని తెలుసుకోవాలి అనుకుంటున్నాను." (Namaste, I want to know if I am eligible for Rythu Bandhu.)
>
> **Agent (Thinking)**: Intent identified: `check_eligibility`. Missing `land_acres` and `occupation`.
>
> **Agent**: "నమస్కారం! తప్పకుండా సహాయం చేస్తాను. మీకు ఎంత పొలం ఉంది మరియు మీరు దేని కోసం వ్యవసాయం చేస్తున్నారు?" (Hello! I can help. How much land do you have and what crops do you grow?)
>
> **User**: "నాకు 5 ఎకరాల పొలం ఉంది, వరి పండిస్తాను." (I have 5 acres, I grow paddy.)
>
> **Agent (Thinking)**: Parameters extracted: `land_acres=5`, `crop=paddy`. Tool `check_eligibility` executed. Result: Eligible, Amount=25000.
>
> **Agent**: "సంతోషం! రైతు బంధు పథకం నిబంధనల ప్రకారం మీరు అర్హులు. మీకు ఎకరానికి 5000 చొప్పున, మొత్తం 25,000 రూపాయలు ప్రభుత్వం నుండి అందుతాయి." (Good news! You are eligible. You will receive 25,000 Rs total at 5000 per acre.)

### 2. ❌ Failed Interaction (Recovery Mode)
**Scenario**: Speech-to-Text fails or produces unintelligible output due to background noise.

> **User**: (Loud background construction noise) "...ఆ... పథకం... (unclear)..."
>
> **Agent (Thinking)**: STT Confidence < 0.6. Transcript: "aa pathakam" (incomplete).
>
> **Agent**: "క్షమించండి, మీ మాటలు స్పష్టంగా వినిపించలేదు. దయచేసి కాస్త గట్టిగా లేదా స్పష్టంగా మళ్ళీ చెప్పండి?" (Sorry, words were not clear. Please speak louder or clearly again.)
>
> **User**: "రైతు బంధు గురించి చెప్పండి." (Tell me about Rythu Bandhu.)
>
> **Agent (Thinking)**: Intent: `search_schemes`.
>
> **Agent**: "రైతు బంధు తెలంగాణ ప్రభుత్వ పథకం..." (Proceeds with explanation).

### 3. ⚠️ Edge-Case Interaction (Conflict Resolution)
**Scenario**: User provides contradictory information (Income) during the session.

> **User**: "నా ఆదాయం సంవత్సరానికి 50 వేలు ఉంటుంది." (My income is 50k per year.)
>
> **Agent (Internal)**: Memory updated: `profile.income = 50000`.
>
> **User**: (Later in conversation) "అవును, మాకు వ్యాపారం ఉంది, సంవత్సరానికి 2 లక్షలు వస్తాయి." (Yes, we have business, we get 2 Lakhs/year.)
>
> **Agent (Thinking)**: Conflict Detected! `profile.income` (50000) != `new_input` (200000). System prioritizes safety/honesty.
>
> **Agent**: "ఒక్క నిమిషం, ఇంతకుముందు మీ ఆదాయం 50 వేలు అని చెప్పారు, ఇప్పుడు 2 లక్షలు అంటున్నారు. సరైన సమాచారం చెప్తే నేను సరిగ్గా గైడ్ చేయగలను. మీ అసలు ఆదాయం ఎంత?" (Wait, you said 50k earlier, now 2L. Please confirm correct amount.)
>
> **User**: "సారీ, 2 లక్షలే కరెక్ట్." (Sorry, 2L is correct.)
>
> **Agent**: "సరే, ధన్యవాదాలు. మీ ఆదాయం 2 లక్షలు కాబట్టి, మీరు రేషన్ కార్డుకు అర్హులు కాకపోవచ్చు..." (Okay. Since income is 2L, you might not be eligible for Ration card...)
