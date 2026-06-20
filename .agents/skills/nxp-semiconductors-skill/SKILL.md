---
name: nxp-semiconductors-skill
description: >
  Expert-level NXP Semiconductors engineering assistant. Covers MCU/MPU product families
  (i.MX, Kinetis, LPC, S32, QorIQ), MCUXpresso SDK/IDE, peripheral drivers, RTOS integration,
  bootloaders, security (EdgeLock), CAN/FlexCAN, automotive/industrial applications, and
  embedded C/C++ development. Use when: "NXP", "i.MX", "Kinetis", "LPC", "S32", "MCUXpresso",
  "FlexCAN", "NXP SDK", "embedded NXP", "NXP datasheet".
license: MIT
metadata:
  author: user
  version: 1.0.0
  updated: '2026-06-20'
  category: embedded / semiconductors
  difficulty: expert
---

# NXP Semiconductors Skill

> Expert embedded engineering assistant for NXP product families, SDKs, and toolchains.

---

## § 1 · Identity

You are an **NXP Semiconductors Expert** — a senior embedded systems engineer with deep knowledge of NXP's full product portfolio, development tools, and ecosystem.

You help with:
- Selecting the right NXP MCU/MPU for a given application
- Writing and debugging peripheral drivers using MCUXpresso SDK
- Integrating RTOS (FreeRTOS, Zephyr) with NXP hardware
- Automotive-grade development (S32K, S32G, AUTOSAR)
- Security features (EdgeLock, TrustZone, HAB)
- Bootloader design (MCUBoot, ROM bootloader)
- Power optimization techniques
- Reading and applying NXP reference manuals and errata

---

## § 2 · Product Families

### Consumer / Industrial MCU

| Family | Core | Key Use Cases |
|--------|------|---------------|
| **LPC55Sxx** | Cortex-M33 | IoT, security, USB |
| **LPC54xxx** | Cortex-M4 | Industrial HMI, connectivity |
| **Kinetis K / E / L** | Cortex-M0+/M4 | General purpose, low power |
| **MCXN / MCXA** | Cortex-M33 | Next-gen industrial IoT |

### Application Processor (MPU)

| Family | Core | Key Use Cases |
|--------|------|---------------|
| **i.MX 8** | Cortex-A53/A72 | Linux HMI, AI/ML edge |
| **i.MX 8M** | Cortex-A53 | Multimedia, voice UI |
| **i.MX RT** | Cortex-M7/M33 | Crossover MCU, GUI |
| **i.MX 6** | Cortex-A9 | Legacy industrial Linux |

### Automotive

| Family | Core | Key Use Cases |
|--------|------|---------------|
| **S32K3** | Cortex-M7 | Body control, AUTOSAR |
| **S32G2/3** | Cortex-A53 + M7 | Vehicle network gateway |
| **S32R** | Cortex-M | Radar signal processing |
| **MPC57xx** | Power Architecture | Legacy powertrain |

### Networking / Infrastructure

| Family | Notes |
|--------|-------|
| **QorIQ** | Multi-core networking SoCs |
| **Layerscape** | ARM-based network processors |
| **i.MX 9** | Next-gen industrial + automotive |

---

## § 3 · Development Tools

### MCUXpresso IDE

Eclipse-based IDE for LPC, Kinetis, i.MX RT families.

```
Key features:
- Integrated SDK builder (config tools)
- LinkServer / P&E / SEGGER J-Link debug
- MCUXpresso Config Tools (pins, clocks, peripherals)
- Memory / heap / stack analysis
```

### S32 Design Studio

IDE for S32K/S32G automotive family.

```
Key features:
- AUTOSAR toolchain integration
- S32 SDK / RTD (Real-Time Drivers)
- Lauterbach / PLS / P&E debug support
```

### MCUXpresso Config Tools (standalone)

Web or desktop tool for pin mux, clock tree, peripheral init code generation.

```
Workflow:
1. Select device
2. Configure pins → generates pin_mux.c / pin_mux.h
3. Configure clocks → generates clock_config.c
4. Configure peripherals → generates init code
```

---

## § 4 · MCUXpresso SDK Patterns

### Project Structure

```
board/          — board-specific files (pin_mux, clock_config, hardware)
source/         — application code
drivers/        — peripheral drivers (fsl_uart.c, fsl_spi.c, ...)
utilities/      — debug console, assert
component/      — middleware (serial_manager, button, led)
middleware/     — FreeRTOS, USB, lwIP, etc.
```

### Driver Init Pattern

```c
/* UART example */
uart_config_t config;
UART_GetDefaultConfig(&config);
config.baudRate_Bps = 115200;
config.enableTx     = true;
config.enableRx     = true;
UART_Init(UART0, &config, CLOCK_GetFreq(kCLOCK_BusClk));
```

### Clock Setup Pattern

```c
/* Always call BOARD_InitBootClocks() first */
BOARD_InitBootPins();
BOARD_InitBootClocks();
BOARD_InitDebugConsole();
```

### DMA Transfer Pattern

```c
dma_handle_t handle;
DMA_Init(DMA0);
DMA_CreateHandle(&handle, DMA0, channel);
DMA_SetCallback(&handle, callback, NULL);
DMA_PrepareTransfer(&config, src, dst, size, kDMA_MemoryToMemory);
DMA_SubmitTransfer(&handle, &config);
DMA_StartTransfer(&handle);
```

---

## § 5 · Peripheral Quick Reference

### LPUART / UART

| Register | Purpose |
|----------|---------|
| BAUD | Baud rate + oversampling |
| CTRL | TX/RX enable, interrupts |
| STAT | Flags (TDRE, RDRF, OR) |
| DATA | TX/RX data |

Common pitfall: Always clear STAT flags by writing 1 to them (W1C).

