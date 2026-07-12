class IpawsMonitorCard extends HTMLElement {
  set hass(hass) {
    const entityId = this.config.entity || 'sensor.ipaws_emergency_alert';
    const state = hass.states[entityId];
    
    if (!state) {
      this.innerHTML = `<ha-card style="color: red; padding: 16px;">Entity not found: ${entityId}</ha-card>`;
      return;
    }

    const alertText = state.state;
    const isAlertActive = alertText !== "No alerts at this time";

    // Only update the DOM if things actually changed to save performance
    if (!this.content) {
      this.innerHTML = `
        <ha-card>
          <div id="eas-container">
            <div id="warning-bar">📺 EAS RELAY STATUS</div>
            <div id="alert-content"></div>
          </div>
        </ha-card>
        <style>
          #eas-container {
            background-color: #000000 !important;
            color: #ffffff !important;
            font-family: 'Courier New', Courier, monospace !important;
            text-transform: uppercase;
            font-size: 1.1em;
            line-height: 1.6;
            border: 3px solid #333;
            padding: 15px;
            border-radius: var(--ha-card-border-radius, 12px);
            overflow: hidden;
          }
          #warning-bar {
            color: #ff3333;
            font-weight: bold;
            border-bottom: 2px dashed #333;
            padding-bottom: 5px;
            margin-bottom: 10px;
            text-align: center;
          }
          #alert-content {
            white-space: pre-wrap;
          }
          /* If an active warning is fetched, make the top bar flash */
          .active-warning #warning-bar {
            background-color: #cc0000;
            color: white;
            animation: eas-blink 1.5s steps(2, start) infinite;
            padding: 2px;
          }
          @keyframes eas-blink {
            to { visibility: hidden; }
          }
        </style>
      `;
      this.content = this.querySelector('#alert-content');
      this.container = this.querySelector('#eas-container');
    }

    if (isAlertActive) {
      this.container.classList.add('active-warning');
    } else {
      this.container.classList.remove('active-warning');
    }

    this.content.innerText = alertText;
  }

  setConfig(config) {
    this.config = config;
  }

  getCardSize() {
    return 3;
  }
}

customElements.define('ipaws-monitor-card', IpawsMonitorCard);

// Register the card to the Home Assistant Card Picker UI
window.customCards = window.customCards || [];
window.customCards.push({
  type: "ipaws-monitor-card",
  name: "FEMA IPAWS Monitor Card",
  description: "A retro style card for rendering active Emergency Alert System broadcasts.",
  preview: true
});