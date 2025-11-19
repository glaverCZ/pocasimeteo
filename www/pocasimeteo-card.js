/*! PočasíMeteo Weather Card */

class PocasimeteoCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._selectedModel = 'MASTER';
    console.log('🎨 PocasimeteoCard constructor called');
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity for pocasimeteo-card');
    }
    this.config = config;
    this._selectedModel = config.default_model || 'MASTER';
    console.log('🎨 Config set:', this.config);
  }

  set hass(hass) {
    this._hass = hass;

    if (!this.shadowRoot.hasChildNodes()) {
      this.render();
    }

    this.updateContent();
  }

  render() {
    const card = document.createElement('ha-card');

    const style = document.createElement('style');
    style.textContent = `
      * { box-sizing: border-box; }

      ha-card {
        overflow: hidden;
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid var(--divider-color);
        background: var(--secondary-background-color);
      }

      .header-left h2 {
        margin: 0;
        font-size: 20px;
      }

      .model-selector {
        background: var(--primary-background-color);
        border: 2px solid var(--primary-color);
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        cursor: pointer;
        color: var(--primary-text-color);
      }

      .current-weather {
        display: flex;
        align-items: center;
        justify-content: space-around;
        padding: 24px 16px;
        background: linear-gradient(135deg, var(--primary-color) 0%, rgba(33, 150, 243, 0.8) 100%);
        color: white;
      }

      .weather-icon {
        font-size: 80px;
        min-width: 100px;
        text-align: center;
      }

      .weather-icon img {
        width: 80px;
        height: 80px;
        object-fit: contain;
      }

      .weather-main {
        flex: 1;
      }

      .temperature {
        font-size: 56px;
        font-weight: 300;
        line-height: 1;
        margin: 0;
      }

      .condition {
        font-size: 18px;
        opacity: 0.9;
      }

      .details-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1px;
        background: var(--divider-color);
      }

      .detail-item {
        background: var(--primary-background-color);
        padding: 12px;
        text-align: center;
      }

      .detail-label {
        font-size: 12px;
        opacity: 0.6;
        margin-bottom: 4px;
      }

      .detail-value {
        font-size: 18px;
        font-weight: 500;
      }

      .stale-warning {
        background: #fff3cd;
        color: #856404;
        padding: 12px 16px;
        text-align: center;
        font-weight: 500;
        border-bottom: 1px solid #ffc107;
      }

      .forecast-section {
        padding: 16px;
      }

      .forecast-title {
        font-weight: 500;
        margin-bottom: 12px;
        color: var(--primary-text-color);
      }

      .hourly-forecast {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding-bottom: 8px;
      }

      .forecast-item {
        flex-shrink: 0;
        min-width: 60px;
        text-align: center;
        padding: 8px;
        background: var(--secondary-background-color);
        border-radius: 8px;
      }

      .forecast-time {
        font-size: 12px;
        opacity: 0.6;
      }

      .forecast-icon {
        font-size: 32px;
        margin: 4px 0;
      }

      .forecast-icon img {
        width: 40px;
        height: 40px;
        object-fit: contain;
      }

      .forecast-temp {
        font-size: 14px;
        font-weight: 500;
      }

      .daily-forecast {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .daily-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px;
        background: var(--secondary-background-color);
        border-radius: 8px;
      }

      .daily-day {
        flex: 1;
        font-weight: 500;
      }

      .daily-temps {
        display: flex;
        gap: 16px;
        align-items: center;
      }

      .no-data {
        text-align: center;
        padding: 20px;
        color: var(--secondary-text-color);
      }
    `;

    const content = document.createElement('div');
    content.innerHTML = `
      <div class="card-header">
        <div class="header-left">
          <h2>PočasíMeteo</h2>
        </div>
        <select class="model-selector" id="modelSelect">
          <option value="MASTER">Master</option>
          <option value="ALADIN">ALADIN</option>
          <option value="ICON">ICON</option>
          <option value="GFS">GFS</option>
          <option value="ECMWF">ECMWF</option>
          <option value="WRF">WRF</option>
          <option value="COSMO">COSMO</option>
          <option value="ARPEGE">ARPEGE</option>
        </select>
      </div>
      <div id="staleWarning" class="stale-warning" style="display:none;">
        ⚠️ Data jsou zastaralá
      </div>
      <div class="current-weather">
        <div class="weather-icon" id="currentIcon">☀️</div>
        <div class="weather-main">
          <div class="temperature"><span id="temp">--</span>°C</div>
          <div class="condition" id="condition">--</div>
        </div>
      </div>
      <div class="details-grid">
        <div class="detail-item">
          <div class="detail-label">Vlhkost</div>
          <div class="detail-value"><span id="humidity">--</span>%</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">Tlak</div>
          <div class="detail-value"><span id="pressure">--</span> hPa</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">Vítr</div>
          <div class="detail-value"><span id="wind">--</span> m/s</div>
        </div>
      </div>
      <div class="forecast-section">
        <div class="forecast-title">Hodinová předpověď (24h)</div>
        <div class="hourly-forecast" id="hourlyForecast">
          <div class="no-data">Načítání...</div>
        </div>
      </div>
      <div class="forecast-section">
        <div class="forecast-title">Denní předpověď (7d)</div>
        <div class="daily-forecast" id="dailyForecast">
          <div class="no-data">Načítání...</div>
        </div>
      </div>
    `;

    card.appendChild(style);
    card.appendChild(content);
    this.shadowRoot.appendChild(card);

    this.shadowRoot.querySelector('#modelSelect').addEventListener('change', (e) => {
      this._selectedModel = e.target.value;
      this.updateContent();
    });

    console.log('🎨 Card rendered');
  }

  updateContent() {
    const entity = this._hass.states[this.config.entity];
    if (!entity) {
      console.warn('🎨 Entity not found:', this.config.entity);
      return;
    }

    const state = entity.state;
    const attrs = entity.attributes;

    console.log('🎨 Updating with entity:', this.config.entity, 'State:', state, 'Attrs:', attrs);

    // Aktuální počasí
    const tempEl = this.shadowRoot.querySelector('#temp');
    const conditionEl = this.shadowRoot.querySelector('#condition');
    const humidityEl = this.shadowRoot.querySelector('#humidity');
    const pressureEl = this.shadowRoot.querySelector('#pressure');
    const windEl = this.shadowRoot.querySelector('#wind');
    const iconEl = this.shadowRoot.querySelector('#currentIcon');
    const staleWarning = this.shadowRoot.querySelector('#staleWarning');

    if (tempEl) tempEl.textContent = attrs.temperature ?? '--';
    if (conditionEl) conditionEl.textContent = this.translateCondition(attrs.condition) ?? '--';
    if (humidityEl) humidityEl.textContent = attrs.humidity ?? '--';
    if (pressureEl) pressureEl.textContent = attrs.pressure ?? '--';
    if (windEl) windEl.textContent = (attrs.wind_speed ?? '--');

    // Ikona
    if (attrs.icon_code) {
      const img = document.createElement('img');
      img.src = `/local/icons/${attrs.icon_code}.png`;
      img.alt = attrs.condition || 'weather';
      img.onerror = () => {
        console.log('🎨 Icon not found:', attrs.icon_code);
        iconEl.textContent = this.getWeatherEmoji(attrs.condition);
      };
      iconEl.innerHTML = '';
      iconEl.appendChild(img);
    } else {
      iconEl.textContent = this.getWeatherEmoji(attrs.condition);
    }

    // Varovní banner
    if (attrs.data_stale) {
      staleWarning.style.display = 'block';
    } else {
      staleWarning.style.display = 'none';
    }

    // Hodinová předpověď
    const hourlyForecast = this.shadowRoot.querySelector('#hourlyForecast');
    if (attrs.forecast_hourly && Array.isArray(attrs.forecast_hourly)) {
      hourlyForecast.innerHTML = '';
      attrs.forecast_hourly.slice(0, 24).forEach(f => {
        const item = document.createElement('div');
        item.className = 'forecast-item';

        const time = new Date(f.datetime || f.forecast_time).toLocaleTimeString('cs-CZ', { hour: '2-digit' });
        const temp = Math.round(f.temperature || f.templow || 0);
        const condition = f.condition || 'unknown';

        item.innerHTML = `
          <div class="forecast-time">${time}</div>
          <div class="forecast-icon">${this.getWeatherEmoji(condition)}</div>
          <div class="forecast-temp">${temp}°</div>
        `;
        hourlyForecast.appendChild(item);
      });
    }

    // Denní předpověď
    const dailyForecast = this.shadowRoot.querySelector('#dailyForecast');
    if (attrs.forecast_daily && Array.isArray(attrs.forecast_daily)) {
      dailyForecast.innerHTML = '';
      attrs.forecast_daily.slice(0, 7).forEach(f => {
        const item = document.createElement('div');
        item.className = 'daily-item';

        const date = new Date(f.datetime || f.forecast_time).toLocaleDateString('cs-CZ', { weekday: 'short' });
        const tempMax = Math.round(f.temperature || 0);
        const tempMin = Math.round(f.templow || 0);

        item.innerHTML = `
          <div class="daily-day">${date}</div>
          <div style="flex: 0.5; text-align: center;">${this.getWeatherEmoji(f.condition)}</div>
          <div class="daily-temps">
            <span style="font-weight: 500;">${tempMax}°</span>
            <span style="opacity: 0.6;">${tempMin}°</span>
          </div>
        `;
        dailyForecast.appendChild(item);
      });
    }
  }

  getWeatherEmoji(condition) {
    const emojis = {
      'sunny': '☀️',
      'partlycloudy': '⛅',
      'cloudy': '☁️',
      'rainy': '🌧️',
      'snowy': '❄️',
      'fog': '🌫️',
      'lightning-rainy': '⛈️',
      'unknown': '🌡️'
    };
    return emojis[condition] || '🌡️';
  }

  translateCondition(condition) {
    const translations = {
      'sunny': 'Slunečno',
      'partlycloudy': 'Polojasno',
      'cloudy': 'Zataženo',
      'rainy': 'Déšť',
      'snowy': 'Sníh',
      'fog': 'Mlha',
      'lightning-rainy': 'Bouřka',
    };
    return translations[condition] || condition;
  }

  getConfig() {
    return this.config;
  }

  getCardSize() {
    return 8;
  }

  static getStubConfig() {
    return {
      entity: 'weather.pocasimeteo_praha_6_ruzyne',
      default_model: 'MASTER'
    };
  }
}

// Registruj custom element
customElements.define('pocasimeteo-card', PocasimeteoCard);
console.log('🎨 PocasimeteoCard registered');

// Registruj pro Lovelace
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'pocasimeteo-card',
  name: 'PočasíMeteo Card',
  description: 'Weather forecast card for PočasíMeteo integration',
  preview: true,
  documentationURL: 'https://github.com/lkrasa/pocasimeteo_ha'
});
console.log('🎨 Card registered in Lovelace');