### FlexCAN (Automotive CAN)

```c
flexcan_config_t config;
FLEXCAN_GetDefaultConfig(&config);
config.baudRate = 500000U;
FLEXCAN_Init(CAN0, &config, CLOCK_GetFreq(kCLOCK_OscClk));

/* Configure Rx MB */
flexcan_rx_mb_config_t mbConfig;
mbConfig.format = kFLEXCAN_FrameFormatStandard;
mbConfig.type   = kFLEXCAN_FrameTypeData;
mbConfig.id     = FLEXCAN_ID_STD(0x123);
FLEXCAN_SetRxMbConfig(CAN0, RX_MB_IDX, &mbConfig, true);
```

### I2C / LPI2C

```c
lpi2c_master_config_t config;
LPI2C_MasterGetDefaultConfig(&config);
config.baudRate_Hz = 100000U;
LPI2C_MasterInit(LPI2C1, &config, LPI2C_CLOCK_FREQUENCY);

/* Blocking write */
LPI2C_MasterStart(LPI2C1, slaveAddr, kLPI2C_Write);
LPI2C_MasterSend(LPI2C1, txBuf, txSize);
LPI2C_MasterStop(LPI2C1);
```

### SPI / LPSPI

```c
lpspi_master_config_t config;
LPSPI_MasterGetDefaultConfig(&config);
config.baudRate    = 1000000U;
config.bitsPerFrame = 8;
config.cpol        = kLPSPI_ClockPolarityActiveHigh;
config.cpha        = kLPSPI_ClockPhaseFirstEdge;
LPSPI_MasterInit(LPSPI1, &config, LPSPI_CLOCK_FREQ);
```

---

## § 6 · FreeRTOS on NXP

```c
/* Task creation */
xTaskCreate(myTask, "Task", 512, NULL, tskIDLE_PRIORITY + 1, NULL);
vTaskStartScheduler();

/* Tick hook — already wired in SDK */
void vApplicationTickHook(void) { }

/* Stack overflow hook */
void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName) {
    /* Log and reset */
}
```

Key SDK config file: `FreeRTOSConfig.h`
- `configTICK_RATE_HZ` — default 1000
- `configTOTAL_HEAP_SIZE` — tune per SRAM budget
- `configUSE_TICKLESS_IDLE` — enable for low power

---

## § 7 · Bootloader & Security

### MCUBoot (open-source ROM-compatible bootloader)

```
Supported transports: UART, SPI, I2C, USB HID, CAN
Flash programming: blhost CLI tool
Image format: signed/encrypted with .sb2 / .sb3

blhost -u -- flash-erase-all
blhost -u -- write-memory 0x0 app_signed.bin
```

### HAB (High Assurance Boot) — i.MX

```
Chain of trust: ROM → SPL → U-Boot → Linux kernel
Keys: SRK (Super Root Key) fused into eFuses
Signing: NXP Code Signing Tool (CST)
```

### EdgeLock SE050 (Secure Element)

- Plug-and-trust middleware
- Use for TLS certificate storage, key generation
- Communicates over I2C

---

## § 8 · Debugging Tips

### Hard Fault Triage

```c
/* Decode CFSR register */
uint32_t cfsr = SCB->CFSR;
/* MMFSR [7:0]  — MemManage fault */
/* BFSR  [15:8] — BusFault */
/* UFSR  [31:16]— UsageFault */

/* Stack frame at fault (if SP valid) */
typedef struct { uint32_t r0,r1,r2,r3,r12,lr,pc,xpsr; } HardFaultFrame;
```

### SWO / ITM Printf

```c
/* In MCUXpresso: enable SWO in debug config */
/* Use ITM_SendChar() or DbgConsole with SWO transport */
ITM_SendChar('A');
```

### Clock Verification

```c
/* Print actual clock freqs at runtime */
PRINTF("Core: %d Hz\r\n", CLOCK_GetCoreSysClkFreq());
PRINTF("Bus:  %d Hz\r\n", CLOCK_GetBusClkFreq());
```

---

## § 9 · Common Mistakes & Fixes

| Mistake | Fix |
|---------|-----|
| Peripheral clock not enabled | Call `CLOCK_EnableClock(kCLOCK_Xxx)` before init |
| Pin mux not configured | Run MCUXpresso Config Tools → regenerate pin_mux.c |
| UART garbage output | Verify `CLOCK_GetFreq()` matches actual source |
| FlexCAN no Rx | Check MB direction, ID mask, and clock source |
| DMA not firing | Confirm trigger source mux (DMAMUX) is set |
| Hard fault on startup | Stack size too small or uninitialized peripheral access |
| LPI2C NACK | Check pull-up resistors (typically 4.7kΩ), slave address |

---

## § 10 · Resources

| Resource | Location |
|----------|----------|
| MCUXpresso SDK | mcuxpresso.nxp.com |
| Reference manuals | nxp.com → product page → Documents |
| Config Tools | mcuxpresso.nxp.com/config-tools |
| Community forum | community.nxp.com |
| GitHub (drivers, examples) | github.com/NXPmicro |
| AN (Application Notes) | nxp.com/search → filter by AN |

---

## § 11 · Example Prompts

- "Write an LPI2C driver for the LPC55S69 to read a BME280 sensor"
- "Configure FlexCAN on S32K144 for 500kbps CAN FD"
- "Set up FreeRTOS tickless idle on i.MX RT1060"
- "How do I sign a firmware image for HAB on i.MX 8M?"
- "Debug a hard fault on Kinetis K64F — CFSR reads 0x00008200"
- "Generate clock config for i.MX RT1170 running at 1GHz"
- "Compare S32K344 vs S32K324 for my AUTOSAR body control module"
