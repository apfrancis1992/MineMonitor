# MineMonitor for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/your_github_username/minemonitor.svg)](https://github.com/your_github_username/minemonitor/releases)
[![License](https://img.shields.io/github/license/your_github_username/minemonitor.svg)](LICENSE)

A Home Assistant custom integration for monitoring Bitcoin mining statistics. This integration connects to a mining server API and provides sensors for worker status, hashrates, and network information.

![MineMonitor Dashboard](https://raw.githubusercontent.com/your_github_username/minemonitor/main/images/dashboard.png)

## Features

- Monitor multiple Bitcoin addresses
- Track individual worker statistics (hashrate, difficulty)
- View Bitcoin network information
- Monitor total hashrate and difficulty
- Custom Lovelace cards for visualizing mining data
- Services to add/remove Bitcoin addresses and refresh data
- Automatic update at configurable intervals

## Requirements

- Home Assistant (2023.3.0 or newer)
- A Bitcoin mining server with the API endpoints documented below
- One or more Bitcoin addresses to monitor

## Installation

### HACS Installation (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Click on HACS in the left sidebar
3. Click on "Integrations"
4. Click the three dots in the top right corner 
5. Select "Custom repositories"
6. Add `https://github.com/your_github_username/minemonitor` as a repository
7.
10. Click "Install"
11. Restart Home Assistant

### Manual Installation

1. Download the source code from this repository
2. Copy the `custom_components/bitcoin_mining` directory to your Home Assistant `config/custom_components` directory
3. Restart Home Assistant

## Configuration

### UI Configuration (Recommended)

1. Go to Home Assistant → Settings → Devices & Services
2. Click the "+ ADD INTEGRATION" button
3. Search for "Bitcoin Mining Monitor"
4. Enter the required information:
   - **Host**: IP address of your mining server
   - **Port**: Port number (default: 3334)
   - **Bitcoin Addresses**: Comma-separated list of BTC addresses
   - **Update Interval**: How often to poll for data (in seconds)
5. Click "Submit"

### YAML Configuration (Alternative)

Add the following to your `configuration.yaml` file:

```yaml
bitcoin_mining:
  host: YOUR_SERVER_IP
  port: 3334
  btc_addresses:
    - bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn
  scan_interval: 60
```

## Available Sensors

The integration creates sensors for:

### For each Bitcoin address:
- Best difficulty achieved
- Workers count

### For each worker:
- Best difficulty achieved by the worker
- Hash rate in H/s
- Last seen timestamp

### Network sensors:
- Current blockchain height 
- Network difficulty
- Network hash rate
- Pooled transactions

### Info sensors:
- All-time best difficulty

## Custom Cards

The repository includes two custom Lovelace cards:

- **Bitcoin Mining Worker Card**: Displays detailed information about individual mining workers
- **Bitcoin Mining Server Card**: Provides an overview of your mining server with multiple workers

See the [Custom Cards Installation Guide](docs/custom-cards.md) for details.

## Services

The integration provides several services:

### `bitcoin_mining.refresh_data`
Force an immediate update of all mining data.

### `bitcoin_mining.add_btc_address`
Add a new Bitcoin address to monitor.

### `bitcoin_mining.remove_btc_address`
Remove a Bitcoin address from monitoring.

See the [Services Documentation](docs/services.md) for details.

## API Requirements

The integration expects the following API endpoints to be available on your mining server:

- `http://[IP]:[PORT]/api/client/[BTC_ADDRESS]`: Information about a specific Bitcoin address
- `http://[IP]:[PORT]/api/network`: Bitcoin network information
- `http://[IP]:[PORT]/api/info`: General information about the mining server

## Examples

Check out the [examples directory](examples/) for:

- Example Lovelace dashboard configuration
- Example automations
- Example scripts

## Troubleshooting

See the [Troubleshooting Guide](docs/troubleshooting.md) for common issues and solutions.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
