from flask import Flask, request, send_file
import geopandas as gpd
import matplotlib.pyplot as plt
import io
import os
import matplotlib.font_manager as fm

app = Flask(__name__)

# Load GeoJSON
# Assuming twCounty.geojson is present
try:
    gdf = gpd.read_file('twCounty.geojson')
    # Make sure we have a recognizable column for county name
    # Usually in g0v data it's properties.COUNTYNAME
except Exception as e:
    gdf = None
    print("Error loading geojson:", e)

# Use a font that supports Traditional Chinese (adjust for deployment environment)
plt.rcParams['font.sans-serif'] = ['PingFang HK', 'Heiti TC', 'Noto Sans CJK TC', 'Microsoft JhengHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

@app.route('/generate_map', methods=['POST'])
def generate_map():
    if gdf is None:
        return "GeoJSON not loaded", 500
        
    data = request.json or {}
    
    # We expect data to be like {"臺北市": 10.5, "高雄市": 200, ...}
    # Note: '台' vs '臺' could be an issue, normalize to '臺' for matching g0v dataset
    normalized_data = {}
    for k, v in data.items():
        k_norm = k.replace('台', '臺')
        normalized_data[k_norm] = float(v)
        
    # Map data to the GeoDataFrame
    gdf['rainfall'] = gdf['COUNTYNAME'].map(normalized_data).fillna(0)
    
    # Define a custom plotting logic based on rainfall
    def get_color(val):
        if val <= 0:
            return '#FFFFFF' # White for no rain
        elif val < 10:
            return '#E0F7FA' # Very light blue
        elif val < 40:
            return '#80DEEA' # Light blue
        elif val < 80:
            return '#26C6DA' # Blue (大雨)
        elif val < 130:
            return '#FFCA28' # Yellow (短延時大雨)
        elif val < 200:
            return '#FF9800' # Orange (豪雨)
        elif val < 350:
            return '#F44336' # Red (大豪雨)
        else:
            return '#9C27B0' # Purple (超大豪雨)
            
    gdf['color'] = gdf['rainfall'].apply(get_color)
    
    # Plotting
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    gdf.plot(ax=ax, color=gdf['color'], edgecolor='#666666', linewidth=0.5)
    
    # Add labels
    for idx, row in gdf.iterrows():
        county = row['COUNTYNAME']
        rain = row['rainfall']
        centroid = row['geometry'].centroid
        
        # Determine text
        if rain > 0:
            label = f"{county}\n{rain:.1f}"
        else:
            label = county
            
        ax.annotate(text=label, 
                    xy=(centroid.x, centroid.y),
                    xytext=(3, 3), textcoords="offset points",
                    ha='center', va='center',
                    fontsize=8, color='#333333',
                    fontweight='bold' if rain > 0 else 'normal')
    
    ax.axis('off')
    
    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', transparent=True)
    buf.seek(0)
    plt.close(fig)
    
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    # Default host and port for local testing
    app.run(host='0.0.0.0', port=5000)
