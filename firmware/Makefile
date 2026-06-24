CC := gcc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror -pedantic -Iinclude
BUILD_DIR := build

ifeq ($(OS),Windows_NT)
EXEEXT := .exe
MKDIR_P = powershell -NoProfile -Command "New-Item -ItemType Directory -Force -Path '$(BUILD_DIR)' | Out-Null"
RM_RF = powershell -NoProfile -Command "if (Test-Path -LiteralPath '$(BUILD_DIR)') { Remove-Item -LiteralPath '$(BUILD_DIR)' -Recurse -Force }"
else
EXEEXT :=
MKDIR_P = mkdir -p $(BUILD_DIR)
RM_RF = rm -rf $(BUILD_DIR)
endif

TEST_CRC16 := $(BUILD_DIR)/test_crc16$(EXEEXT)
TEST_TELEMETRY_PACKET := $(BUILD_DIR)/test_telemetry_packet$(EXEEXT)
TEST_XBEE_API := $(BUILD_DIR)/test_xbee_api$(EXEEXT)

.PHONY: all test clean

all: $(TEST_CRC16) $(TEST_TELEMETRY_PACKET) $(TEST_XBEE_API)

test: all
	$(TEST_CRC16)
	$(TEST_TELEMETRY_PACKET)
	$(TEST_XBEE_API)

$(BUILD_DIR):
	$(MKDIR_P)

$(TEST_CRC16): tests/test_crc16.c src/crc16.c include/crc16.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ tests/test_crc16.c src/crc16.c

$(TEST_TELEMETRY_PACKET): tests/test_telemetry_packet.c src/telemetry_packet.c src/crc16.c include/telemetry_packet.h include/crc16.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ tests/test_telemetry_packet.c src/telemetry_packet.c src/crc16.c

$(TEST_XBEE_API): tests/test_xbee_api.c src/xbee_api.c include/xbee_api.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ tests/test_xbee_api.c src/xbee_api.c

clean:
	$(RM_RF)
