/*! PočasíMeteo Weather Card - HA 2024.1+ Compatible */

(() => {
  class PocasimeteoCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this._selectedEntityId = null;
      this._availableModels = [];
      this._currentEntity = null;
    }

    setConfig(config) {
      if (!config.entity) throw new Error('entity je povinná');
      this.config = config;
      this._selectedEntityId = config.entity;

      // Konfigurovaná seznam modelů k porovnání
      this._modelConfigs = config.models || [
        { name: 'MASTER', label: 'MASTER' },
        { name: 'ALADIN', label: 'ALADIN' },
        { name: 'ICON', label: 'ICON' },
        { name: 'GFS', label: 'GFS' },
        { name: 'ECMWF', label: 'ECMWF' },
        { name: 'WRF', label: 'WRF' },
        { name: 'COSMO', label: 'COSMO' },
        { name: 'ARPEGE', label: 'ARPEGE' }
      ];

      // Entita pro automatickou detekci modelu
      this._temperatureEntity = config.temperature_entity;
    }

    set hass(hass) {
      this._hass = hass;

      // První render
      if (!this.shadowRoot.hasChildNodes()) {
        this._buildAvailableModels();
        this._render();
      }

      this._updateContent();
    }

    _buildAvailableModels() {
      if (!this._hass || !this.config) return;

      const entity = this._hass.states[this.config.entity];
      if (!entity) return;

      // Zj isti stanici z entity_id (weather.pocasimeteo_STATION_MODEL)
      const entityId = this.config.entity;
      const models = [];

      // Extrahuj stanici z primární entity
      const match = entityId.match(/pocasimeteo_([a-z0-9_]+?)(?:_[a-z]+)?$/);
      if (!match) return;

      const station = match[1]; // praha_6_ruzyne nebo brno, atd.
      const prefix = `weather.pocasimeteo_${station}`;

      // Zkus najít entity pro každý model
      this._modelConfigs.forEach(modelConfig => {
        const modelLower = modelConfig.name.toLowerCase();
        let entityIdToCheck = prefix;

        // Primární entita (bez suffixu) je primární model
        if (modelConfig.name === 'MASTER') {
          entityIdToCheck = prefix;
        } else {
          entityIdToCheck = `${prefix}_${modelLower}`;
        }

        // Zkontroluj, zda entita existuje
        if (this._hass.states[entityIdToCheck]) {
          models.push({
            name: modelConfig.name,
            label: modelConfig.label,
            entityId: entityIdToCheck
          });
        }
      });

      this._availableModels = models;
    }

    _autoSelectBestModel() {
      if (!this._temperatureEntity || !this._hass) return;

      const tempEntity = this._hass.states[this._temperatureEntity];
      if (!tempEntity) return;

      const refTemp = tempEntity.state;
      if (refTemp === undefined || refTemp === 'unknown') return;

      const referenceTemperature = parseFloat(refTemp);
      if (isNaN(referenceTemperature)) return;

      // Porovnej s aktuálníteplotami všech dostupných modelů
      let bestModel = null;
      let bestDiff = Infinity;

      this._availableModels.forEach(model => {
        const modelEntity = this._hass.states[model.entityId];
        if (!modelEntity) return;

        const modelTemp = modelEntity.attributes?.temperature;
        if (modelTemp === undefined) return;

        const diff = Math.abs(modelTemp - referenceTemperature);
        if (diff < bestDiff) {
          bestDiff = diff;
          bestModel = model;
        }
      });

      // Pokud jsme našli nejbližší model a není to aktuálně vybraný, vyber ho
      if (bestModel && bestModel.entityId !== this._selectedEntityId) {
        this._selectedEntityId = bestModel.entityId;

        // Aktualizuj aktivní tab
        const tabs = this.shadowRoot?.querySelectorAll('.model-tab');
        if (tabs) {
          tabs.forEach(tab => tab.classList.remove('active'));
        }

        // Najdi a označ aktivní tab
        if (this._availableModels.indexOf(bestModel) >= 0) {
          const tabIndex = this._availableModels.indexOf(bestModel);
          const tabs = this.shadowRoot?.querySelectorAll('.model-tab');
          if (tabs && tabs[tabIndex]) {
            tabs[tabIndex].classList.add('active');
          }
        }
      }
    }

    _render() {
      const style = document.createElement('style');
      style.textContent = `
        * { box-sizing: border-box; margin: 0; padding: 0; }

        ha-card {
          overflow: hidden;
          --ha-card-border-radius: 12px;
        }

        .card-container {
          background: var(--primary-background-color);
          color: var(--primary-text-color);
        }

        /* Header - Model Selector */
        .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          border-bottom: 1px solid var(--divider-color);
          background: linear-gradient(90deg, rgba(33, 150, 243, 0.05) 0%, rgba(33, 150, 243, 0) 100%);
          gap: 12px;
        }

        .card-title {
          font-size: 16px;
          font-weight: 700;
          letter-spacing: -0.3px;
          flex-shrink: 0;
        }

        .model-tabs {
          display: flex;
          gap: 4px;
          flex-wrap: wrap;
          overflow-x: auto;
          flex: 1;
        }

        .model-tabs::-webkit-scrollbar {
          height: 3px;
        }

        .model-tabs::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 2px;
        }

        .model-tab {
          padding: 5px 10px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(33, 150, 243, 0.3);
          border-radius: 5px;
          cursor: pointer;
          font-size: 11px;
          font-weight: 500;
          transition: all 0.2s ease;
          color: var(--secondary-text-color);
          white-space: nowrap;
          flex-shrink: 0;
        }

        .model-tab:hover {
          background: rgba(33, 150, 243, 0.15);
          border-color: var(--primary-color);
        }

        .model-tab.active {
          background: var(--primary-color);
          color: white;
          border-color: var(--primary-color);
        }

        .model-precision {
          font-size: 10px;
          opacity: 0.8;
          margin-top: 1px;
        }

        /* Stale warning */
        .stale-warning {
          background: #fff3cd;
          color: #856404;
          padding: 12px 16px;
          text-align: center;
          font-weight: 500;
          font-size: 13px;
          border-bottom: 1px solid rgba(133, 100, 4, 0.2);
        }

        /* Current Weather - Compact */
        .current-section {
          padding: 14px 16px;
          background: linear-gradient(135deg, rgba(33, 150, 243, 0.08) 0%, rgba(33, 150, 243, 0.03) 100%);
          border-bottom: 1px solid var(--divider-color);
        }

        .current-weather {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .weather-icon {
          font-size: 56px;
          min-width: 56px;
          text-align: center;
        }

        .weather-icon img {
          width: 56px;
          height: 56px;
          object-fit: contain;
        }

        .weather-main {
          flex: 1;
        }

        .temperature {
          font-size: 38px;
          font-weight: 300;
          line-height: 1;
          margin-bottom: 2px;
        }

        .condition {
          font-size: 13px;
          opacity: 0.8;
          margin-bottom: 1px;
        }

        .data-age {
          font-size: 11px;
          opacity: 0.6;
        }

        /* Details Grid */
        .details-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1px;
          background: var(--divider-color);
          margin: 0;
        }

        .detail-item {
          background: var(--primary-background-color);
          padding: 10px 12px;
          text-align: center;
        }

        .detail-label {
          font-size: 10px;
          opacity: 0.6;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 3px;
        }

        .detail-value {
          font-size: 15px;
          font-weight: 500;
        }

        /* Forecast Sections */
        .forecast-section {
          padding: 12px 16px;
          border-bottom: 1px solid var(--divider-color);
        }

        .forecast-title {
          font-weight: 600;
          font-size: 12px;
          margin-bottom: 10px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          opacity: 0.8;
        }

        /* Hourly Forecast */
        .hourly-forecast {
          display: flex;
          gap: 5px;
          overflow-x: auto;
          padding-bottom: 6px;
        }

        .hourly-forecast::-webkit-scrollbar {
          height: 3px;
        }

        .hourly-forecast::-webkit-scrollbar-track {
          background: transparent;
        }

        .hourly-forecast::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 2px;
        }

        .forecast-item {
          flex-shrink: 0;
          min-width: 56px;
          padding: 7px;
          background: var(--secondary-background-color);
          border-radius: 5px;
          text-align: center;
          font-size: 11px;
          display: flex;
          flex-direction: column;
          gap: 3px;
        }

        .forecast-item-time {
          font-weight: 500;
          font-size: 10px;
          opacity: 0.8;
        }

        .forecast-item-icon {
          font-size: 24px;
          flex-shrink: 0;
        }

        .forecast-item-icon img {
          width: 24px;
          height: 24px;
          object-fit: contain;
        }

        .forecast-item-temp {
          font-weight: 600;
          font-size: 12px;
        }

        .forecast-item-wind {
          font-size: 10px;
          opacity: 0.8;
        }

        .forecast-item-rain {
          font-size: 10px;
          opacity: 0.8;
          color: rgba(33, 150, 243, 0.8);
        }

        /* Daily Forecast */
        .daily-forecast {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .daily-item {
          display: grid;
          grid-template-columns: 60px 28px 1fr auto;
          align-items: center;
          gap: 10px;
          padding: 10px 12px;
          background: var(--secondary-background-color);
          border-radius: 5px;
          font-size: 12px;
        }

        .daily-day {
          font-weight: 500;
          font-size: 12px;
        }

        .daily-icon {
          font-size: 22px;
        }

        .daily-icon img {
          width: 22px;
          height: 22px;
          object-fit: contain;
        }

        .daily-temps {
          text-align: left;
          font-weight: 500;
          font-size: 12px;
        }

        .daily-temp-max {
          color: var(--primary-color);
        }

        .daily-temp-min {
          opacity: 0.6;
          font-size: 11px;
        }

        .daily-rain {
          min-width: 50px;
          text-align: right;
          font-size: 11px;
          color: rgba(33, 150, 243, 0.8);
        }

        .rain-icon {
          display: inline-block;
          margin-right: 2px;
        }
      `;

      const card = document.createElement('ha-card');

      const content = document.createElement('div');
      content.className = 'card-container';

      // Header s model selectorem
      const header = document.createElement('div');
      header.className = 'card-header';

      const title = document.createElement('div');
      title.className = 'card-title';
      title.textContent = 'PočasíMeteo';
      header.appendChild(title);

      const tabs = document.createElement('div');
      tabs.className = 'model-tabs';
      tabs.id = 'modelTabs';
      header.appendChild(tabs);

      content.appendChild(header);

      // Stale warning
      const warning = document.createElement('div');
      warning.id = 'staleWarning';
      warning.className = 'stale-warning';
      warning.style.display = 'none';
      warning.textContent = '⚠️ Data jsou zastaralá (>90 minut)';
      content.appendChild(warning);

      // Current weather
      const current = document.createElement('div');
      current.className = 'current-section';
      current.innerHTML = `
        <div class="current-weather">
          <div class="weather-icon" id="icon">🌡️</div>
          <div class="weather-main">
            <div class="temperature"><span id="temp">--</span>°C</div>
            <div class="condition" id="cond">--</div>
            <div class="data-age" id="dataAge"></div>
          </div>
        </div>
      `;
      content.appendChild(current);

      // Details grid
      const details = document.createElement('div');
      details.className = 'details-grid';
      details.innerHTML = `
        <div class="detail-item">
          <div class="detail-label">Vlhkost</div>
          <div class="detail-value"><span id="hum">--</span>%</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">Tlak</div>
          <div class="detail-value"><span id="pres">--</span> hPa</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">Vítr</div>
          <div class="detail-value"><span id="wind">--</span> m/s</div>
        </div>
      `;
      content.appendChild(details);

      // Hourly forecast
      const hourlySection = document.createElement('div');
      hourlySection.className = 'forecast-section';
      hourlySection.innerHTML = `
        <div class="forecast-title">Hodinová Předpověď (48h)</div>
        <div class="hourly-forecast" id="hourly"></div>
      `;
      content.appendChild(hourlySection);

      // Daily forecast
      const dailySection = document.createElement('div');
      dailySection.className = 'forecast-section';
      dailySection.innerHTML = `
        <div class="forecast-title">Denní Předpověď (7 dní)</div>
        <div class="daily-forecast" id="daily"></div>
      `;
      content.appendChild(dailySection);

      card.appendChild(style);
      card.appendChild(content);
      this.shadowRoot.appendChild(card);

      // Setup model tabs
      this._setupModelTabs();
    }

    _setupModelTabs() {
      const tabsContainer = this.shadowRoot.querySelector('#modelTabs');
      if (!tabsContainer || !this._availableModels.length) return;

      this._availableModels.forEach(model => {
        const tab = document.createElement('div');
        tab.className = 'model-tab';
        if (this._selectedEntityId === model.entityId) {
          tab.classList.add('active');
        }

        tab.innerHTML = `
          <div>${model.label}</div>
          <div class="model-precision" id="precision-${model.name}"></div>
        `;

        tab.addEventListener('click', () => {
          this._selectedEntityId = model.entityId;

          // Update active tab
          this.shadowRoot.querySelectorAll('.model-tab').forEach(t => {
            t.classList.remove('active');
          });
          tab.classList.add('active');

          this._updateContent();
        });

        tabsContainer.appendChild(tab);
      });
    }

    _updateContent() {
      if (!this._hass || !this._selectedEntityId) return;

      // Pokud je nastavena temperature_entity, zkus najít nejbližší model
      if (this._temperatureEntity && this._availableModels.length > 0) {
        this._autoSelectBestModel();
      }

      const entity = this._hass.states[this._selectedEntityId];
      if (!entity) return;

      const a = entity.attributes || {};
      const sr = this.shadowRoot;

      // Current weather
      sr.querySelector('#temp').textContent = a.temperature !== undefined ? Math.round(a.temperature) : '--';
      sr.querySelector('#cond').textContent = a.condition || '--';
      sr.querySelector('#hum').textContent = a.humidity !== undefined ? a.humidity : '--';
      sr.querySelector('#pres').textContent = a.pressure !== undefined ? a.pressure : '--';
      sr.querySelector('#wind').textContent = a.wind_speed !== undefined ? a.wind_speed.toFixed(1) : '--';

      // Data age
      if (a.data_age_minutes !== undefined) {
        sr.querySelector('#dataAge').textContent = `Data je ${a.data_age_minutes} minut stará`;
      }

      // Stale warning
      sr.querySelector('#staleWarning').style.display = a.data_stale ? 'block' : 'none';

      // Icon - PNG z JSON
      const iconEl = sr.querySelector('#icon');
      if (a.icon_code) {
        const img = document.createElement('img');
        img.src = `/local/icons/${a.icon_code}.png`;
        img.onerror = () => {
          iconEl.textContent = '❓';
        };
        iconEl.innerHTML = '';
        iconEl.appendChild(img);
      }

      // Update precision info
      this._availableModels.forEach(model => {
        const precisionEl = sr.querySelector(`#precision-${model.name}`);
        if (precisionEl) {
          const modelEntity = this._hass.states[model.entityId];
          if (modelEntity && modelEntity.attributes.data_age_minutes !== undefined) {
            precisionEl.textContent = `${modelEntity.attributes.data_age_minutes}m`;
          }
        }
      });

      // Hourly forecast
      const hourly = sr.querySelector('#hourly');
      if (a.forecast_hourly && Array.isArray(a.forecast_hourly)) {
        hourly.innerHTML = '';
        a.forecast_hourly.slice(0, 24).forEach((f, idx) => {
          const div = document.createElement('div');
          div.className = 'forecast-item';

          const dt = new Date(f.datetime || f.forecast_time);
          const time = dt.toLocaleTimeString('cs-CZ', { hour: '2-digit' });
          const temp = f.temperature ? Math.round(f.temperature) : '--';
          const wind = this._formatWindInfo(f.wind_speed, f.wind_gust);
          const rain = f.precipitation !== undefined ? f.precipitation : 0;
          const rainDisplay = rain > 0 ? `${rain}mm` : '--';

          div.innerHTML = `
            <div class="forecast-item-time">${time}</div>
            <div class="forecast-item-icon" id="hourly-icon-${idx}">📌</div>
            <div class="forecast-item-temp">${temp}°</div>
            <div class="forecast-item-wind">${wind} m/s</div>
            <div class="forecast-item-rain">${rainDisplay}</div>
          `;

          hourly.appendChild(div);

          // Load icon - předej icon_code z předpovědi
          this._loadForecastIcon(div.querySelector(`#hourly-icon-${idx}`), f.icon_code, f.condition || 'unknown');
        });
      }

      // Daily forecast
      const daily = sr.querySelector('#daily');
      if (a.forecast_daily && Array.isArray(a.forecast_daily)) {
        daily.innerHTML = '';
        a.forecast_daily.slice(0, 7).forEach((f, idx) => {
          const div = document.createElement('div');
          div.className = 'daily-item';

          const dt = new Date(f.datetime || f.forecast_time);
          const day = dt.toLocaleDateString('cs-CZ', { weekday: 'short' });
          const max = f.temperature ? Math.round(f.temperature) : '--';
          const min = f.templow ? Math.round(f.templow) : '--';
          const rain = f.precipitation !== undefined ? f.precipitation : 0;
          const rainIcon = this._getPrecipitationIcon(f.condition || 'rainy');
          const rainDisplay = rain > 0 ? `${rainIcon} ${rain}mm` : `${rainIcon} -`;

          div.innerHTML = `
            <div class="daily-day">${day}</div>
            <div class="daily-icon" id="daily-icon-${idx}">📌</div>
            <div class="daily-temps">
              <div><span class="daily-temp-max">${max}°</span></div>
              <div><span class="daily-temp-min">${min}°</span></div>
            </div>
            <div class="daily-rain">${rainDisplay}</div>
          `;

          daily.appendChild(div);

          // Load icon - předej icon_code z předpovědi
          this._loadForecastIcon(div.querySelector(`#daily-icon-${idx}`), f.icon_code, f.condition || 'unknown');
        });
      }
    }

    _loadForecastIcon(iconEl, iconCode, condition) {
      if (!iconEl) return;

      // Preferuj icon_code, fallback na mapování condition
      let finalIconCode = iconCode;

      // Validuj icon_code - měl by začínat 'a' a obsahovat čísla
      if (!finalIconCode || !this._isValidIconCode(finalIconCode)) {
        // Fallback mapování podmínky na icon code
        const conditionToIcon = {
          'sunny': 'a01d',
          'partlycloudy': 'a02d',
          'cloudy': 'a03d',
          'rainy': 'a10',
          'snowy': 'a13',
          'lightning-rainy': 'a11',
          'fog': 'a50',
          'unknown': 'a04'
        };
        finalIconCode = conditionToIcon[condition] || 'a04';
      }

      const img = document.createElement('img');
      img.src = `/local/icons/${finalIconCode}.png`;
      img.onerror = () => {
        iconEl.textContent = '❓';
      };

      iconEl.innerHTML = '';
      iconEl.appendChild(img);
    }

    _isValidIconCode(iconCode) {
      // Icon code by měl být ve formátu: a01d, a10, a13 atd.
      return typeof iconCode === 'string' && /^a\d+/.test(iconCode);
    }

    _getPrecipitationIcon(condition) {
      // Vrátí ikonu pro typ srážek na základě podmínky
      if (condition === 'snowy' || condition === 'snow') {
        return '❄️';
      } else if (condition === 'rainy' || condition === 'lightning-rainy' || condition === 'rain') {
        return '💧';
      }
      return '💧'; // Default
    }

    _formatWindInfo(windSpeed, windGust) {
      if (windSpeed === undefined || windSpeed === null) return '--';
      const speed = typeof windSpeed === 'number' ? windSpeed.toFixed(1) : windSpeed;
      if (windGust !== undefined && windGust !== null) {
        const gust = typeof windGust === 'number' ? windGust.toFixed(1) : windGust;
        return `${speed}↗${gust}`;
      }
      return `${speed}`;
    }

    static getStubConfig() {
      return {
        type: 'custom:pocasimeteo-card',
        entity: 'weather.pocasimeteo_praha_6_ruzyne',
        // Volitelné: seznam modelů k zobrazení
        models: [
          { name: 'MASTER', label: 'Master' },
          { name: 'ALADIN', label: 'ALADIN' },
          { name: 'ICON', label: 'ICON' },
          { name: 'GFS', label: 'GFS' },
          { name: 'ECMWF', label: 'ECMWF' }
        ],
        // Volitelné: entita teploty pro automatickou detekci modelu
        // temperature_entity: 'sensor.outdoor_temperature'
      };
    }

    getCardSize() {
      return 10;
    }
  }

  customElements.define('pocasimeteo-card', PocasimeteoCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'pocasimeteo-card',
    name: 'PočasíMeteo Card',
    description: 'Modern weather forecast with multiple model selection'
  });
})();
