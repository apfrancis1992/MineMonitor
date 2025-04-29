# MineMonitor - Troubleshooting Guide

This guide helps you diagnose and fix common issues with the MineMonitor integration.

## Common Issues and Solutions

### Integration Not Found in HACS

**Symptoms**: The MineMonitor integration doesn't appear in HACS after adding the repository.

**Solutions**:
1. Make sure you added the repository as an "Integration" type, not "Plugin" or "Theme"
2. Check that the repository URL is correct
3. Try refreshing HACS (Settings → HACS → 3-dot menu → "Reload data")
4. Restart Home Assistant

### Cannot Connect to Mining Server

**Symptoms**: During setup, you get the error "Failed to connect to the mining server".

**Solutions**:
1. Verify the IP address and port are correct
2. Check that the mining server is running and accessible from Home Assistant
3. Ensure no firewall is blocking the connection
4. Try accessing the API endpoints directly in your browser:
   - `http://[IP]:[PORT]/api/info`
   - `http://[IP]:[PORT]/api/network`
5. Increase the timeout in your setup by editing the integration code:
   - Open `custom_components/bitcoin_mining/config_flow.py`
   - Find `timeout=10` and change it to a higher value like `timeout=30`

### Invalid Bitcoin Address

**Symptoms**: During setup, you get the error "One or more Bitcoin addresses are invalid".

**Solutions**:
1. Check that the Bitcoin addresses are entered correctly with no extra spaces
2. Make sure the addresses follow the correct format (starting with 1, 3, or bc1)
3. If using multiple addresses, ensure they're properly comma-separated
4. Verify that the addresses exist and are accessible through the mining server API
5. Try adding addresses one at a time to identify which one is causing the issue

### No Sensors Created

**Symptoms**: After setup, no sensors appear in Home Assistant.

**Solutions**:
1. Check the Home Assistant logs for any errors
2. Verify that the Bitcoin addresses are correctly configured
3. Make sure the mining server is returning valid data for those addresses
4. Restart Home Assistant
5. Try removing and re-adding the integration

### Missing Worker Data

**Symptoms**: Worker-specific sensors don't appear even though the worker is active.

**Solutions**:
1. Check if the worker is properly connected to the mining server
2. Verify that the worker data appears in the API response when accessing directly
3. Ensure the worker has been active recently (within the last scan interval)
4. Try restarting the integration using the service `minemonitor.refresh_data`

### Inaccurate Hash Rate Values

**Symptoms**: Hash rate values seem incorrect or are showing in scientific notation.

**Solutions**:
1. The API returns values in hashes per second (H/s), which can be very large numbers
2. Check if your mining software reports in different units (MH/s, GH/s, TH/s)
3. Use a value template in Lovelace to format the units appropriately:
   ```yaml
   value_template: "{{ (states('sensor.your_hashrate_sensor') | float / 1000000000) | round(2) }} GH/s"
   ```

### Custom Cards Not Loading

**Symptoms**: The custom cards don't appear in the dashboard or show errors.

**Solutions**:
1. Verify that the card files are correctly installed
2. Check that the resources are added to your Lovelace configuration
3. Look for JavaScript errors in your browser console (F12 → Console)
4. Ensure entity IDs in the card configuration match your actual entities
5. Try using the "Card Preview" feature in the dashboard editor to test the configuration

### Integration Stops Updating

**Symptoms**: Sensors stop refreshing after some time.

**Solutions**:
1. Check if the mining server is still accessible
2. Look for any network issues between Home Assistant and the mining server
3. Verify that the scan interval is appropriate (not too short or too long)
4. Check Home Assistant logs for timeout errors or other issues
5. Create an automation to periodically refresh the data:
   ```yaml
   automation:
     - alias: Refresh Mining Data
       trigger:
         platform: time_pattern
         hours: "/1"
       action:
         service: minemonitor.refresh_data
   ```

### API Format Changes

**Symptoms**: The integration stops working after a mining server update.

**Solutions**:
1. Check if the API response format has changed
2. Compare the current responses with the examples in the documentation
3. Update the integration code to handle the new format
4. Open an issue on GitHub to report the change

## Debugging

### Enabling Debug Logging

Add the following to your `configuration.yaml` to enable debug logs:

```yaml
logger:
  default: info
  logs:
    custom_components.minemonitor: debug
```

Restart Home Assistant and check the logs for detailed information.

### Testing API Endpoints

Use cURL or a tool like Postman to test the API endpoints directly:

```bash
# Test info endpoint
curl http://YOUR_SERVER_IP:PORT/api/info

# Test network endpoint
curl http://YOUR_SERVER_IP:PORT/api/network

# Test client endpoint for a specific address
curl http://YOUR_SERVER_IP:PORT/api/client/YOUR_BTC_ADDRESS
```

### Checking Entity States

Use the Developer Tools → States in Home Assistant to check your entity states:

1. Filter for `bitcoin` to see all related entities
2. Check the state and attributes of each entity
3. Verify that the values match what you expect

## Getting Help

If you're still experiencing issues:

1. Check the GitHub repository for existing issues
2. Open a new issue with:
   - A detailed description of the problem
   - Steps to reproduce
   - Home Assistant logs
   - Screenshots or examples of API responses
3. Join the Home Assistant community forums and ask for help