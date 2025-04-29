# MineMonitor Custom Cards Installation Guide

This guide explains how to install and use the custom Lovelace cards included with the MineMonitor integration.

## Custom Cards Overview

This integration includes two custom cards for visualizing your mining data:

1. **MineMonitor Worker Card**: Displays detailed information about individual mining workers
2. **MineMonitor Server Card**: Provides an overview of your mining server with multiple workers

## Installation

### Method 1: Using HACS Frontend

1. Make sure you have HACS installed
2. Go to HACS → Frontend
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add the repository URL containing these cards
6. Select "Lovelace" as the category
7. Click "ADD"
8. Look for "MineMonitor Cards" and install them
9. Restart Home Assistant

### Method 2: Manual Installation

1. Create a directory: `www/community/minemonitor-cards/`
2. Save the card files in this directory:
   - `www/community/minemonitor-cards/minemonitor-worker-card.js`
   - `www/community/minemonitor-cards/minemonitor-server-card.js`
3. Add the resources to your Lovelace configuration by going to:
   - Settings → Dashboards → Select your dashboard
   - Click the three dots in the top right corner → Resources
   - Add each file as a JavaScript resource:
     - URL: `/local/community/minemonitor-cards/minemonitor-worker-card.js`
     - Resource type: JavaScript Module
   - Add the second card similarly
4. Restart Home Assistant

## Using the Worker Card

### Configuration Options

The Worker Card has the following configuration options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `type` | string | required | Must be `custom:minemonitor-worker-card` |
| `title` | string | Worker name | Optional custom title for the card |
| `worker_entity` | string | required | Entity ID of the worker (for name/status) |
| `hashrate_entity` | string | required | Entity ID of the hashrate sensor |
| `difficulty_entity` | string | required | Entity ID of the difficulty sensor |
| `max_hashrate` | number | 1,000,000,000,000 | Maximum hashrate for the progress bar (in H/s) |

### Example Configuration

```yaml
type: custom:minemonitor-worker-card
title: Worker 1
worker_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w1_best_difficulty
hashrate_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w1_hash_rate
difficulty_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w1_best_difficulty
max_hashrate: 500000000000
```

## Using the Server Card

### Configuration Options

The Server Card has the following configuration options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `type` | string | required | Must be `custom:minemonitor-server-card` |
| `title` | string | Mining Address | Optional custom title for the card |
| `address` | string | required | Bitcoin address being monitored |
| `workers_count_entity` | string | required | Entity ID of the workers count sensor |
| `best_difficulty_entity` | string | required | Entity ID of the best difficulty sensor |
| `worker_hashrate_entities` | array | optional | List of worker hashrate entity IDs |
| `network_difficulty_entity` | string | optional | Entity ID of network difficulty sensor |
| `network_blocks_entity` | string | optional | Entity ID of network blocks sensor |

### Example Configuration

```yaml
type: custom:minemonitor-server-card
title: Mining Server Status
address: bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn
workers_count_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_workers_count
best_difficulty_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_best_difficulty
worker_hashrate_entities:
  - sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w1_hash_rate
  - sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w2_hash_rate
network_difficulty_entity: sensor.bitcoin_network_difficulty
network_blocks_entity: sensor.bitcoin_network_blocks
```

## Advanced Dashboard Example

Here's an example of a complete dashboard using both custom cards:

```yaml
title: MineMonitor Dashboard
views:
  - title: Mining Overview
    path: mining
    cards:
      - type: custom:minemonitor-server-card
        title: Mining Overview
        address: bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn
        workers_count_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_workers_count
        best_difficulty_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_best_difficulty
        worker_hashrate_entities:
          - sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w1_hash_rate
          - sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w2_hash_rate
        network_difficulty_entity: sensor.bitcoin_network_difficulty
        network_blocks_entity: sensor.bitcoin_network_blocks
      
      - type: horizontal-stack
        cards:
          - type: custom:minemonitor-worker-card
            title: Worker 1
            worker_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w1_best_difficulty
            hashrate_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w1_hash_rate
            difficulty_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w1_best_difficulty
            max_hashrate: 500000000000
          
          - type: custom:minemonitor-worker-card
            title: Worker 2
            worker_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w2_best_difficulty
            hashrate_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w2_hash_rate
            difficulty_entity: sensor.bc1q543khxm7uygqec0qm2z4qkyfnjvm5xgpyp24yn_w2_best_difficulty
            max_hashrate: 1200000000000
```