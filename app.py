from __future__ import annotations
import io, zipfile
from datetime import datetime, timezone
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from PIL import Image
from studio.config import ASPECTS, STYLES, MODEL
from studio.db import init_db, add_generation, recent_generations
from studio.providers.openai_provider import OpenAIImageProvider
from studio.service import build_prompt, validate_image

st.set_page_config(page_title="Lumina — Image Studio", page_icon="✦", layout="wide")
st.markdown("""<style>
:root{color-scheme:dark}
.stApp{background:radial-gradient(ellipse at 12% 0%,#12333b 0%,#101820 35%,#0b1118 75%);color:#e9f3f5}
.block-container{max-width:1320px;padding-top:2rem}
.hero{padding:1.5rem 1.8rem;border:1px solid #24515a;border-radius:20px;background:linear-gradient(120deg,#142b35dd,#101a25dd);margin-bottom:1.3rem}
.eyebrow{color:#5fe0d0;font-size:.78rem;letter-spacing:.18em;font-weight:700}
.hero h1{font-size:2.45rem;margin:.3rem 0;color:#f3fbfc}
.hero p{color:#a9c2c8;margin:0}
div[data-testid="stMetric"]{background:#14242c;border:1px solid #28434c;padding:12px;border-radius:12px}
.stButton>button[kind="primary"]{background:linear-gradient(90deg,#10a99e,#27c9bd);color:#061b1c;border:0;font-weight:800}
div[data-testid="stVerticalBlockBorderWrapper"]{border-color:#28434c!important}
</style>""", unsafe_allow_html=True)
init_db()
st.markdown('<div class="hero"><div class="eyebrow">✦ CREATIVE INTELLIGENCE / IMAGE LAB</div><h1>Lumina Image Studio</h1><p>Turn a thought into a visual. Compose, generate, refine, and collect.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Studio controls")
    provider_name = st.selectbox("Provider", ["OpenAI"])
    model = st.selectbox("Model", [MODEL], index=0)
    aspect_label = st.selectbox("Aspect ratio", list(ASPECTS))
    size = ASPECTS[aspect_label]
    quality = st.select_slider("Quality", options=["low", "medium", "high"], value="medium")
    output_format = st.selectbox("Output format", ["png", "jpeg", "webp"])
    count = st.slider("Images to generate", 1, 4, 1)
    st.caption(f"Output canvas: {size[0]} × {size[1]} px")
    st.divider()
    st.caption("OpenAI credentials are read from OPENAI_API_KEY or Streamlit secrets.")

left, right = st.columns([1.08, .92], gap="large")
with left:
    st.subheader("01 / Describe your image")
    prompt = st.text_area("Main prompt", height=155, max_chars=4000,
        placeholder="A cinematic photograph of a glass greenhouse in a misty alpine valley at sunrise...")
    st.caption(f"{len(prompt)} / 4,000 characters")
    negative = st.text_input("Avoid (optional)", placeholder="blurry, text, watermark, oversaturated")
    style = st.selectbox("Art direction", list(STYLES))
    custom_style = st.text_input("Custom style details (optional)", placeholder="e.g. editorial film grain, muted earth tones")
    enhance = st.checkbox("Enhance prompt with composition and lighting guidance", value=True)
    if st.button("✦ Generate artwork", type="primary", use_container_width=True):
        if not prompt.strip():
            st.error("Enter an image description before generating.")
        else:
            final_prompt = build_prompt(prompt, style, custom_style, negative, enhance)
            try:
                with st.spinner("Creating your artwork… this can take a little while."):
                    provider = OpenAIImageProvider(model=model)
                    results = provider.generate(final_prompt, size=size, quality=quality,
                                                output_format=output_format, count=count)
                    saved = []
                    for item in results:
                        image = validate_image(item["bytes"])
                        record_id = add_generation(
                            prompt=prompt, final_prompt=final_prompt, style=style, model=model,
                            size=f"{image.width}x{image.height}", quality=quality,
                            output_format=output_format, image_bytes=item["bytes"],
                            revised_prompt=item.get("revised_prompt", "")
                        )
                        saved.append({"id": record_id, "bytes": item["bytes"], "image": image,
                                      "prompt": prompt, "final_prompt": final_prompt,
                                      "style": style, "model": model, "quality": quality,
                                      "format": output_format, "size": f"{image.width}x{image.height}"})
                    st.session_state["latest"] = saved
                    st.success(f"Successfully generated {len(saved)} image(s).")
            except Exception as exc:
                st.error(f"Generation failed: {exc}")
                st.info("Check your API key, account access, quota, and network connection. Your prompt has not been lost.")
with right:
    st.subheader("02 / Canvas")
    latest = st.session_state.get("latest", [])
    if latest:
        for idx, item in enumerate(latest):
            st.image(item["image"], caption=f'{item["size"]} · {item["style"]}', use_container_width=True)
            st.download_button("⬇ Download image", data=item["bytes"],
                file_name=f'l um ina-{item["id"]}.{item["format"]}'.replace(" ", ""),
                mime=f'image/{item["format"]}', key=f'dl_{item["id"]}')
            with st.expander("Generation details"):
                st.write({"model": item["model"], "quality": item["quality"], "format": item["format"],
                          "style": item["style"], "prompt": item["prompt"]})
        if len(latest) > 1:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
                for i, item in enumerate(latest, 1):
                    archive.writestr(f"lumina_{i}.{item['format']}", item["bytes"])
            st.download_button("⬇ Download all (ZIP)", buffer.getvalue(), "lumina_gallery.zip",
                               "application/zip", use_container_width=True)
    else:
        st.markdown("""<div style="height:370px;border:1px dashed #37616a;border-radius:18px;
        display:flex;align-items:center;justify-content:center;text-align:center;color:#8daab1;
        background:linear-gradient(135deg,#15252d,#101820)">
        <div><div style="font-size:3rem;color:#50d8ca">✧</div><b>Your canvas is waiting</b><br>
        <small>Write a prompt and generate your first image.</small></div></div>""", unsafe_allow_html=True)

st.divider()
st.subheader("03 / Generation history")
history = recent_generations(limit=30)
if history:
    cols = st.columns(3)
    for i, row in enumerate(history):
        with cols[i % 3]:
            try:
                st.image(row["image_bytes"], use_container_width=True)
                st.caption(f'{row["created_at"][:16]} · {row["model"]} · {row["size"]}')
                with st.expander("Prompt"):
                    st.write(row["prompt"])
                    st.download_button("Download", row["image_bytes"],
                        file_name=f"history_{row['id']}.{row['output_format']}",
                        mime=f"image/{row['output_format']}", key=f'hist_{row["id"]}')
            except Exception:
                st.warning(f"History item {row['id']} could not be displayed.")
else:
    st.caption("Your generated images will appear here. History is stored locally in SQLite.")
