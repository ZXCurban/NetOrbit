<p align="center">
  <img src="https://github.com/user-attachments/assets/b671d9c6-f5d9-44c7-9480-26d15b6f5606" alt="NetOrbit live terminal packet map demo" width="960">
</p>

<h1 align="center">NetOrbit</h1>

<p align="center">
  <strong>Real-time global packet visualization in your terminal.</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"></a>
  <a href="https://opensource.org/license/mit"><img alt="License MIT" src="https://img.shields.io/badge/License-MIT-00E676?style=for-the-badge"></a>
  <img alt="Fedora Support" src="https://img.shields.io/badge/Fedora-supported-51A2DA?style=for-the-badge&logo=fedora&logoColor=white">
  <img alt="TUI Rich" src="https://img.shields.io/badge/TUI%2FRich-terminal_native-00D9FF?style=for-the-badge">
  <img alt="Textual Rich" src="https://img.shields.io/badge/Textual%2FRich-neon_console-FF00AA?style=for-the-badge">
</p>

<p align="center">
  <code>Scapy</code> packet capture · <code>Textual/Rich</code> terminal aesthetic · Braille world map · live GeoIP telemetry
</p>

---

## English

## Why NetOrbit?

NetOrbit turns raw outbound IPv4 traffic into visual intelligence. Every external packet becomes a signal on a terminal-native world map: where your machine is talking, how fast destinations appear, and what routes light up while you work.

It is built for people who want network awareness without leaving the shell. No browser dashboard. No heavy desktop UI. Just a cyberpunk command center running directly in your terminal.

- 🛰️ **Visual intelligence:** watch outbound connections land on a global map instead of reading dead packet logs.
- ⚡ **Real-time tracking:** Scapy captures traffic asynchronously while the TUI keeps rendering.
- 🧬 **Pure terminal aesthetics:** high-density Braille pixels, neon-style traces, and Rich-powered panels.
- 🧊 **Low CPU footprint:** static map caching keeps warm renders fast, measured at **0.0044s**.

## One-Command Install

Use `pipx` to install NetOrbit as an isolated CLI tool:

```bash
pipx install git+https://github.com/ZXCurban/NetOrbit.git
```

Then launch packet capture with root privileges:

```bash
sudo netorbit
```

> [!IMPORTANT]
> Root is required because NetOrbit captures packets through Scapy. On Linux, NetOrbit can also re-run itself through `sudo` when capture privileges are missing.

## Quick Start

```bash
# Install
pipx install git+https://github.com/ZXCurban/NetOrbit.git

# Run live capture
sudo netorbit
```

Need to inspect available network interfaces first?

```bash
netorbit --list-interfaces
```

Want the visual experience without root or real traffic?

```bash
netorbit --demo
```

Force a specific interface or a VPN + default-route pair:

```bash
sudo netorbit -i tun0,wlo1
```

## Key Features

- 🌍 **Braille-rendered world map** with dense terminal pixels and a coordinate grid.
- 🎯 **Sub-pixel accuracy** through a virtual 2x4 Braille dot layer.
- 📡 **Async Scapy sniffing** for live outbound IPv4 capture without blocking the UI.
- 🧠 **GeoIP resolution** via MaxMind-compatible workflows and IP-API fallback.
- 🔥 **Live destination traces** from your home point to remote IP locations.
- 🧾 **Recent connection panel** with IP, country, protocol, size, and interface data.
- 🛡️ **Smart filtering** for local, private, multicast, and broadcast addresses.
- ❄️ **Low CPU footprint** with cached static map layers and **0.0044s warm render**.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Runtime | Python 3.10+ |
| Terminal UI | Textual/Rich terminal aesthetic, implemented with Rich rendering |
| Packet capture | Scapy `AsyncSniffer` |
| Geolocation | MaxMind-ready architecture / IP-API |
| Rendering | Braille canvas, cached world mask, sub-pixel trajectories |

## Commands

```bash
netorbit --help
netorbit --list-interfaces
netorbit --demo
sudo netorbit
sudo netorbit -i eth0
sudo netorbit -i tun0,wlo1
```

## How It Works

1. NetOrbit detects one or more capture interfaces from your routing table.
2. Scapy streams outbound IPv4 packets into an async pipeline.
3. Local and non-routable destinations are filtered out.
4. GeoIP lookup resolves remote IPs to latitude, longitude, country, and city.
5. The renderer projects coordinates onto a cached Braille world map.
6. Rich updates the terminal with active traces and recent connection telemetry.

