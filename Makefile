PYTHON := $(shell which python3)

WATER_SCRIPT   := $(shell realpath water_plant.py)
WATER_LOG_DIR  := $(HOME)/logs/plant-water/water
WATER_CRON_JOB := 0 * * * * mkdir -p $(WATER_LOG_DIR) && $(PYTHON) $(WATER_SCRIPT) >> $(WATER_LOG_DIR)/water_plant.log 2>&1

IMAGE_SCRIPT   := $(shell realpath capture_image.py)
IMAGE_LOG_DIR  := $(HOME)/logs/plant-water/images
IMAGE_CRON_JOB := 0 * * * * mkdir -p $(IMAGE_LOG_DIR) && $(PYTHON) $(IMAGE_SCRIPT) 2>> $(IMAGE_LOG_DIR)/camera.log

.PHONY: schedule-water-plant unschedule-water-plant schedule-capture-image unschedule-capture-image

schedule-water-plant:
	(crontab -l 2>/dev/null | grep -v "$(WATER_SCRIPT)"; echo "$(WATER_CRON_JOB)") | crontab -
	@echo "Cron job installed: waters plant every hour"

unschedule-water-plant:
	crontab -l 2>/dev/null | grep -v "$(WATER_SCRIPT)" | crontab -
	@echo "Cron job removed"

schedule-capture-image:
	(crontab -l 2>/dev/null | grep -v "$(IMAGE_SCRIPT)"; echo "$(IMAGE_CRON_JOB)") | crontab -
	@echo "Cron job installed: captures image every hour"

unschedule-capture-image:
	crontab -l 2>/dev/null | grep -v "$(IMAGE_SCRIPT)" | crontab -
	@echo "Cron job removed"
