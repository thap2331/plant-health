PYTHON := $(shell which python3)
SCRIPT := $(shell realpath water_plant.py)
LOG_DIR := $(HOME)/logs/plant-water/water
CRON_JOB := 0 * * * * mkdir -p $(LOG_DIR) && $(PYTHON) $(SCRIPT) >> $(LOG_DIR)/water_plant.log 2>&1

.PHONY: schedule-water-plant unschedule-water-plant

schedule-water-plant:
	(crontab -l 2>/dev/null | grep -v "$(SCRIPT)"; echo "$(CRON_JOB)") | crontab -
	@echo "Cron job installed: runs every hour"

unschedule-water-plant:
	crontab -l 2>/dev/null | grep -v "$(SCRIPT)" | crontab -
	@echo "Cron job removed"
