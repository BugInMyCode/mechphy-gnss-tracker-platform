CC := gcc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror -pedantic -Iinclude
BUILD_DIR := build

ifeq ($(OS),Windows_NT)
EXEEXT := .exe
MKDIR_P = powershell -NoProfile -Command "New-Item -ItemType Directory -Force -Path '$(BUILD_DIR)' | Out-Null"
RM_RF = powershell -NoProfile -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue '$(BUILD_DIR)'"
else
EXEEXT :=
MKDIR_P = mkdir -p $(BUILD_DIR)
RM_RF = rm -rf $(BUILD_DIR)
endif

TEST_CRC16 := $(BUILD_DIR)/test_crc16$(EXEEXT)
TEST_TELEMETRY_PACKET := $(BUILD_DIR)/test_telemetry_packet$(EXEEXT)

.PHONY: all test clean

all: $(TEST_CRC16) $(TEST_TELEMETRY_PACKET)

test: all
	$(TEST_CRC16)
	$(TEST_TELEMETRY_PACKET)

$(BUILD_DIR):
	$(MKDIR_P)

$(TEST_CRC16): tests/test_crc16.c src/crc16.c include/crc16.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ tests/test_crc16.c src/crc16.c

$(TEST_TELEMETRY_PACKET): tests/test_telemetry_packet.c src/telemetry_packet.c src/crc16.c include/telemetry_packet.h include/crc16.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ tests/test_telemetry_packet.c src/telemetry_packet.c src/crc16.c

clean:
	$(RM_RF)
