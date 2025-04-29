class MineMonitorWorkerCard extends HTMLElement {
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
    if (!config.worker_entity) {
      throw new Error('You need to define a worker_entity');
    }
    if (!config.hashrate_entity) {
      throw new Error('You need to define a hashrate_entity');
    }
    if (!config.difficulty_entity) {
      throw new Error('You need to define a difficulty_entity');
    }
    this._config = config;
    this._updateContent();
  }

  // Card size
  getCardSize() {
    return 3;
  }

  // Calculate human-readable hash rate
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

  // Format time since last seen
  _formatTimeSince(lastSeenStr) {
    if (!lastSeenStr) return 'Unknown';
    
    const lastSeen = new Date(lastSeenStr);
    const now = new Date();
    const diffMs = now - lastSeen;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  }

  // Get worker status class
  _getStatusClass(lastSeenStr) {
    if (!lastSeenStr) return 'status-unknown';
    
    const lastSeen = new Date(lastSeenStr);
    const now = new Date();
    const diffMs = now - lastSeen;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 10) return 'status-active';
    if (diffMins < 30) return 'status-warning';
    return 'status-offline';
  }

  // Update card content
  _updateContent() {
    if (!this._hass || !this._config) {
      return;
    }

    const workerEntity = this._config.worker_entity;
    const hashrateEntity = this._config.hashrate_entity;
    const difficultyEntity = this._config.difficulty_entity;
    
    const workerState = this._hass.states[workerEntity];
    const hashrateState = this._hass.states[hashrateEntity];
    const difficultyState = this._hass.states[difficultyEntity];
    
    if (!workerState || !hashrateState || !difficultyState) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="card-content">
            <div class="not-found">Worker entities not found</div>
          </div>
        </ha-card>
      `;
      return;
    }
    
    // Get worker data
    const workerName = this._config.title || workerState.attributes.worker_name || 'Worker';
    const hashrate = this._formatHashRate(hashrateState.state);
    const difficulty = parseFloat(difficultyState.state).toLocaleString();
    const lastSeen = workerState.attributes.last_seen;
    const timeSince = this._formatTimeSince(lastSeen);
    const statusClass = this._getStatusClass(lastSeen);
    
    // Calculate percentage of hashrate compared to max value
    const maxHashrate = this._config.max_hashrate || 1000000000000; // 1 TH/s default
    const hashratePercent = Math.min(100, (parseFloat(hashrateState.state) / maxHashrate) * 100);
    
    this.shadowRoot.innerHTML = `
      <ha-card>
        <style>
          .card-header {
            padding: 16px 16px 0;
            display: flex;
            justify-content: space-between;
          }
          .worker-name {
            font-size: 1.2em;
            font-weight: 500;
          }
          .status-indicator {
            display: flex;
            align-items: center;
          }
          .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
          }
          .status-active {
            background-color: var(--success-color, #4CAF50);
          }
          .status-warning {
            background-color: var(--warning-color, #FF9800);
          }
          .status-offline {
            background-color: var(--error-color, #F44336);
          }
          .status-unknown {
            background-color: var(--disabled-color, #9E9E9E);
          }
          .card-content {
            padding: 16px;
          }
          .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-gap: 16px;
          }
          .stat-item {
            margin-bottom: 8px;
          }
          .stat-label {
            font-size: 0.9em;
            color: var(--secondary-text-color);
          }
          .stat-value {
            font-size: 1.4em;
            font-weight: 500;
          }
          .hashrate-bar {
            width: 100%;
            height: 6px;
            background-color: var(--disabled-color, #9E9E9E);
            border-radius: 3px;
            margin-top: 16px;
            overflow: hidden;
          }
          .hashrate-fill {
            height: 100%;
            background-color: var(--primary-color);
            width: ${hashratePercent}%;
            transition: width 0.5s ease-in-out;
          }
          .last-seen {
            font-size: 0.8em;
            color: var(--secondary-text-color);
            margin-top: 16px;
            text-align: right;
          }
        </style>
        
        <div class="card-header">
          <div class="worker-name">${workerName}</div>
          <div class="status-indicator">
            <div class="status-dot ${statusClass}"></div>
            <div>${statusClass === 'status-active' ? 'Online' : statusClass === 'status-warning' ? 'Warning' : 'Offline'}</div>
          </div>
        </div>
        
        <div class="card-content">
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-label">Hash Rate</div>
              <div class="stat-value">${hashrate}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Best Difficulty</div>
              <div class="stat-value">${difficulty}</div>
            </div>
          </div>
          
          <div class="hashrate-bar">
            <div class="hashrate-fill"></div>
          </div>
          
          <div class="last-seen">Last seen: ${timeSince}</div>
        </div>
      </ha-card>
    `;
  }
}

customElements.define('minemonitor-worker-card', MineMonitorWorkerCard);

// Add card type to card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'minemonitor-worker-card',
  name: 'MineMonitor Worker Card',
  description: 'A card showing mining worker status'
});