## Requirements

- Linux recommended, Fedora supported.
- Python **3.10+**.
- `pipx` for clean CLI installation.
- Root privileges for real packet capture.

---

## Русский

## Почему NetOrbit?

NetOrbit превращает исходящий IPv4-трафик в визуальную разведку. Каждый внешний пакет становится сигналом на терминальной карте мира: куда говорит ваша машина, какие направления вспыхивают в реальном времени и как выглядит сеть прямо из shell.

Это инструмент для тех, кому нужна сетевая осведомленность без браузерных панелей и тяжелого UI. Только терминал, живая карта и киберпанковский командный центр в одну команду.

- 🛰️ **Визуальная разведка:** внешние соединения видны на карте, а не теряются в сухих логах.
- ⚡ **Отслеживание в реальном времени:** Scapy асинхронно ловит пакеты, пока TUI продолжает рендеринг.
- 🧬 **Чистая терминальная эстетика:** плотные Braille-пиксели, неоновые трассы и панели на Rich.
- 🧊 **Низкая нагрузка на CPU:** кэш статической карты дает быстрый теплый рендер, измерено **0.0044s**.

## Установка в одну команду

Используйте `pipx`, чтобы установить NetOrbit как изолированный CLI-инструмент:

```bash
pipx install git+https://github.com/ZXCurban/NetOrbit.git
```

Запуск реального захвата пакетов требует root-доступ:

```bash
sudo netorbit
```

> [!IMPORTANT]
> Root нужен потому, что NetOrbit захватывает пакеты через Scapy. На Linux приложение также может автоматически перезапуститься через `sudo`, если прав для захвата не хватает.

## Быстрый старт

```bash
# Установка
pipx install git+https://github.com/ZXCurban/NetOrbit.git

# Запуск live-захвата
sudo netorbit
```

Посмотреть доступные сетевые интерфейсы:

```bash
netorbit --list-interfaces
```

Запустить визуальный режим без root и реального трафика:

```bash
netorbit --demo
```

Принудительно выбрать интерфейс или пару VPN + default-route:

```bash
sudo netorbit -i tun0,wlo1
```

## Ключевые возможности

- 🌍 **Карта мира на Braille** с плотной терминальной графикой и координатной сеткой.
- 🎯 **Sub-pixel accuracy** через виртуальный слой Braille 2x4 точек.
- 📡 **Асинхронный Scapy-sniffing** для live-захвата исходящих IPv4-пакетов без блокировки UI.
- 🧠 **GeoIP-резолвинг** с архитектурой под MaxMind и fallback через IP-API.
- 🔥 **Живые трассы назначений** от вашей home-точки к удаленным IP.
- 🧾 **Панель последних соединений** с IP, страной, протоколом, размером и интерфейсом.
- 🛡️ **Умная фильтрация** локальных, приватных, multicast и broadcast-адресов.
- ❄️ **Низкая нагрузка на CPU** благодаря кэшу статических слоев карты и **0.0044s warm render**.

## Технологический стек

| Слой | Технология |
| --- | --- |
| Runtime | Python 3.10+ |
| Terminal UI | Textual/Rich terminal aesthetic, implemented with Rich rendering |
| Захват пакетов | Scapy `AsyncSniffer` |
| Геолокация | MaxMind-ready architecture / IP-API |
| Рендеринг | Braille canvas, cached world mask, sub-pixel trajectories |

## Команды

```bash
netorbit --help
netorbit --list-interfaces
netorbit --demo
sudo netorbit
sudo netorbit -i eth0
sudo netorbit -i tun0,wlo1
```

## Как это работает

1. NetOrbit определяет один или несколько интерфейсов захвата по таблице маршрутизации.
2. Scapy передает исходящие IPv4-пакеты в асинхронный pipeline.
3. Локальные и неротируемые адреса отфильтровываются.
4. GeoIP lookup превращает удаленный IP в широту, долготу, страну и город.
5. Рендерер проецирует координаты на кэшированную Braille-карту мира.
6. Rich обновляет терминал активными трассами и телеметрией последних соединений.

## Требования

- Рекомендуется Linux, Fedora поддерживается.
- Python **3.10+**.
- `pipx` для чистой CLI-установки.
- Root-доступ для реального захвата пакетов.
