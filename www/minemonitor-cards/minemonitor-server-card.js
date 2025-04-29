class MineMonitorServerCard extends HTMLElement {
  // Define properties to observe
  static get properties() {
    return {
      hass: {},
      config: {}
    };
  }

  // Constructor
  constructor() {
    super();
    this._hass = null;
    this._config = null;
    this.attachShadow({ mode: 'open' });
  }

  // Set Home Assistant instance
  set hass(hass) {
    this._hass = hass;
    this._updateContent();
  }

  // Set card configuration
  setConfig(config) {
    if (!config.address) {
      throw new Error('You need to define a bitcoin address');
    }
    if (!config.workers_count_entity) {
      throw new Error('You need to define a workers_count_entity');
    }
    if (!config.best_difficulty_entity) {
      throw new Error('You need to define a best_difficulty_entity');
    }
    this._config = config;
    this._updateContent();
  }

  // Card size
  getCardSize() {
    return 5;
  }

  // Format difficulty
  _formatDifficulty(difficulty) {
    if (!difficulty) return '0';
    
    const value = parseFloat(difficulty);
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(2)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(2)}K`;
    }
    return value.toFixed(2);
  }

  // Calculate total hashrate from worker entities
  _calculateTotalHashrate() {
    if (!this._config.worker_hashrate_entities || !Array.isArray(this._config.worker_hashrate_entities)) {
      return 0;
    }

    let totalHashrate = 0;
    this._config.worker_hashrate_entities.forEach(entity => {
      const state = this._hass.states[entity];
      if (state && !isNaN(state.state)) {
        totalHashrate += parseFloat(state.state);
      }
    });
    
    return totalHashrate;
  }

  // Format hashrate
  _formatHashRate(hashrate) {
    if (!hashrate) return '0 H/s';
    
    const units = ['H/s', 'KH/s', 'MH/s', 'GH/s', 'TH/s', 'PH/s', 'EH/s'];
    let unitIndex = 0;
    let value = parseFloat(hashrate);
    
    while (value >= 1000 && unitIndex < units.length - 1) {
      value /= 1000;
      unitIndex++;
    }
    
    return `${value.toFixed(2)} ${units[unitIndex]}`;
  }

  // Get worker status data
  _getWorkerStatusData() {
    if (!this._config.worker_hashrate_entities || !Array.isArray(this._config.worker_hashrate_entities)) {
      return { online: 0, warning: 0, offline: 0 };
    }

    let statusData = { online: 0, warning: 0, offline: 0 };
    
    this._config.worker_hashrate_entities.forEach(entity => {
      const state = this._hass.states[entity];
      if (!state) return;
      
      // Check if the worker has a last_seen attribute
      if (state.attributes.last_seen) {
        const lastSeen = new Date(state.attributes.last_seen);
        const now = new Date();
        const diffMs = now - lastSeen;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 10) {
          statusData.online++;
        } else if (diffMins < 30) {
          statusData.warning++;
        } else {
          statusData.offline++;
        }
      } else if (state.state && parseFloat(state.state) > 0) {
        // If no last_seen attribute, but hashrate is positive, consider online
        statusData.online++;
      } else {
        statusData.offline++;
      }
    });
    
    return statusData;
  }

  // Update card content
  _updateContent() {
    if (!this._hass || !this._config) {
      return;
    }

    const address = this._config.address;
    const workersCountEntity = this._config.workers_count_entity;
    const bestDifficultyEntity = this._config.best_difficulty_entity;
    
    const workersCountState = this._hass.states[workersCountEntity];
    const bestDifficultyState = this._hass.states[bestDifficultyEntity];
    
    if (!workersCountState || !bestDifficultyState) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="card-content">
            <div class="not-found">Server entities not found</div>
          </div>
        </ha-card>
      `;
      return;
    }
    
    // Get server data
    const title = this._config.title || `Mining Address: ${address}`;
    const workersCount = workersCountState.state;
    const bestDifficulty = this._formatDifficulty(bestDifficultyState.state);
    const totalHashrate = this._calculateTotalHashrate();
    const formattedHashrate = this._formatHashRate(totalHashrate);
    
    // Get worker status
    const workerStatus = this._getWorkerStatusData();
    
    // Get network entity if provided
    let networkDifficulty = null;
    let networkBlocks = null;
    
    if (this._config.network_difficulty_entity) {
      const networkDiffState = this._hass.states[this._config.network_difficulty_entity];
      if (networkDiffState) {
        networkDifficulty = parseFloat(networkDiffState.state).toLocaleString();
      }
    }
    
    if (this._config.network_blocks_entity) {
      const networkBlocksState = this._hass.states[this._config.network_blocks_entity];
      if (networkBlocksState) {
        networkBlocks = networkBlocksState.state;
      }
    }
    
    this.shadowRoot.innerHTML = `
      <ha-card>
        <style>
          .card-header {
            padding: 16px 16px 0;
          }
          .card-title {
            font-size: 1.4em;
            font-weight: 500;
            margin-bottom: 8px;
          }
          .address {
            font-size: 0.8em;
            color: var(--secondary-text-color);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          .card-content {
            padding: 16px;
          }
          .main-stats {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            grid-gap: 16px;
            margin-bottom: 24px;
          }
          .stat-box {
            background-color: var(--card-background-color, #FFF);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
          }
          .stat-value {
            font-size: 1.8em;
            font-weight: 500;
            margin-bottom: 4px;
          }
          .stat-label {
            font-size: 0.9em;
            color: var(--secondary-text-color);
          }
          .status-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            grid-gap: 8px;
            margin-top: 16px;
          }
          .status-box {
            padding: 8px;
            border-radius: 4px;
            text-align: center;
          }
          .online {
            background-color: rgba(76, 175, 80, 0.2);
            color: var(--success-color, #4CAF50);
          }
          .warning {
            background-color: rgba(255, 152, 0, 0.2);
            color: var(--warning-color, #FF9800);
          }
          .offline {
            background-color: rgba(244, 67, 54, 0.2);
            color: var(--error-color, #F44336);
          }
          .network-info {
            margin-top: 24px;
            border-top: 1px solid var(--divider-color, #EEE);
            padding-top: 16px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-gap: 16px;
          }
          .network-box {
            padding: 8px;
            border-radius: 4px;
            background-color: rgba(0, 0, 0, 0.03);
          }
          .network-label {
            font-size: 0.8em;
            color: var(--secondary-text-color);
          }
          .network-value {
            font-size: 1.2em;
            font-weight: 500;
          }
          .not-found {
            color: var(--error-color, #F44336);
            font-style: italic;
          }
        </style>
        
        <div class="card-header">
          <div class="card-title">${title}</div>
          <div class="address">${address}</div>
        </div>
        
        <div class="card-content">
          <div class="main-stats">
            <div class="stat-box">
              <div class="stat-value">${workersCount}</div>
              <div class="stat-label">Workers</div>
            </div>
            <div class="stat-box">
              <div class="stat-value">${formattedHashrate}</div>
              <div class="stat-label">Total Hashrate</div>
            </div>
            <div class="stat-box">
              <div class="stat-value">${bestDifficulty}</div>
              <div class="stat-label">Best Difficulty</div>
            </div>
          </div>
          
          <div class="status-grid">
            <div class="status-box online">
              <div>${workerStatus.online} Online</div>
            </div>
            <div class="status-box warning">
              <div>${workerStatus.warning} Warning</div>
            </div>
            <div class="status-box offline">
              <div>${workerStatus.offline} Offline</div>
            </div>
          </div>
          
          ${(networkDifficulty || networkBlocks) ? `
          <div class="network-info">
            ${networkDifficulty ? `
            <div class="network-box">
              <div class="network-label">Network Difficulty</div>
              <div class="network-value">${networkDifficulty}</div>
            </div>
            ` : ''}
            ${networkBlocks ? `
            <div class="network-box">
              <div class="network-label">Block Height</div>
              <div class="network-value">${networkBlocks}</div>
            </div>
            ` : ''}
          </div>
          ` : ''}
        </div>
      </ha-card>
    `;
  }
}

customElements.define('minemonitor-server-card', MineMonitorServerCard);

// Add card type to card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'minemonitor-server-card',
  name: 'MineMonitor Server Card',
  description: 'A card showing mining server overview'
});
