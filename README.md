# VoltForge prototype

A small Streamlit demonstration for the TECHgium presentation.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy publicly for free
1. Create a GitHub repository, e.g. `voltforge-prototype`.
2. Upload `app.py`, `requirements.txt`, and this README.
3. Visit https://share.streamlit.io/ and sign in with GitHub.
4. Select **Create app**, choose the repository, branch `main`, and file `app.py`.
5. Click **Deploy**. Share the resulting `*.streamlit.app` URL or QR code in your presentation.

## Demo script
Use the defaults (5.5 kW, 415 V, 3-phase, PF 0.85, efficiency 0.90). Click **Generate draft design**.
Show the generated PanelSpec, calculated current, catalog candidate selection, PASS/FAIL/UNKNOWN checks, and downloadable JSON evidence passport.

## Important limitations
This is an educational proof-of-concept, not an IEC/UL compliance tool. The catalog and selection heuristic are illustrative. In particular, the 125% value is a demonstration assumption, not a general motor-protection sizing rule. Compliance, short-circuit coordination, overload protection, cable sizing, enclosure, thermal and layout checks remain UNKNOWN and require approved rules, manufacturer data and qualified engineer approval.
