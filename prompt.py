PROMPT_TMPL = """Create a high-quality professional profile photo.

INPUT IMAGES:
- Main subject: the FIRST uploaded image (this is the person to render).
- Optional props: up to 3 additional images containing clothing or accessories. If provided, transfer only the outfit/accessory design to the main subject. Do not change the face identity based on prop images.

Subject Settings:
- Composition: {구도}
- Expression: {표정}
- Lighting: {조명}
- Mood/Feeling: {느낌}
- Background: {배경}

Identity Preservation (highest priority):
- Keep the same person as in the FIRST image. Do NOT create a new person.
- Preserve unique facial traits: overall face shape, eye shape/size, nose and lip shape, hairline, moles/freckles, skin undertone, age/gender cues.
- Allowed beautification (subtle only): even skin tone and slightly brighter exposure, light blemish cleanup, slightly sharper eyes, gentle jawline definition.
- Do NOT alter iris color, hairstyle length, facial hair status, or face proportions beyond a subtle refinement (max ~5% slimming). No nose/eye reshaping.

Props Application (only if prop images exist):
- Use clothing/accessory design from prop images on the main subject.
- Match fit and perspective naturally; ignore prop image backgrounds.

General Requirements:
- Realistic studio-grade portrait. Subject must be the main focus (background can be softly blurred).
- Maintain consistent lighting with the chosen tone.
- Keep body and facial proportions natural.
- No added text, logos, or unrelated props.

Output Style:
- Photorealistic, clean, balanced lighting
- Suitable for professional or social media profile use

Priority Order (in case of conflicts):
1) Identity preservation of the main subject
2) Composition & expression
3) Lighting & mood
4) Props from additional images
5) Background styling

Negative Constraints:
- over-smoothing, plastic skin, cartoonish look
- distorted anatomy, excessive slimming, AI artifacts
- changed identity (different person), mismatched age/gender
- text or logos in the image
"""