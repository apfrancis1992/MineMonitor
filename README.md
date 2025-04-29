# MineMonitor for Home Assistant

This Home Assistant integration allows you to monitor Bitcoin mining statistics from a Public Pool Mining server API.

## Features

- Monitor multiple Bitcoin addresses
- Track individual worker statistics
- View network information
- Monitor hash rates, difficulties, and more
- Automatically updates at configurable intervals

## Installation

### Using HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance
2. In HACS, click on "Integrations"
3. Click the "..." menu in the top right corner
4. Select "Custom repositories"
5. Add the URL of this repository: `https://github.com/your_github_username/bitcoin_mining`
6. Select "Integration" as the category
7. Click "ADD"
8. Search for "Bitcoin Mining Monitor" in the integrations tab
9. Click "Install"
10. Restart Home Assistant

### Manual Installation

1. Download the source code from this repository
2. Copy the `custom_components/minemonitor` directory to your `<config>/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to Home Assistant Configuration → Integrations
2. Click the "+ ADD INTEGRATION" button
3. Search for "MineMonitor"
4. Fill in the required information:
   - **Host**: IP address of your mining server
   - **Port**: Port number (default: 3334)
   - **Bitcoin Addresses**: One or more Bitcoin addresses to monitor (comma-separated)
   - **Update Interval**: How often to poll for new data (in seconds)
5. Click "Submit"

## Available Sensors

For each Bitcoin address, the integration provides:

- **Best Difficulty**: The best difficulty achieved by this BTC address
- **Workers Count**: The number of active workers

For each worker:

- **Best Difficulty**: The best difficulty achieved by this worker
- **Hash Rate**: The hash rate in hashes per second (H/s)

Network sensors:

- **Blocks**: Current blockchain height
- **Network Difficulty**: Current Bitcoin network difficulty
- **Network Hash Rate**: Total network hash rate (H/s)
- **Pooled Transactions**: Number of transactions in the mempool

Info sensors:

- **All-time Best Difficulty**: The highest difficulty ever achieved

## Screenshots

[Add screenshots here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
