# Viscosity Temperature Analysis (Streamlit)

Enter the viscosity at 40 C and 100 C. The app draws the ASTM D341
viscosity-temperature chart with your oil's line, shows the viscosity at the
minimum / normal / maximum operating temperatures, and lets you download:

- **Chart PNG** (11 x 7 in, 300 dpi) - insert into the image box of the fillable PDF form
- **Full report PDF** and **PNG** - header, details, operating table and chart on one A4 page

## Run on your computer
```
pip install -r requirements.txt
streamlit run app.py
```

## Put it online (Streamlit Community Cloud)
1. Create a GitHub repository and upload these files: `app.py`, `viscosity.py`,
   `requirements.txt`, `.streamlit/config.toml`.
2. Go to https://share.streamlit.io, sign in with GitHub, choose "New app",
   pick the repository, set the main file to `app.py`, and deploy.
3. You get a link to send to the client.

## Keep it private (recommended for audit data)
In the app's **Settings > Secrets** add this line:
```
APP_PASSWORD = "choose-a-password"
```
The app then asks for the password before showing anything. (Without it, anyone
with the link can open the app. Nothing the user types is stored by the app.)

## How the line is calculated
ASTM D341: log10(log10(v + 0.7)) = A - B * log10(T + 273.15), with v in cSt and
T in C. A and B come from the two viscosities entered. On this chart's scales the
line is straight.

## Files
- `app.py` - the web interface
- `viscosity.py` - the maths and the chart / report drawing
