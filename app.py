from flask import Flask, request, send_file, jsonify
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')  # Must be before pyplot import for headless server
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import os
import urllib.request
import json

app = Flask(__name__)

GEOJSON_PATH = 'twCounty.geojson'
GEOJSON_URL = "https://raw.githubusercontent.com/g0v/twgeojson/master/json/twCounty2010.geo.json"

# ─── Load or Download GeoJSON ────────────────────────────
def load_geodata():
    global gdf
    if not os.path.exists(GEOJSON_PATH):
        print("twCounty.geojson not found, downloading...")
        urllib.request.urlretrieve(GEOJSON_URL, GEOJSON_PATH)
        print("Download complete.")
    gdf = gpd.read_file(GEOJSON_PATH, engine='pyogrio')
    print(f"GeoJSON loaded: {len(gdf)} counties")
    print(f"Columns: {list(gdf.columns)}")

gdf = None
try:
    load_geodata()
except Exception as e:
    print(f"Error loading GeoJSON: {e}")

# ─── Font Setup for Linux (Render) ───────────────────────
# On Render (Linux), we use matplotlib's default fonts.
# CJK fonts may not be available, so we use a Unicode-capable fallback.
plt.rcParams['font.sans-serif'] = [
    'Noto Sans CJK TC', 'Noto Sans CJK SC', 'WenQuanYi Zen Hei',
    'Arial Unicode MS', 'DejaVu Sans', 'sans-serif'
]
plt.rcParams['axes.unicode_minus'] = False

# ─── Color scale based on CWA rainfall thresholds ────────
def get_color(val):
    if val <= 0:
        return '#F5F5F5'   # No rain - light grey
    elif val < 10:
        return '#E3F2FD'   # Very light - pale blue
    elif val < 40:
        return '#90CAF9'   # Light rain - light blue
    elif val < 80:
        return '#42A5F5'   # Moderate - blue (大雨 threshold)
    elif val < 130:
        return '#FFCA28'   # Heavy - yellow (短延時大雨)
    elif val < 200:
        return '#FF9800'   # Very heavy - orange (豪雨)
    elif val < 350:
        return '#F44336'   # Extreme - red (大豪雨)
    else:
        return '#9C27B0'   # Catastrophic - purple (超大豪雨)

# ─── Health check endpoint ────────────────────────────────
@app.route('/', methods=['GET'])
def health():
    status = "GeoJSON loaded" if gdf is not None else "GeoJSON not loaded"
    return jsonify({"status": "ok", "geojson": status})

# ─── Main map generation endpoint ─────────────────────────
@app.route('/generate_map', methods=['POST'])
def generate_map():
    if gdf is None:
        return jsonify({"error": "GeoJSON not loaded"}), 500

    data = request.json or {}

    # Normalize '臺' -> '台' to match GeoJSON (g0v uses 台, CWA uses 臺)
    normalized_data = {}
    for k, v in data.items():
        k_norm = k.replace('臺', '台')
        normalized_data[k_norm] = float(v) if v else 0.0

    # Find the county name column
    county_col = None
    for col in ['COUNTYNAME', 'name', 'NAME', 'County']:
        if col in gdf.columns:
            county_col = col
            break
    if county_col is None:
        county_col = gdf.columns[0]
        print(f"Warning: guessing county column as '{county_col}'")

    # Map rainfall data
    gdf['rainfall'] = gdf[county_col].map(normalized_data).fillna(0)
    gdf['color'] = gdf['rainfall'].apply(get_color)

    # ─── Plotting ─────────────────────────────────────────
    fig, ax = plt.subplots(1, 1, figsize=(9, 11))
    fig.patch.set_facecolor('#FAFAFA')
    ax.set_facecolor('#E8F4FD')

    gdf.plot(ax=ax, color=gdf['color'], edgecolor='#555555', linewidth=0.6)

    # ─── Labels ───────────────────────────────────────────
    for _, row in gdf.iterrows():
        county = row[county_col]
        rain = row['rainfall']
        centroid = row['geometry'].centroid
        
        if rain > 0:
            label = f"{county}\n{rain:.1f}mm"
            weight = 'bold'
            fsize = 7.5
        else:
            label = county
            weight = 'normal'
            fsize = 7

        ax.annotate(
            text=label,
            xy=(centroid.x, centroid.y),
            ha='center', va='center',
            fontsize=fsize,
            color='#222222',
            fontweight=weight
        )

    # ─── Legend ───────────────────────────────────────────
    legend_items = [
        (mpatches.Patch(color='#F5F5F5'), '無雨 (0mm)'),
        (mpatches.Patch(color='#90CAF9'), '有雨 (10~40mm)'),
        (mpatches.Patch(color='#42A5F5'), '大雨 (40~80mm)'),
        (mpatches.Patch(color='#FFCA28'), '豪雨 (80~130mm)'),
        (mpatches.Patch(color='#FF9800'), '大豪雨 (130~200mm)'),
        (mpatches.Patch(color='#F44336'), '超大豪雨 (200~350mm)'),
        (mpatches.Patch(color='#9C27B0'), '極端豪雨 (>350mm)'),
    ]
    handles = [h for h, _ in legend_items]
    labels  = [l for _, l in legend_items]
    ax.legend(handles, labels, loc='lower left', fontsize=7.5,
              framealpha=0.9, title='雨量等級', title_fontsize=8)

    ax.axis('off')
    ax.set_title('台灣各縣市累積雨量分布圖', fontsize=13, fontweight='bold',
                 pad=12, color='#333333')

    # ─── Output ───────────────────────────────────────────
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
