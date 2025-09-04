
# Purchase Agreement Filler — Streamlit Cloud (DOCX only, Purchaser uppercased)

- Outputs **.docx** only (Streamlit Community Cloud cannot run Word/LibreOffice)
- Ensures **purchaser** is **UPPERCASED** in the generated document
- Ampersands render correctly (RichText fields)
- Currency formatting for `death_benefit`, `purchase_price`, `p_reimburse`
- `execution_date` → `{{day}}`, `{{month}}`, `{{year}}`

## Deploy to Streamlit Community Cloud
1. Create a GitHub repo and add these files.
2. Go to https://share.streamlit.io/ → New App → select repo/branch → `app.py` → Deploy.

## Local Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Customize
- To disable uppercasing, remove the block that sets `context["purchaser"] = context["purchaser"].upper()`.
