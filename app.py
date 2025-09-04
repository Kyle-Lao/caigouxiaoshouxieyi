# Streamlit Purchase Agreement Filler — Streamlit Cloud (DOCX only, purchaser uppercased)
# Run locally: streamlit run app.py
# On Streamlit Cloud: deploy this repo; no PDF conversion (Word/LibreOffice not available).
import io, re
from pathlib import Path
import datetime as dt
import streamlit as st

from docxtpl import DocxTemplate, RichText

try:
    import yaml
except Exception:
    yaml = None

st.set_page_config(page_title="Purchase Agreement Filler", page_icon="📝", layout="centered")
st.title("📝 LCC Purchase Agreement Filler")

TEMPLATE_PATH = Path("templates/purchase_agreement_template.docx")
FIELDS_SCHEMA = Path("templates/fields.yaml")

st.info("This cloud build outputs **.docx only** (PDF requires Microsoft Word or LibreOffice, which are not available on Streamlit Community Cloud).")

def load_fields_schema():
    if FIELDS_SCHEMA.exists() and yaml is not None:
        data = yaml.safe_load(FIELDS_SCHEMA.read_text(encoding="utf-8"))
        fields = data.get("fields", [])
        norm = []
        for f in fields:
            name = f.get("name")
            if not name:
                continue
            norm.append({
                "name": name,
                "label": f.get("label", name.replace("_", " ").title()),
                "type": (f.get("type") or "text").lower(),
                "required": bool(f.get("required", False)),
                "format": f.get("format"),
                "default": f.get("default", ""),
                "hint": f.get("hint", ""),
            })
        return norm
    st.stop()

if not TEMPLATE_PATH.exists():
    st.error("Template not found at templates/purchase_agreement_template.docx.")
    st.stop()

def format_currency_like(value: str) -> str:
    if value is None:
        return ""
    txt = str(value).strip()
    if txt == "":
        return ""
    cleaned = txt.replace(",", "").replace("$", "")
    m = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not m:
        return txt
    num_str = m.group(0)
    try:
        if "." in num_str:
            val = float(num_str)
            return f"${val:,.2f}"
        else:
            val_i = int(num_str)
            return f"${val_i:,}"
    except Exception:
        try:
            val = float(num_str)
            return f"${val:,.2f}"
        except Exception:
            return txt

fields = load_fields_schema()

st.subheader("Fill fields")
context = {}
execution_date_obj = None

for f in fields:
    ftype = f["type"]
    label = f["label"]
    name = f["name"]
    hint = f.get("hint") or ""
    default = f.get("default") or ""
    fmt = f.get("format")
    helptext = hint if hint else None

    if ftype == "date":
        default_date = dt.date.today()
        if default:
            try:
                default_date = dt.datetime.strptime(default, fmt or "%m/%d/%Y").date()
            except Exception:
                pass
        val = st.date_input(label, value=default_date, help=helptext, key=f"field_{name}")
        context[name] = val.strftime(fmt or "%m/%d/%Y")
        if name == "execution_date":
            execution_date_obj = val

    elif ftype in ("int", "number"):
        val = st.number_input(label, value=float(default) if default != "" else 0.0, step=1.0, help=helptext, key=f"field_{name}")
        context[name] = int(val) if float(val).is_integer() else val

    elif ftype == "textarea":
        val = st.text_area(label, value=str(default), help=helptext, key=f"field_{name}")
        context[name] = val

    else:
        val = st.text_input(label, value=str(default), help=helptext, key=f"field_{name}")
        context[name] = val

# Derive day / month / year from execution_date
if execution_date_obj:
    context["day"] = execution_date_obj.strftime("%d")
    context["month"] = execution_date_obj.strftime("%m")
    context["year"] = execution_date_obj.strftime("%Y")

# Currency-style formatting
for money_key in ("death_benefit", "purchase_price", "p_reimburse"):
    if money_key in context:
        context[money_key] = format_currency_like(context[money_key])

# --- Force "purchaser" to UPPERCASE in the output ---
if "purchaser" in context and isinstance(context["purchaser"], str):
    context["purchaser"] = context["purchaser"].upper()

# RichText for fields that might include '&'
RICH_TEXT_FIELDS = {"purchaser", "signatory", "signatory_title", "purchaser_address", "carrier"}
for k in list(context.keys()):
    if k in RICH_TEXT_FIELDS and isinstance(context[k], str):
        rt = RichText()
        rt.add(context[k])
        context[k] = rt

st.write("---")
output_filename = st.text_input("Output filename (no extension)", value="Purchase_Agreement")

if st.button("Generate .docx", type="primary"):
    # Required check
    miss = [f["label"] for f in fields if f.get("required") and not str(context.get(f["name"], "")).strip()]
    if miss:
        st.error("Please fill required fields: " + ", ".join(miss))
    else:
        try:
            tpl = DocxTemplate(TEMPLATE_PATH.as_posix())
            tpl.render(context)
            out = io.BytesIO()
            tpl.save(out)
            out.seek(0)
            st.download_button(
                label="⬇️ Download Word (.docx)",
                data=out.getvalue(),
                file_name=f"{output_filename}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            st.caption("Need a PDF? Export the downloaded .docx with Word, or deploy this app on a machine with Word/LibreOffice.")
        except Exception as e:
            st.error(f"Failed to generate: {e}")
