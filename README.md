# Plant Health

Automated plant watering system using a Raspberry Pi, soil moisture sensor (via SPI/MCP3008), and a relay-controlled water pump.

## Watering

`water_plant.py` reads the soil moisture sensor and waters the plant if the soil is dry and the cooldown period has passed. It is designed to run as a one-shot script via cron.

| Setting | Value |
|---|---|
| Dry threshold | 560 |
| Watering duration | 3s |
| Cooldown | 300 minutes |

## Scheduling

Use the Makefile to manage the cron job (runs every hour):

```bash
# Install
make schedule-water-plant

# Remove
make unschedule-water-plant
```

Logs are written to `~/water_plant.log`. Moisture readings are logged to `~/moisture_log.csv`.
