/*! PočasíMeteo Weather Card - HA 2024.1+ Compatible */

(() => {
  class PocasimeteoCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this._selectedEntityId = null;
      this._availableModels = [];
      this._currentEntity = null;
      this._userSelectedModel = false; // Флаг - uživatel ručně vybral model
      this._timeUpdateInterval = null; // Interval pro aktualizaci času
      this._hourlyRefreshTimeout = null; // Timeout pro hodinový refresh předpovědi
      this._todayHoliday = '---'; // Cache pro svátek na dnes
      this._holidayFetchDate = null; // Datum posledního fetche pro cache invalidaci
      this._imageCache = {}; // Cache pro načtené obrázky ikon
      this._lastChartRender = null; // Timestamp posledního vykreslení grafu
      this._lastContentUpdate = null; // Timestamp poslední aktualizace obsahu (pro throttling)
      this._tooltipHideTimeout = null; // Timeout pro skrytí tooltipu s prodlevou
      this._timeUpdateTimeout = null; // Timeout pro aktualizaci času (odděleno od hourlyRefreshTimeout)
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
        { name: 'ARPEGE', label: 'ARPEGE' },
        { name: 'YRno', label: 'YRno' }
      ];

      // Entita pro automatickou detekci modelu - NEW: best_match_temperature_entity
      this._bestMatchTemperatureEntity = config.best_match_temperature_entity || config.temperature_entity;
      this._temperatureEntity = config.temperature_entity;
      this._bestMatchModel = null; // Bude nastaven později

      // Layout a zobrazení konfigurací
      this._showCurrentWeather = config.show_current_weather !== false; // Default: true
      this._showHourlyForecast = config.show_hourly_forecast !== false; // Default: true
      this._showDailyForecast = config.show_daily_forecast !== false; // Default: true
      this._fullWidth = config.full_width === true; // Default: false

      // Zvětšení všech položek (0.8 = -20%, 1.0 = 100%, 1.2 = +20%, atd.)
      this._scale = config.scale || 1.0; // Default: 1.0 (bez změny)

      // Počet hodin pro hodinovou předpověď (1-72, default: 24)
      this._hourlyHours = Math.min(Math.max(config.hourly_hours || 24, 1), 72);
    }

    set hass(hass) {
      this._hass = hass;

      // První render
      if (!this.shadowRoot.hasChildNodes()) {
        this._buildAvailableModels();
        this._selectBestModel(); // Vybrat nejpřesnější model na začátku
        this._render();
        this._setupHourlyRefresh(); // Setup hourly refresh for forecast updates
      } else {
        // Při aktualizaci také zkontroluj nejpřesnější model
        this._selectBestModel();
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
      // Pokud se dostupné modely změnily a není vybraný model, zvol první
      if (models.length > 0 && !this._selectedEntityId) {
        this._selectedEntityId = models[0].entityId;
      }
    }

    _selectBestModel() {
      if (!this._bestMatchTemperatureEntity || !this._hass || !this._availableModels.length) {
        return;
      }

      const tempEntity = this._hass.states[this._bestMatchTemperatureEntity];
      if (!tempEntity) return;

      const refTemp = tempEntity.state;
      if (refTemp === undefined || refTemp === 'unknown') return;

      const referenceTemperature = parseFloat(refTemp);
      if (isNaN(referenceTemperature)) return;

      // Porovnej s aktuálními teplotami všech dostupných modelů
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

      this._bestMatchModel = bestModel; // Uložit nejpřesnější model pro CSS označení

      // Pokud je to první inicializace a uživatel vybral model, automaticky ho vyber
      if (bestModel && !this._userSelectedModel && bestModel.entityId !== this._selectedEntityId) {
        this._selectedEntityId = bestModel.entityId;
      }
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

        // Znovu načti obsah s novým modelem
        this._updateContentForSelectedModel();
        return true; // Signalizuj, že se model změnil
      }
      return false;
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

        /* Full width styling */
        ha-card.full-width {
          width: 100%;
        }

        /* Hidden sections */
        .hidden {
          display: none;
        }

        /* Header - Model Selector */
        .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 6px 12px;
          border-bottom: 1px solid var(--divider-color);
          background: linear-gradient(90deg, rgba(33, 150, 243, 0.05) 0%, rgba(33, 150, 243, 0) 100%);
          gap: 8px;
        }

        .card-title {
          font-size: 16px;
          font-weight: 700;
          letter-spacing: -0.3px;
          flex-shrink: 0;
        }

        .model-tabs {
          display: flex;
          gap: 3px;
          flex-wrap: wrap;
          overflow-x: auto;
          flex: 1;
          padding: 2px 0;
        }

        .model-tabs::-webkit-scrollbar {
          height: 3px;
        }

        .model-tabs::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 2px;
        }

        .model-tab {
          padding: 3px 8px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(33, 150, 243, 0.3);
          border-radius: 3px;
          cursor: pointer;
          font-size: 10px;
          font-weight: 500;
          transition: all 0.2s ease;
          color: var(--secondary-text-color);
          white-space: nowrap;
          flex-shrink: 0;
          line-height: 1;
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

        .model-tab.best-match {
          background: rgba(33, 150, 243, 0.25);
          border-color: var(--primary-color);
        }

        .model-tab.best-match.active {
          background: var(--primary-color);
          color: white;
        }

        .model-precision {
          font-size: 8px;
          opacity: 0.6;
          margin-top: 0;
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

        /* Current Weather - Invisible Table Layout */
        .current-section {
          padding: 8px 16px 4px 16px;
          border-bottom: 1px solid var(--divider-color);
        }

        .current-weather {
          display: grid;
          grid-template-columns: 80px 1fr;
          gap: 16px;
          align-items: start;
          padding: 0;
        }

        .weather-icon {
          font-size: 64px;
          width: 80px;
          height: auto;
          text-align: center;
          grid-row: 1 / 3;
        }

        .weather-icon img {
          width: 64px;
          height: 64px;
          object-fit: contain;
        }

        /* Invisible table - 2 rows × 4 columns */
        .weather-table {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 0;
          align-items: center;
          text-align: left;
        }

        .table-cell {
          padding: 8px 0;
          border: none;
          background: transparent;
          font-size: 13px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: flex-start;
          text-align: center;
        }

        .table-cell-label {
          font-size: 10px;
          opacity: 0.7;
          text-transform: uppercase;
          letter-spacing: 0.3px;
          margin-bottom: 4px;
          order: 1;
        }

        .table-cell-value {
          font-size: 16px;
          font-weight: 600;
          line-height: 1.2;
          display: flex;
          flex-direction: column;
          align-items: center;
          order: 2;
        }

        .table-cell-unit {
          font-size: 9px;
          opacity: 0.65;
          margin-top: 2px;
          letter-spacing: 0.2px;
        }

        .weather-left {
          display: none;
        }

        .weather-right {
          display: none;
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
          display: none;
        }

        .data-age {
          font-size: 11px;
          opacity: 0.6;
        }

        .temp-label {
          font-size: 10px;
          opacity: 0.8;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .temp-value {
          font-size: 18px;
          font-weight: 600;
          line-height: 1.2;
        }

        .humidity {
          font-size: 12px;
          margin-top: 4px;
        }

        .big-time {
          font-size: 24px;
          font-weight: 700;
          line-height: 1;
        }

        .small-date {
          font-size: 11px;
          opacity: 0.9;
        }

        .data-line {
          font-size: 12px;
          opacity: 0.95;
        }

        /* Details Grid */
        .details-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 1px;
          background: var(--divider-color);
          margin: 0;
        }

        .detail-item {
          background: var(--primary-background-color);
          padding: 4px 8px;
          text-align: center;
        }

        .detail-label {
          font-size: 9px;
          opacity: 0.6;
          text-transform: uppercase;
          letter-spacing: 0.3px;
          margin-bottom: 2px;
        }

        .detail-value {
          font-size: 15px;
          font-weight: 500;
        }

        /* Forecast Sections */
        .forecast-section {
          padding: 1px 0;
          margin: 0;
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
          position: relative;
          width: calc(100% - 2px);
          height: 200px;
          padding: 0;
          margin: 0;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 4px;
          box-sizing: border-box;
          display: flex;
          flex-direction: column;
        }

        .hourly-forecast canvas {
          width: 100%;
          flex: 1;
          display: block;
        }

        .hourly-forecast-tooltip {
          position: absolute;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 4px;
          padding: 6px 8px;
          font-size: 9px;
          color: rgba(255, 255, 255, 0.95);
          pointer-events: none;
          z-index: 1000;
          white-space: nowrap;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
          display: none;
          line-height: 1.2;
          backdrop-filter: blur(10px);
          text-align: center;
          width: auto;
          max-width: 100px;
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
          font-size: 32px;
          flex-shrink: 0;
        }

        .forecast-item-icon img {
          width: 32px;
          height: 32px;
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
          flex-direction: row;
          gap: 4px;
          overflow-x: visible;
          overflow-y: hidden;
          padding-bottom: 6px;
          margin: 0;
          padding: 0;
          scroll-behavior: smooth;
          flex-wrap: wrap;
          justify-content: flex-start;
        }

        .daily-forecast::-webkit-scrollbar {
          height: 8px;
        }

        .daily-forecast::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.08);
          border-radius: 4px;
          margin: 0 16px;
        }

        .daily-forecast::-webkit-scrollbar-thumb {
          background: rgba(33, 150, 243, 0.4);
          border-radius: 4px;
        }

        .daily-forecast::-webkit-scrollbar-thumb:hover {
          background: rgba(33, 150, 243, 0.7);
        }

        .daily-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
          padding: 5px 3px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 3px;
          font-size: 9px;
          min-width: 50px;
          flex: 1 1 calc(14.28% - 4px);
          max-width: 85px;
          text-align: center;
        }

        .daily-day {
          font-weight: 600;
          font-size: 10px;
          line-height: 1;
        }

        .daily-icon {
          font-size: 24px;
        }

        .daily-icon img {
          width: 24px;
          height: 24px;
          object-fit: contain;
        }

        .daily-temps {
          text-align: center;
          font-weight: 600;
          font-size: 11px;
          line-height: 1;
        }

        .daily-temp-max {
          color: var(--primary-color);
        }

        .daily-temp-min {
          opacity: 0.6;
          font-size: 9px;
        }

        .daily-wind {
          font-size: 9px;
          opacity: 0.8;
        }

        .daily-rain {
          font-size: 8px;
          color: rgba(33, 150, 243, 0.8);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .rain-icon {
          display: inline-block;
          margin-right: 2px;
        }
      `;

      const card = document.createElement('ha-card');
      if (this._fullWidth) {
        card.classList.add('full-width');
      }

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

      // Current weather with compact layout
      const current = document.createElement('div');
      current.className = 'current-section' + (this._showCurrentWeather ? '' : ' hidden');
      current.innerHTML = `
        <!-- Horní řádek: čas+datum+svátek | popis počasí | východ+západ -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 16px;">
          <div style="display: flex; gap: 4px; flex-direction: column; flex: 0 0 auto;">
            <div id="currentTime" style="font-size: 20px; font-weight: 700; line-height: 1;">--:--</div>
            <div id="currentDate" style="font-size: 11px; opacity: 0.75; line-height: 1.2;">--</div>
            <div id="todayHoliday" style="font-size: 10px; opacity: 0.65; line-height: 1.2;">---</div>
          </div>
          <div style="flex: 1; text-align: center; font-size: 12px; font-weight: 500;">
            <div id="weatherDescription" style="letter-spacing: 0.3px;">--</div>
          </div>
          <div style="display: flex; gap: 8px; font-size: 11px; flex: 0 0 auto;">
            <div style="text-align: right;">
              <div style="opacity: 0.65; font-size: 9px;">Východ</div>
              <div id="sunrise" style="font-weight: 600;">--:--</div>
            </div>
            <div style="text-align: right;">
              <div style="opacity: 0.65; font-size: 9px;">Západ</div>
              <div id="sunset" style="font-weight: 600;">--:--</div>
            </div>
          </div>
        </div>

        <!-- Ikona + hodnoty -->
        <div class="current-weather">
          <div class="weather-icon" id="icon">🌡️</div>
          <div class="weather-table">
            <!-- Row 1: Aktuální | Předpověď | Vlhkost | Srážky -->
            <div class="table-cell">
              <div class="table-cell-label">Aktuální</div>
              <div class="table-cell-value"><span id="entityTemp">--</span><div class="table-cell-unit">°C</div></div>
            </div>
            <div class="table-cell">
              <div class="table-cell-label">Předpověď</div>
              <div class="table-cell-value"><span id="forecastTemp">--</span><div class="table-cell-unit">°C</div></div>
            </div>
            <div class="table-cell">
              <div class="table-cell-label">Vlhkost</div>
              <div class="table-cell-value"><span id="humidity">--</span><div class="table-cell-unit">%</div></div>
            </div>
            <div class="table-cell">
              <div class="table-cell-label">Srážky</div>
              <div class="table-cell-value"><span id="precipitation">0</span><div class="table-cell-unit">mm</div></div>
            </div>
            <!-- Row 2: Tlak | Vítr | Nárazy | Směr -->
            <div class="table-cell">
              <div class="table-cell-label">Tlak</div>
              <div class="table-cell-value"><span id="pres">--</span><div class="table-cell-unit">hPa</div></div>
            </div>
            <div class="table-cell">
              <div class="table-cell-label">Vítr</div>
              <div class="table-cell-value"><span id="wind">--</span><div class="table-cell-unit">m/s</div></div>
            </div>
            <div class="table-cell">
              <div class="table-cell-label">Nárazy</div>
              <div class="table-cell-value"><span id="windGust">--</span><div class="table-cell-unit">m/s</div></div>
            </div>
            <div class="table-cell">
              <div class="table-cell-label">Směr</div>
              <div class="table-cell-value"><span id="windDir">--</span><div class="table-cell-unit"></div></div>
            </div>
          </div>
        </div>
        <div class="condition" id="cond">--</div>
      `;
      content.appendChild(current);

      // Hourly forecast
      const hourlySection = document.createElement('div');
      hourlySection.className = 'forecast-section' + (this._showHourlyForecast ? '' : ' hidden');
      hourlySection.innerHTML = `
        <div class="hourly-forecast" id="hourly"></div>
      `;
      content.appendChild(hourlySection);

      // Daily forecast
      const dailySection = document.createElement('div');
      dailySection.className = 'forecast-section' + (this._showDailyForecast ? '' : ' hidden');
      dailySection.innerHTML = `
        <div class="daily-forecast" id="daily"></div>
      `;
      content.appendChild(dailySection);

      card.appendChild(style);
      card.appendChild(content);

      // Aplikuj scaling pokud je nastavený
      if (this._scale !== 1.0) {
        card.style.transform = `scale(${this._scale})`;
        card.style.transformOrigin = 'top left';
        card.style.width = `${100 / this._scale}%`;
      }

      this.shadowRoot.appendChild(card);

      // Setup model tabs
      this._setupModelTabs();

      // Setup time update interval (every 30 seconds)
      this._startTimeUpdate();
    }

    _startTimeUpdate() {
      // Pokud je interval už běží, nepřepisuj ho znovu
      if (this._timeUpdateInterval) {
        console.log('[PočasíMeteo] Time update already scheduled, skipping');
        this._updateSystemTime(); // Ale aktualizuj čas hned
        return;
      }

      // Update time immediately
      this._updateSystemTime();

      // Schedule next update synchronously at the start of the next minute
      const now = new Date();
      const secondsUntilNextMinute = (60 - now.getSeconds()) * 1000;
      console.log(`[PočasíMeteo] Time update scheduled in ${Math.round(secondsUntilNextMinute / 1000)}s`);

      // Clear any existing time update timeout first
      if (this._timeUpdateTimeout) {
        clearTimeout(this._timeUpdateTimeout);
      }

      this._timeUpdateTimeout = setTimeout(() => {
        console.log('[PočasíMeteo] Triggering time update at minute start');
        this._updateSystemTime();
        // Then update every minute
        if (this._timeUpdateInterval) {
          clearInterval(this._timeUpdateInterval);
        }
        this._timeUpdateInterval = setInterval(() => {
          console.log('[PočasíMeteo] Updating time (interval)');
          this._updateSystemTime();
        }, 60000);
      }, secondsUntilNextMinute);
    }

    _setupHourlyRefresh() {
      // Clear any existing timeout
      if (this._hourlyRefreshTimeout) {
        clearTimeout(this._hourlyRefreshTimeout);
      }

      // Calculate time until next whole hour + random 1-2 minute offset
      const now = new Date();
      const nextHour = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours() + 1, 0, 0);
      const minuteOffset = Math.floor(Math.random() * 2) + 1; // 1-2 minutes
      nextHour.setMinutes(minuteOffset);

      const msUntilRefresh = nextHour.getTime() - now.getTime();

      // Schedule the refresh
      this._hourlyRefreshTimeout = setTimeout(() => {
        // Refresh the hourly forecast content
        this._updateContentForSelectedModel();

        // Recursively setup next refresh
        this._setupHourlyRefresh();
      }, msUntilRefresh);
    }

    _updateSystemTime() {
      const now = new Date();
      const sr = this.shadowRoot;

      // Format time as HH:MM
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const timeStr = `${hours}:${minutes}`;

      // Format date as "Pondělí 19.11" (Czech day name + day.month)
      const czechDayNames = ['Neděle', 'Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota'];
      const dayName = czechDayNames[now.getDay()];
      const day = String(now.getDate()).padStart(2, '0');
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const dateStr = `${dayName} ${day}.${month}`;

      // Update time and date elements (if they exist from old layout)
      const timeEl = sr.querySelector('#currentTime');
      if (timeEl) {
        timeEl.textContent = timeStr;
      }

      const dateEl = sr.querySelector('#currentDate');
      if (dateEl) {
        dateEl.textContent = dateStr;
      }

      // Load and update today's holiday
      const holidayEl = sr.querySelector('#todayHoliday');
      if (holidayEl) {
        this._loadTodayHoliday().then(holiday => {
          holidayEl.textContent = holiday;
        });
      }
    }

    disconnectedCallback() {
      // Clean up intervals/timeouts when card is removed
      if (this._timeUpdateInterval) {
        clearInterval(this._timeUpdateInterval);
      }
      if (this._timeUpdateTimeout) {
        clearTimeout(this._timeUpdateTimeout);
      }
      if (this._tooltipHideTimeout) {
        clearTimeout(this._tooltipHideTimeout);
      }
      if (this._hourlyRefreshTimeout) {
        clearTimeout(this._hourlyRefreshTimeout);
      }
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
        // Přidej CSS třídu best-match pro nejpřesnější model
        if (this._bestMatchModel && this._bestMatchModel.entityId === model.entityId) {
          tab.classList.add('best-match');
        }

        tab.innerHTML = `
          <div>${model.label}</div>
          <div class="model-precision" id="precision-${model.name}"></div>
        `;

        tab.addEventListener('click', () => {
          this._selectedEntityId = model.entityId;
          this._userSelectedModel = true; // Uživatel ručně vybral model

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

      // Throttle updates - don't update more than every 1000ms to prevent blinking
      const now = Date.now();
      if (this._lastContentUpdate && (now - this._lastContentUpdate) < 1000) {
        return;
      }
      this._lastContentUpdate = now;

      // Smart refresh: Pokud jsou data starší než 2 minuty, refresh hned (ne čekej na scheduler)
      const entity = this._hass.states[this._selectedEntityId];
      if (entity && entity.attributes) {
        const dataAgeMins = entity.attributes.data_age_minutes;
        if (dataAgeMins !== undefined && dataAgeMins > 2) {
          console.log(`Data are ${dataAgeMins} minutes old, requesting refresh...`);
          // Skryj první item v hodinové předpovědi (z minulé hodiny)
          const sr = this.shadowRoot;
          const hourlyContainer = sr.querySelector('#hourly');
          if (hourlyContainer && hourlyContainer.firstChild) {
            hourlyContainer.firstChild.style.display = 'none';
          }
          this._requestRefresh();
          return; // Počkej na refresh, pak se znovu zavolá _updateContent()
        }
      }

      // Pokud je nastavena temperature_entity a uživatel nezvolil model ručně,
      // zkus najít nejbližší model
      if (this._temperatureEntity && this._availableModels.length > 0 && !this._userSelectedModel) {
        const modelChanged = this._autoSelectBestModel();
        if (modelChanged) return; // _autoSelectBestModel() se o update postará
      }

      // Když se aktualizují data, zobraz zpátky první item
      const hourlyContainer = this.shadowRoot.querySelector('#hourly');
      if (hourlyContainer && hourlyContainer.firstChild) {
        hourlyContainer.firstChild.style.display = '';
      }

      this._updateContentForSelectedModel();
    }

    _getCurrentHourForecast(forecastHourly) {
      // Vrátí forecast data pro aktuální hodinu
      if (!forecastHourly || !Array.isArray(forecastHourly)) return null;

      const now = new Date();
      const currentHour = now.getHours();

      // Najdi první forecast item který je v aktuální hodině
      for (const item of forecastHourly) {
        const dt = new Date(item.datetime || item.forecast_time);
        if (dt.getHours() === currentHour) {
          return item;
        }
      }

      return null;
    }

    _getWeatherDescription(cloudiness, precipitation) {
      // Generuj textový popis počasí na základě O (oblačnost) a S (srážky)
      let conditions = '';

      const cloudPercent = parseInt(cloudiness);
      const precipMm = parseFloat(precipitation);

      if (cloudPercent <= 10) {
        conditions = 'Jasno';
      } else if (cloudPercent <= 30) {
        conditions = 'Skoro jasno';
      } else if (cloudPercent <= 70) {
        conditions = 'Polojasno';
      } else if (cloudPercent <= 90) {
        conditions = 'Oblačno';
      } else {
        conditions = 'Zataženo';
      }

      if (precipMm > 0) {
        if (precipMm < 0.5) {
          conditions += ', slabý déšť';
        } else if (precipMm < 2) {
          conditions += ', déšť';
        } else {
          conditions += ', silný déšť';
        }
      }

      return conditions;
    }

    _requestRefresh() {
      // Zavolej Home Assistant API k refreshu entity
      if (!this._hass || !this._selectedEntityId) return;

      console.log(`[PočasíMeteo] Requesting refresh for ${this._selectedEntityId}`);

      // Call the refresh service
      this._hass.callService('homeassistant', 'update_entity', {
        entity_id: this._selectedEntityId
      }).then(() => {
        console.log('[PočasíMeteo] Refresh service called successfully');
      }).catch((error) => {
        console.error('[PočasíMeteo] Refresh service error:', error);
      });
    }

    _updateContentForSelectedModel() {
      if (!this._hass || !this._selectedEntityId) return;

      const entity = this._hass.states[this._selectedEntityId];
      if (!entity) return;

      const a = entity.attributes || {};
      const sr = this.shadowRoot;

      // Current weather
      sr.querySelector('#cond').textContent = a.condition || '--';
      sr.querySelector('#pres').textContent = a.pressure !== undefined ? Math.round(a.pressure) : '--';

      // Aktuální temperature (teplota z entity konfigurace - hlavní teplota)
      const entityTempEl = sr.querySelector('#entityTemp');
      if (entityTempEl && this._bestMatchTemperatureEntity) {
        const entityState = this._hass.states[this._bestMatchTemperatureEntity];
        if (entityState && entityState.state !== 'unknown') {
          const entityTemp = parseFloat(entityState.state);
          if (!isNaN(entityTemp)) {
            entityTempEl.textContent = entityTemp.toFixed(1);
          }
        }
      }

      // Forecast temperature (teplota z předpovědi - z aktuální hodiny)
      const forecastTempEl = sr.querySelector('#forecastTemp');
      if (forecastTempEl) {
        const currentHourData = this._getCurrentHourForecast(a.forecast_hourly);
        if (currentHourData && currentHourData.temperature !== undefined) {
          forecastTempEl.textContent = currentHourData.temperature.toFixed(1);
        } else {
          forecastTempEl.textContent = a.temperature !== undefined ? a.temperature.toFixed(1) : '--';
        }
      }

      // Vítr (wind_speed) je v m/s
      const windEl = sr.querySelector('#wind');
      if (windEl) {
        const currentHourData = this._getCurrentHourForecast(a.forecast_hourly);
        if (currentHourData && currentHourData.wind_speed !== undefined) {
          windEl.textContent = currentHourData.wind_speed.toFixed(1);
        } else {
          windEl.textContent = a.wind_speed !== undefined ? a.wind_speed.toFixed(1) : '--';
        }
      }

      // Nárazy (wind gust)
      const windGustEl = sr.querySelector('#windGust');
      if (windGustEl) {
        const currentHourData = this._getCurrentHourForecast(a.forecast_hourly);
        if (currentHourData && currentHourData.wind_gust !== undefined) {
          windGustEl.textContent = currentHourData.wind_gust.toFixed(1);
        } else {
          windGustEl.textContent = a.wind_gust !== undefined ? a.wind_gust.toFixed(1) : '--';
        }
      }

      // Srážky (precipitation) - zobrazuj 0 místo --
      const precipEl = sr.querySelector('#precipitation');
      if (precipEl) {
        const currentHourData = this._getCurrentHourForecast(a.forecast_hourly);
        if (currentHourData && currentHourData.precipitation !== undefined) {
          precipEl.textContent = currentHourData.precipitation.toFixed(1);
        } else {
          precipEl.textContent = a.precipitation !== undefined ? a.precipitation.toFixed(1) : '0';
        }
      }

      // Směr (wind direction)
      const windDirEl = sr.querySelector('#windDir');
      if (windDirEl) {
        windDirEl.textContent = a.wind_direction_czech || '--';
      }

      const humidityEl = sr.querySelector('#humidity');
      if (humidityEl) {
        humidityEl.textContent = a.humidity !== undefined ? a.humidity : '--';
      }

      // Reference temperature from configured entity
      const refTempEl = sr.querySelector('#refTemp');
      if (refTempEl && this._bestMatchTemperatureEntity) {
        const refEntity = this._hass.states[this._bestMatchTemperatureEntity];
        if (refEntity && refEntity.state !== 'unknown') {
          const refTemp = parseFloat(refEntity.state);
          if (!isNaN(refTemp)) {
            refTempEl.textContent = refTemp.toFixed(1);
          }
        }
      }

      // Time and date are now updated via _updateSystemTime() interval
      // No need to get from JSON attributes anymore

      // Data age
      if (a.data_age_minutes !== undefined) {
        sr.querySelector('#dataAge').textContent = `Data je ${a.data_age_minutes} minut stará`;
      }

      // Stale warning
      sr.querySelector('#staleWarning').style.display = a.data_stale ? 'block' : 'none';

      // Icon - PNG z JSON
      // API vrací správnou ikonu (s d/n suffixem) - nepotřebujeme dalších úprav
      const iconEl = sr.querySelector('#icon');
      if (iconEl) {
        this._loadForecastIcon(iconEl, a.icon_code, a.condition || 'unknown', null, false);
      }

      // Weather description (Jasno, Polojasno, déšť, atd.)
      const weatherDescEl = sr.querySelector('#weatherDescription');
      if (weatherDescEl) {
        const description = this._getWeatherDescription(a.cloudiness, a.precipitation);
        weatherDescEl.textContent = description || '--';
      }

      // Sunrise and sunset times
      const sunriseEl = sr.querySelector('#sunrise');
      if (sunriseEl && a.sunrise) {
        sunriseEl.textContent = a.sunrise;
      }
      const sunsetEl = sr.querySelector('#sunset');
      if (sunsetEl && a.sunset) {
        sunsetEl.textContent = a.sunset;
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

      // Hourly forecast - Chart visualization
      const hourly = sr.querySelector('#hourly');
      if (a.forecast_hourly && Array.isArray(a.forecast_hourly)) {
        // Prepare data for chart
        const now = new Date();
        const currentTimestamp = now.getTime();
        const chartData = [];

        // Collect hourly data starting from current/next hour, limit to hourly_hours
        let hoursCollected = 0;
        for (const f of a.forecast_hourly) {
          if (hoursCollected >= this._hourlyHours) break;

          const dt = new Date(f.datetime || f.forecast_time);

          // Include current and future hours (compare timestamps, not just hours)
          if (dt.getTime() >= currentTimestamp) {
            // Normalize icon_code - remove .png if present
            let iconCode = f.icon_code || 'unknown';
            if (typeof iconCode === 'string' && iconCode.endsWith('.png')) {
              iconCode = iconCode.slice(0, -4);
            }

            const entry = {
              time: dt.toLocaleTimeString('cs-CZ', { hour: '2-digit' }),
              temperature: f.temperature !== undefined ? f.temperature : null,
              precipitation: f.precipitation !== undefined ? f.precipitation : 0,
              wind_speed: f.wind_speed !== undefined ? f.wind_speed : null,
              humidity: f.humidity !== undefined ? f.humidity : null,
              icon_code: iconCode,
              condition: f.condition || 'unknown',
              datetime: dt
            };
            chartData.push(entry);
            if (hoursCollected < 3) {
              console.log(`📊 Chart entry ${hoursCollected}: time=${entry.time}, temp=${entry.temperature}, precip=${entry.precipitation}, icon=${entry.icon_code}`);
            }
            hoursCollected++;
          }
        }

        // Render chart
        this._renderHourlyChart(hourly, chartData);
      }

      // Daily forecast
      const daily = sr.querySelector('#daily');
      if (a.forecast_daily && Array.isArray(a.forecast_daily)) {
        daily.innerHTML = '';
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

        a.forecast_daily.forEach((f, idx) => {
          const div = document.createElement('div');
          div.className = 'daily-item';

          const dt = new Date(f.datetime || f.forecast_time);
          const forecastDate = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
          const day = dt.toLocaleDateString('cs-CZ', { weekday: 'short' });
          const max = f.temperature !== undefined ? Math.round(f.temperature) : '--';
          const min = f.templow !== undefined ? Math.round(f.templow) : '--';
          const rain = f.precipitation !== undefined ? f.precipitation : 0;
          const rainIcon = this._getPrecipitationIcon(f.condition || 'rainy');
          const rainDisplay = rain > 0 ? `${rainIcon} ${rain}mm` : '';
          const wind = this._formatWindInfo(f.wind_speed_max, f.wind_gust_max);

          div.innerHTML = `
            <div class="daily-day">${day}</div>
            <div class="daily-icon" id="daily-icon-${idx}">📌</div>
            <div class="daily-temps">
              <span class="daily-temp-max">${max}</span> / <span class="daily-temp-min">${min}°C</span>
            </div>
            <div class="daily-wind">${wind} m/s</div>
            ${rainDisplay ? `<div class="daily-rain">${rainDisplay}</div>` : ''}
          `;

          daily.appendChild(div);

          // Skryj data ze starých dní (včera a dnes pokud je už odpoledne)
          if (forecastDate < today) {
            div.style.display = 'none';
          } else {
            div.style.display = '';
          }

          // Load icon - předej icon_code z předpovědi (isDaily=true pro denní předpověď)
          this._loadForecastIcon(div.querySelector(`#daily-icon-${idx}`), f.icon_code, f.condition || 'unknown', f.datetime || f.forecast_time, true);
        });
      }
    }

    _loadForecastIcon(iconEl, iconCode, condition, datetime, isDaily = false) {
      if (!iconEl) return;

      // Normalize icon_code - remove .png if present
      if (typeof iconCode === 'string' && iconCode.endsWith('.png')) {
        iconCode = iconCode.slice(0, -4);
      }

      // Použij nové mapování ikon z JSON
      let iconFileName = this._getWeatherIconFileName(iconCode);

      // Pokud se nepodařilo mapování, zkus podle condition
      if (iconFileName === 'otaznik.png' && condition) {
        const conditionToIcon = {
          'sunny': 'clear_day',
          'partlycloudy': 'partly_cloudy_day',
          'cloudy': 'cloudy',
          'rainy': 'rain',
          'snowy': 'snow',
          'lightning-rainy': 'zatazeno_bourka',
          'fog': 'mlha',
          'unknown': 'otaznik'
        };
        const conditionIconName = conditionToIcon[condition];
        if (conditionIconName) {
          iconFileName = this._getWeatherIconFileName(conditionIconName);
        }
      }

      const img = document.createElement('img');
      img.src = `/local/icons/${iconFileName}`;
      img.alt = condition || 'weather';

      // Fallback na emoji ikony pokud se obrázek nenačte
      img.onerror = () => {
        iconEl.innerHTML = this._getEmojiIcon(iconCode, condition);
      };

      iconEl.innerHTML = '';
      iconEl.appendChild(img);

      // Aplikuj scale na ikony v předpovědi
      if (this._scale !== 1.0) {
        iconEl.style.transform = `scale(${this._scale})`;
        iconEl.style.transformOrigin = 'center';
      }
    }

    _getEmojiIcon(iconCode, condition) {
      // Mapa emoji ikon na základě icon code nebo condition
      const emojiMap = {
        'a01d': '☀️', 'a01n': '🌙',      // Slunečno / Noční
        'a02d': '⛅', 'a02n': '☁️',      // Částečně zataženo
        'a03d': '☁️', 'a03n': '☁️',      // Zataženo
        'a04d': '☁️', 'a04n': '☁️',      // Nejasno
        'a10': '🌧️',                      // Déšť
        'a11': '⛈️',                      // Bouřka
        'a13': '❄️',                      // Sníh
        'a50': '🌫️',                      // Mlha
      };

      // Pokus se najít emoji podle icon code
      if (emojiMap[iconCode]) {
        return emojiMap[iconCode];
      }

      // Fallback podle condition
      const conditionEmojiMap = {
        'sunny': '☀️',
        'partlycloudy': '⛅',
        'cloudy': '☁️',
        'rainy': '🌧️',
        'snowy': '❄️',
        'lightning-rainy': '⛈️',
        'fog': '🌫️',
      };

      return conditionEmojiMap[condition] || '🌡️';
    }

    _getWeatherIconFileName(code) {
      // Základní validace vstupu
      if (!code || typeof code !== 'string' || code === 'null') {
        return 'otaznik.png';
      }

      // Normalizace - odstranit .png pokud je přítomno
      let normalizedCode = code.endsWith('.png') ? code.slice(0, -4) : code;
      normalizedCode = normalizedCode.toLowerCase();

      // === MAPOVÁNÍ API KÓDŮ NA PNG IKONY ===
      // Defaultní logika: kód "01" → "a01.png", "46" → "a46.png", atd.

      // Defaultní mapování: přidej 'a' na začátek a '.png' na konec
      if (/^\d+[dn]?$/.test(normalizedCode)) {
        return 'a' + normalizedCode + '.png';
      }

      // === MAPOVÁNÍ SPECIFICKÝCH TEXTOVÝCH NÁZVŮ ===
      const specificIconMappings = {
        'polojasno-destova-prehanka': 'polojasno-destova-prehanka.png',
        'polojasno-snezeni': 'polojasno-snezeni.png',
        'mlha-dest': 'mlha-dest.png',
        'mlha-snih': 'mlha-snih.png',
        'mlha-snezeni': 'mlha-snih.png', // ALADIN: alias pro sníh s mlhou
        'skoro_zatazeno_dest_1': 'skoro_zatazeno_dest_1.png',
        'skoro_zatazeno_dest_2': 'skoro_zatazeno_dest_2.png',
        'skoro_zatazeno_dest_se_snehem': 'skoro_zatazeno_dest_se_snehem.png',
        'skoro_zatazeno_snezeni_1': 'skoro_zatazeno_snezeni_1.png',
        'skoro_zatazeno_snezeni_2': 'skoro_zatazeno_snezeni_2.png',
        'skoro_zatazeno_bourka_d': 'skoro_zatazeno_bourka_d.png',
        'skoro_zatazeno_bourka_n': 'skoro_zatazeno_bourka_n.png',
        'oblacno_bourka_d': 'oblacno_bourka_d.png',
        'oblacno_bourka_n': 'oblacno_bourka_n.png',
        'zatazeno_bourka': 'zatazeno_bourka.png',
        'clear_day': 'clear_day.png',
        'clear_night': 'clear_night.png',
        'partly_cloudy_day': 'partly_cloudy_day.png',
        'partly_cloudy_night': 'partly_cloudy_night.png',
        'cloudy': 'cloudy.png',
        'rain': 'rain.png',
        'snow': 'snow.png',
        'sleet': 'sleet.png',
        'fog': 'fog.png',
        'mlha': 'mlha.png',
        'skoro_zatazeno': 'skoro_zatazeno.png'
      };

      // Zkontrolovat specifické mapování
      if (specificIconMappings[normalizedCode]) {
        return specificIconMappings[normalizedCode];
      }

      // === TEXTOVÉ NÁZVY BEZ SPECIÁLNÍHO MAPOVÁNÍ ===
      if (/^[a-z_-][a-z_0-9-]*$/.test(normalizedCode)) {
        return normalizedCode + '.png';
      }

      // Poslední fallback
      return 'otaznik.png';
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

    _getWindDirection(bearing) {
      // Převeď azimut (0-360°) na směr (N, NE, E, SE, atd.)
      if (bearing === undefined || bearing === null) return '--';

      const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
      const index = Math.round(bearing / 22.5) % 16;
      return directions[index];
    }

    _formatWindInfo(windSpeed, windGust) {
      if (windSpeed === undefined || windSpeed === null) return '--';
      const speed = typeof windSpeed === 'number' ? windSpeed.toFixed(1) : windSpeed;
      if (windGust !== undefined && windGust !== null) {
        // wind_gust je již v m/s - bez konverze
        const gust = typeof windGust === 'number' ? windGust.toFixed(1) : windGust;
        return `${speed}↗${gust}`;
      }
      return `${speed}`;
    }

    _renderHourlyChart(container, chartData) {
      if (!chartData || chartData.length === 0) {
        container.innerHTML = '<div style="padding: 20px; text-align: center; opacity: 0.6;">Žádné údaje</div>';
        return;
      }

      // Prevent excessive redraws - throttle to 500ms
      const now = Date.now();
      if (this._lastChartRender && (now - this._lastChartRender) < 500) {
        // Too soon, skip redraw
        return;
      }
      this._lastChartRender = now;

      // Clear container
      container.innerHTML = '';

      // Create wrapper - fixed height to prevent jumping
      const wrapper = document.createElement('div');
      wrapper.style.display = 'flex';
      wrapper.style.flexDirection = 'column';
      wrapper.style.width = '100%';
      wrapper.style.height = '200px'; // Fixed height - compact without legend
      wrapper.style.boxSizing = 'border-box';
      container.appendChild(wrapper);

      // Create canvas element
      const canvas = document.createElement('canvas');
      canvas.style.flex = '1';
      canvas.style.width = '100%';
      wrapper.appendChild(canvas);

      // Get canvas context
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Set fixed canvas dimensions - use container's actual size
      // Get computed style to get stable width
      const computedStyle = window.getComputedStyle(container);
      const containerWidth = parseFloat(computedStyle.width);
      const dpr = window.devicePixelRatio || 1;

      // Fixed dimensions: 200px total height (no legend)
      const w = containerWidth || 400; // Fallback to 400px
      const h = 200; // Fixed chart height (full wrapper height)

      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.scale(dpr, dpr);

      // Compute margins and chart area
      const margin = { top: 15, right: 35, bottom: 40, left: 45 };
      const chartWidth = w - margin.left - margin.right;
      const chartHeight = h - margin.top - margin.bottom;

      // Find min/max temperatures - round to stable values to prevent jumping
      const temps = chartData.filter(d => d.temperature !== null).map(d => d.temperature);
      if (temps.length === 0) {
        container.innerHTML = '<div style="padding: 20px; text-align: center; opacity: 0.6;">Žádné údaje teploty</div>';
        return;
      }

      // Round to nearest 5°C for stable axis (no extra padding)
      const rawMin = Math.min(...temps);
      const rawMax = Math.max(...temps);
      const minTemp = Math.floor(rawMin / 5) * 5; // Round down to nearest 5
      const maxTemp = Math.ceil(rawMax / 5) * 5; // Round up to nearest 5
      const tempRange = maxTemp - minTemp;

      // Find max precipitation
      const maxPrecip = Math.max(...chartData.map(d => d.precipitation), 0.1);

      // Get computed styles - use the container element for correct theme
      const style = getComputedStyle(container);
      let textColor = style.color || '#fff';
      let accentColor = '#2196F3';
      let dividerColor = 'rgba(255, 255, 255, 0.1)';

      // Try to get from CSS variables
      const rootStyle = getComputedStyle(document.documentElement);
      const primaryColor = rootStyle.getPropertyValue('--primary-color').trim();
      if (primaryColor) accentColor = primaryColor;
      const divColor = rootStyle.getPropertyValue('--divider-color').trim();
      if (divColor) dividerColor = divColor;

      // Convert CSS color to RGB (simple version)
      const getRGBColor = (cssColor) => {
        if (cssColor.startsWith('#')) {
          const hex = cssColor.replace('#', '');
          return `rgb(${parseInt(hex.substr(0, 2), 16)}, ${parseInt(hex.substr(2, 2), 16)}, ${parseInt(hex.substr(4, 2), 16)})`;
        }
        return cssColor;
      };

      ctx.fillStyle = getRGBColor(textColor);
      ctx.strokeStyle = getRGBColor(dividerColor);
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'center';

      // Note: Y-axis labels and precipitation label are drawn in Promise.all() callback
      // This prevents them from showing during initial chart draw (black text issue)

      // Calculate positions for data points
      const xSpacing = chartWidth / Math.max(chartData.length - 1, 1);
      const getX = (idx) => margin.left + idx * xSpacing;
      const getY = (temp) => margin.top + chartHeight - ((temp - minTemp) / tempRange) * chartHeight;
      const getYPrecip = (precip) => margin.top + chartHeight - (precip / maxPrecip) * (chartHeight * 0.4);

      // Draw precipitation bars (semi-transparent)
      chartData.forEach((d, idx) => {
        if (d.precipitation > 0) {
          const x = getX(idx);
          const yBottom = margin.top + chartHeight;
          const yTop = getYPrecip(d.precipitation);
          ctx.fillStyle = 'rgba(33, 150, 243, 0.25)';
          ctx.fillRect(x - 4, yTop, 8, yBottom - yTop);
        }
      });

      // Draw temperature line
      ctx.strokeStyle = getRGBColor(accentColor);
      ctx.lineWidth = 2;
      ctx.beginPath();
      let first = true;
      chartData.forEach((d, idx) => {
        if (d.temperature !== null) {
          const x = getX(idx);
          const y = getY(d.temperature);
          if (first) {
            ctx.moveTo(x, y);
            first = false;
          } else {
            ctx.lineTo(x, y);
          }
        }
      });
      ctx.stroke();

      // Calculate icon density step
      let iconStep = 1;
      if (chartData.length > 36) {
        iconStep = Math.ceil(chartData.length / 8); // Show ~8 icons max
      } else if (chartData.length > 24) {
        iconStep = Math.ceil(chartData.length / 10); // Show ~10 icons
      } else if (chartData.length > 12) {
        iconStep = Math.ceil(chartData.length / 12); // Show ~12 icons
      }

      // Preload icons for display - use cache to prevent flickering
      const iconSize = 20; // Size of weather icons
      const iconsToDraw = [];
      const iconLoadPromises = [];

      chartData.forEach((d, idx) => {
        if (d.temperature !== null && idx % iconStep === 0) {
          const x = getX(idx);
          const y = getY(d.temperature);
          const iconFileName = this._getWeatherIconFileName(d.icon_code);
          if (idx === 0 || idx === iconStep) {
            console.log(`🎯 Chart icon ${idx}: code=${d.icon_code}, mapped=${iconFileName}`);
          }

          // Track what needs to be drawn with temperature
          iconsToDraw.push({
            idx,
            x,
            y,
            temperature: d.temperature,
            iconFileName,
            condition: d.condition,
            iconCode: d.icon_code
          });

          // Check cache first, otherwise load
          if (this._imageCache[iconFileName]) {
            // Already cached, will be drawn immediately
            iconLoadPromises.push(Promise.resolve(this._imageCache[iconFileName]));
          } else {
            // Not in cache, load it
            const iconPromise = new Promise((resolve, reject) => {
              const img = new Image();
              img.onload = () => {
                this._imageCache[iconFileName] = img; // Cache it
                console.log(`✓ Icon loaded: ${iconFileName}`);
                resolve(img);
              };
              img.onerror = () => {
                console.warn(`✗ Icon failed to load: ${iconFileName} (code: ${d.icon_code})`);
                reject(d.icon_code);
              };
              img.src = `/local/icons/${iconFileName}`;
            });
            iconLoadPromises.push(iconPromise);
          }
        }
      });

      // Draw small dots for all points first
      chartData.forEach((d, idx) => {
        if (d.temperature !== null) {
          const x = getX(idx);
          const y = getY(d.temperature);

          if (idx % iconStep !== 0) {
            // Small dots for non-icon points
            ctx.fillStyle = getRGBColor(accentColor);
            ctx.beginPath();
            ctx.arc(x, y, 2, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      });

      // Load icons and draw with images + temperature labels
      Promise.all(iconLoadPromises)
        .then((images) => {
          // All icons loaded successfully, draw them with temperature
          images.forEach((img, i) => {
            const icon = iconsToDraw[i];
            ctx.drawImage(img, icon.x - iconSize / 2, icon.y - iconSize / 2, iconSize, iconSize);

            // Draw temperature above icon
            ctx.font = 'bold 10px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            ctx.fillStyle = getRGBColor(accentColor);
            ctx.fillText(Math.round(icon.temperature), icon.x, icon.y - iconSize / 2 - 2);
          });

          // Draw Y-axis labels and gridlines
          ctx.textAlign = 'right';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = getRGBColor(textColor);
          const tempSteps = 5;
          for (let i = 0; i <= tempSteps; i++) {
            const temp = minTemp + (tempRange / tempSteps) * i;
            const y = margin.top + chartHeight - (chartHeight / tempSteps) * i;
            ctx.fillText(Math.round(temp) + '°', margin.left - 10, y);

            // Draw subtle gridlines (only for middle steps)
            if (i > 0 && i < tempSteps) {
              ctx.beginPath();
              ctx.moveTo(margin.left + 5, y);
              ctx.lineTo(w - margin.right - 5, y);
              ctx.strokeStyle = getRGBColor(dividerColor);
              ctx.lineWidth = 0.3;
              ctx.stroke();
            }
          }

          // Note: precipitation label "mm" removed to save space

          // Draw precipitation values on right side (max 2 values to avoid overlapping)
          const precipSteps = 2;
          const precipStep = maxPrecip / precipSteps;
          for (let i = 1; i <= precipSteps; i++) {
            const precip = precipStep * i;
            const y = margin.top + chartHeight - (precip / maxPrecip) * (chartHeight * 0.4);
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.font = '7px sans-serif';
            ctx.fillStyle = 'rgba(33, 150, 243, 0.8)';
            ctx.fillText(precip.toFixed(1), w - margin.right + 3, y);
            console.log(`📊 Precip value: ${precip.toFixed(1)} at y=${y.toFixed(0)}`);
          }

          // Draw X-axis labels (time)
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';
          ctx.fillStyle = getRGBColor(textColor);

          // Calculate step based on available width
          let step = 1;
          if (chartData.length > 36) {
            step = Math.ceil(chartData.length / 12); // Show ~12 labels max
          } else if (chartData.length > 12) {
            step = Math.ceil(chartData.length / 8); // Show ~8 labels
          }

          chartData.forEach((d, idx) => {
            if (idx % step === 0 || idx === chartData.length - 1) {
              const x = getX(idx);
              const y = margin.top + chartHeight + 8;
              ctx.fillText(d.time, x, y);
            }
          });

          // Draw bottom line
          ctx.strokeStyle = getRGBColor(dividerColor);
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(margin.left, margin.top + chartHeight);
          ctx.lineTo(w - margin.right, margin.top + chartHeight);
          ctx.stroke();
        })
        .catch((failedCode) => {
          // Some icons failed, draw fallback emoji with temperature
          console.warn(`⚠ Using emoji fallback for code: ${failedCode}`);
          iconsToDraw.forEach((icon) => {
            const emoji = this._getEmojiIcon(icon.iconCode, icon.condition);
            ctx.font = 'bold 16px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = getRGBColor(textColor);
            ctx.fillText(emoji, icon.x, icon.y);

            // Draw temperature above emoji
            ctx.font = 'bold 10px Arial';
            ctx.textBaseline = 'bottom';
            ctx.fillStyle = getRGBColor(accentColor);
            ctx.fillText(Math.round(icon.temperature), icon.x, icon.y - 12);
          });

          // Draw Y-axis labels and gridlines
          ctx.textAlign = 'right';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = getRGBColor(textColor);
          const tempSteps = 5;
          for (let i = 0; i <= tempSteps; i++) {
            const temp = minTemp + (tempRange / tempSteps) * i;
            const y = margin.top + chartHeight - (chartHeight / tempSteps) * i;
            ctx.fillText(Math.round(temp) + '°', margin.left - 10, y);

            // Draw subtle gridlines (only for middle steps)
            if (i > 0 && i < tempSteps) {
              ctx.beginPath();
              ctx.moveTo(margin.left + 5, y);
              ctx.lineTo(w - margin.right - 5, y);
              ctx.strokeStyle = getRGBColor(dividerColor);
              ctx.lineWidth = 0.3;
              ctx.stroke();
            }
          }

          // Note: precipitation label "mm" removed to save space

          // Draw precipitation values on right side (max 2 values to avoid overlapping)
          const precipSteps = 2;
          const precipStep = maxPrecip / precipSteps;
          for (let i = 1; i <= precipSteps; i++) {
            const precip = precipStep * i;
            const y = margin.top + chartHeight - (precip / maxPrecip) * (chartHeight * 0.4);
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.font = '7px sans-serif';
            ctx.fillStyle = 'rgba(33, 150, 243, 0.8)';
            ctx.fillText(precip.toFixed(1), w - margin.right + 3, y);
            console.log(`📊 Precip value: ${precip.toFixed(1)} at y=${y.toFixed(0)}`);
          }

          // Draw X-axis labels (time)
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';
          ctx.fillStyle = getRGBColor(textColor);

          // Calculate step based on available width
          let step = 1;
          if (chartData.length > 36) {
            step = Math.ceil(chartData.length / 12); // Show ~12 labels max
          } else if (chartData.length > 12) {
            step = Math.ceil(chartData.length / 8); // Show ~8 labels
          }

          chartData.forEach((d, idx) => {
            if (idx % step === 0 || idx === chartData.length - 1) {
              const x = getX(idx);
              const y = margin.top + chartHeight + 8;
              ctx.fillText(d.time, x, y);
            }
          });

          // Draw bottom line
          ctx.strokeStyle = getRGBColor(dividerColor);
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(margin.left, margin.top + chartHeight);
          ctx.lineTo(w - margin.right, margin.top + chartHeight);
          ctx.stroke();
        });

      // Create tooltip element
      const tooltip = document.createElement('div');
      tooltip.className = 'hourly-forecast-tooltip';
      wrapper.appendChild(tooltip);

      // Add interactivity
      const handleMouseMove = (e) => {
        const rect = wrapper.getBoundingClientRect();
        // Account for scale transform - when scaled, coordinates need to be adjusted
        const scale = this._scale || 1.0;
        const x = (e.clientX - rect.left) / scale;
        const y = (e.clientY - rect.top) / scale;
        console.log(`🖱 Mouse move - x=${x.toFixed(0)}, y=${y.toFixed(0)}, scale=${scale}, margin.left=${margin.left}, margin.right=${margin.right}, w=${w}, check: ${x >= margin.left && x <= w - margin.right}`);

        // Only react to movement within chart area (left to right margin)
        if (x < margin.left || x > w - margin.right) {
          console.log(`❌ Out of bounds - hiding tooltip`);
          tooltip.style.display = 'none';
          return;
        }

        // Find closest data point
        let closest = { idx: 0, distance: Infinity };
        chartData.forEach((d, idx) => {
          const px = getX(idx);
          const dist = Math.abs(px - x);
          if (dist < closest.distance) {
            closest = { idx, distance: dist };
          }
        });

        console.log(`📍 Closest point: idx=${closest.idx}, distance=${closest.distance.toFixed(1)}, mouse x=${x.toFixed(0)}, point px=${getX(closest.idx).toFixed(0)}`);

        if (closest.distance < 30) {
          const d = chartData[closest.idx];
          const wind = d.wind_speed !== null && d.wind_speed !== undefined ? `${d.wind_speed.toFixed(1)} m/s` : '--';
          const precip = d.precipitation !== null && d.precipitation !== undefined ? `${d.precipitation.toFixed(1)} mm` : '--';
          console.log(`🎯 Tooltip data - idx: ${closest.idx}, time: ${d.time}, temp: ${d.temperature}, precip: ${d.precipitation}, displayed: ${precip}`);

          // Format time: "dnes 21", "zítra 04", etc.
          const now = new Date();
          const forecastDate = new Date(d.datetime);
          const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
          const tomorrow = new Date(today.getTime() + 86400000);
          const forecastDateOnly = new Date(forecastDate.getFullYear(), forecastDate.getMonth(), forecastDate.getDate());

          let dayLabel = '';
          if (forecastDateOnly.getTime() === today.getTime()) {
            dayLabel = 'dnes';
          } else if (forecastDateOnly.getTime() === tomorrow.getTime()) {
            dayLabel = 'zítra';
          } else {
            dayLabel = forecastDateOnly.toLocaleDateString('cs-CZ', { weekday: 'short' });
          }

          const hour = String(forecastDate.getHours()).padStart(2, '0');
          const timeStr = `${dayLabel} ${hour}`;

          // Get PNG icon
          const iconFileName = this._getWeatherIconFileName(d.icon_code);
          console.log(`🎨 Tooltip icon: code=${d.icon_code}, fileName=${iconFileName}, cached=${!!this._imageCache[iconFileName]}`);
          const iconImg = this._imageCache[iconFileName] ?
            `<img src="/local/icons/${iconFileName}" style="width: 18px; height: 18px; margin-bottom: 2px; display: block; margin-left: auto; margin-right: auto;" alt="weather">` :
            `<div style="font-size: 20px; margin-bottom: 2px;">${this._getEmojiIcon(d.icon_code, d.condition)}</div>`;

          tooltip.innerHTML = `
            <div style="font-size: 9px; font-weight: 600; margin-bottom: 3px;">${timeStr}</div>
            ${iconImg}
            <div style="font-size: 12px; font-weight: 600; margin-bottom: 2px;">${Math.round(d.temperature)}°</div>
            <div style="font-size: 8px; opacity: 0.85; line-height: 1.1;">V: ${wind}<br/>S: ${precip}</div>
          `;
          tooltip.style.display = 'block';

          // Position tooltip above the data point (not cursor)
          const tooltipWidth = 75; // Zmenšeno z 90
          const pointX = getX(closest.idx); // Use point position, not cursor
          let left = pointX - tooltipWidth / 2;
          let top = margin.top - 10; // Position above chart area

          // Keep in bounds
          if (left < 0) left = 4;
          if (left + tooltipWidth > w) left = w - tooltipWidth - 4;

          tooltip.style.left = left + 'px';
          tooltip.style.top = top + 'px';
          console.log(`📍 Tooltip positioned: left=${left.toFixed(0)}, top=${top.toFixed(0)}, pointX=${pointX.toFixed(0)}`);
        } else {
          tooltip.style.display = 'none';
        }
      };

      const handleMouseLeave = () => {
        // Hide tooltip with delay so it's visible a bit longer
        if (this._tooltipHideTimeout) {
          clearTimeout(this._tooltipHideTimeout);
        }
        this._tooltipHideTimeout = setTimeout(() => {
          tooltip.style.display = 'none';
        }, 800); // Keep tooltip visible for 800ms after mouse leaves
      };

      // Add listeners to wrapper to catch movement on entire area including right side
      wrapper.addEventListener('mousemove', handleMouseMove);
      wrapper.addEventListener('mouseleave', handleMouseLeave);
    }

    _isCurrentlyAfterSunset(sunsetTimeStr) {
      // Porovná aktuální čas se západem slunce (formát "HH:MM")
      // Vrací TRUE když je DEN (PŘED západem) - vrací FALSE když je NOČ (PO západu)
      if (!sunsetTimeStr || typeof sunsetTimeStr !== 'string') return true; // Default: den

      const now = new Date();
      const [sunsetHours, sunsetMinutes] = sunsetTimeStr.split(':').map(Number);

      const sunsetTime = new Date(now.getFullYear(), now.getMonth(), now.getDate(), sunsetHours, sunsetMinutes);

      // Vrátí true když je PŘED západem (je den)
      return now < sunsetTime;
    }

    _getIconCodeWithNightAdjustment(iconCode, isNight) {
      // Pokud je noc a ikona je denní, změní 'd' na 'n'
      if (isNight && iconCode && iconCode.endsWith('d')) {
        return iconCode.replace(/d$/, 'n');
      }
      return iconCode;
    }

    async _loadTodayHoliday() {
      // Načti svátek na dnes z API - cache na 24 hodin
      const today = new Date();
      const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`; // YYYY-MM-DD
      const todayKey = dateStr;

      // Pokud jsme už dneska fetchli, použij cache
      if (this._holidayFetchDate === todayKey && this._todayHoliday !== undefined) {
        return this._todayHoliday;
      }

      try {
        // Použij správný endpoint s datem: https://svatkyapi.cz/api/day?date=2025-11-21
        const response = await fetch(`https://svatkyapi.cz/api/day?date=${dateStr}`);

        if (!response.ok) {
          console.warn('Failed to fetch holiday data:', response.status);
          this._todayHoliday = '---';
          this._holidayFetchDate = todayKey;
          return '---';
        }

        const data = await response.json();

        // Vytáhni jméno z response
        // Response má strukturu: { "name": "Albert", "isHoliday": false, ... }
        if (data && data.name) {
          this._todayHoliday = data.name;
        } else {
          this._todayHoliday = '---';
        }

        this._holidayFetchDate = todayKey;
        console.log('Holiday loaded:', this._todayHoliday);
        return this._todayHoliday;
      } catch (error) {
        console.warn('Error loading holiday:', error);
        this._todayHoliday = '---';
        this._holidayFetchDate = todayKey;
        return '---';
      }
    }

    static getStubConfig() {
      return {
        type: 'custom:pocasimeteo-card',
        entity: 'weather.pocasimeteo_praha_6_ruzyne',
        // Volitelné: entita teploty pro automatickou detekci nejpřesnějšího modelu
        best_match_temperature_entity: 'sensor.outdoor_temperature',
        // Volitelné: seznam modelů k zobrazení
        models: [
          { name: 'MASTER', label: 'Master' },
          { name: 'ALADIN', label: 'ALADIN' },
          { name: 'ICON', label: 'ICON' },
          { name: 'GFS', label: 'GFS' },
          { name: 'ECMWF', label: 'ECMWF' }
        ],
        // Konfigurační možnosti:
        full_width: false,                      // true = karta přes celou šířku
        show_current_weather: true,             // Zobrazit aktuální počasí
        show_hourly_forecast: true,             // Zobrazit hodinovou předpověď
        show_daily_forecast: true               // Zobrazit denní předpověď
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
