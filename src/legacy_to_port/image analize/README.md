# Legacy Image Analysis Tool

This directory contains the source code for a legacy desktop application for image analysis. It is currently scheduled to be ported to the BCor modular framework.

## Project Structure (Legacy)
- `main.py`: Entry point for the PySide6 application.
- `gui/`: Contains UI definitions and custom widgets.
- `core/`: Legacy business logic and image processing utilities.
- `analytics/`: Historical implementation of reporting features.

## Technical Stack
- **UI Framework**: PySide6 (Qt for Python).
- **Database**: SQLite (see `astral_mariner.db`).
- **Processing**: Standard Python logging and base image manipulation.

## Porting Strategy
The goal is to extract the core image analysis logic into a BCor Domain Module and replace the monolithic PySide6 GUI with a modern web frontend or a modular BCor-driven desktop interface.
- **Step 1**: Identify domain aggregates in `core/`.
- **Step 2**: Define Commands and Events for analysis triggers.
- **Step 3**: Re-implement data persistence using the BCor Repository pattern.
