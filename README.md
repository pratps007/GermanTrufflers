# PRAVAH-X — National Multi-Hazard Disaster & Agricultural Resilience Intelligence Platform

> **Tagline**: *"Predict the impact. Protect people. Protect farms. Orchestrate recovery."*

---

## Overview

**PRAVAH-X** is an end-to-end multi-hazard spatial decision-support platform that connects:
`WEATHER → HAZARD → IMPACT → EXPOSURE → ACCESSIBILITY → RESOURCE DEMAND → RESPONSE → AGRICULTURAL IMPACT → FARMER ADVISORY → DAMAGE ASSESSMENT → RECOVERY`

Designed for disaster response authorities, municipal corporations, and agricultural departments, PRAVAH-X fuses fragmented spatial datasets into a single operational 3D digital twin.

---

## Key Features

1. **Multi-Hazard Impact Engine (`flood_impact_engine.py`)**:
   - Uses Copernicus DEM DSM 90m derivatives, elevation, slope, GCC waterways, stormwater drains, and rainfall intensity to compute surface inundation depth & ward risk scores.

2. **Dynamic Road Accessibility & Emergency Routing (`accessibility_engine.py`)**:
   - Dynamically classifies road network edges into `OPEN`, `CAUTION`, `INACCESSIBLE`.
   - Calculates dynamic NetworkX emergency routing avoiding flooded corridors.

3. **Agricultural Intelligence & ICAR Farmer Advisories (`agri_exposure_engine.py`, `farmer_advisory_engine.py`)**:
   - Monitors crop growth stages (`FLOWERING`, `VEGETATIVE`, `SEEDING`, `HARVEST`) and waterlogging submergence limits.
   - Generates evidence-backed action advisories for farmers derived from ICAR-CRIDA protocols.

4. **Data Provenance Registry (`data_registry.py`)**:
   - Central catalog (`GET /api/v1/data/catalog`) enforcing strict provenance tagging:
     - `● VERIFIED` (Official GIS / Agency Data)
     - `● OBSERVED` (Telemetry / Satellite Inundation)
     - `◐ MODELLED` (Hydrodynamic / Susceptibility Grids)
     - `◌ SIMULATED` (Synthetic Response Assets)

5. **Post-Event Infrastructure & Agricultural Recovery (`recovery_engine.py`)**:
   - Ranks recovery priorities into `RESTORE FIRST`, `RESTORE NEXT`, `MONITOR`.

---

## Technical Stack

- **Frontend**: React, TypeScript, Vite, CesiumJS, TailwindCSS, Lucide Icons.
- **Backend**: Python 3.13, FastAPI, NetworkX, GeoPandas, Pytest.
- **GIS Datasets**: Official GCC Wards (200), Zones (15), Rivers, Stormwater Drains (11.5k), Road Network (37.3k), Copernicus DEM DSM 90m.

---

## Quick Start

### Backend
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Swagger API docs available at: `http://127.0.0.1:8000/docs`

### Frontend
```bash
cd frontend
npm run dev
```
Web application available at: `http://localhost:5173`

### Run Pytest Suite
```bash
cd backend
python -m pytest tests/test_pravah_engine.py
```

---

## Scientific Disclaimer & Decision Support

> [!IMPORTANT]
> **PRAVAH-X** provides AI-assisted spatial decision support for emergency planning and scenario simulation. It does not replace official state disaster management authorities or emergency dispatch systems. All simulated assets and modelled extents are explicitly tagged with provenance metadata.
