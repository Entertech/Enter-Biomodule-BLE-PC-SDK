# Enter BLE SDK For PC

## Introduction

Enter BLE SDK For PC is provided by [EnterTech](https://www.entertech.cn/), and it is tailored for EnterTech's Bluetooth chips for PC. This SDK is developed in Python and can run on macOS, Linux, and Windows.

## Installation

`pip install enterble`

## Features

1. Search for Bluetooth devices
2. Connect to Bluetooth devices
3. Communicate with Bluetooth devices
4. Adaptation for data exchange with EnterTech's Flowtime series chips

## Usage

See [examples](https://github.com/Entertech/Enter-Biomodule-BLE-PC-SDK/tree/main/examples)

### Guide
1. Start scanning for devices
    - `loop.run_until_complete(device_discover())`
2. Run simple.py
3. Observe the device scanning situation
4. Change the unique device ID to the one you scanned for your device (use UUID for macOS systems, MAC address for Win systems)
    - ```python
      device_identify = (
          "d2:ab:3f:c9:37:ad"
          if platform.system() != "Darwin"
          else "D5D4362A-1690-4204-B797-3015EEDB510E"
      )
      ```
5. Start the code for data collection
    - `loop.run_until_complete(data_collector())`
6. Run simple.py
