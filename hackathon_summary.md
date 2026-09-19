# PRAVAH-X — Hackathon Presentation Summary (6-Slide Structure)

## SLIDE 1: COVER
### PRAVAH-X
**National Multi-Hazard Disaster & Agricultural Resilience Intelligence Platform**
- **Tagline**: *"Predict the impact. Protect people. Protect farms. Orchestrate recovery."*
- **Pilot Region**: Greater Chennai Metropolitan Area & Peri-Urban Agricultural Belts (Tiruvallur, Kanchipuram, Chengalpattu).
- **Core Technology**: 3D Cesium Spatial Engine + Copernicus DEM + NetworkX Routing + Hydrodynamic Consequence Engine + ICAR Agromet Rulebook.

---

## SLIDE 2: THE PROBLEM
### Fragmented Disaster Intelligence & Warning-to-Action Gap
- **Operational Reality**: India loses billions annually to recurring extreme weather events (urban floods, flash inundation, waterlogging).
- **The Core Failure**: Fragmented data across weather agencies, GIS municipal bodies, road departments, and agricultural boards.
- **The Operational Gap**: `WARNING ≠ ACTION`. Authorities receive rainfall millimeter figures, but lack dynamic spatial clarity on which roads fail, which wards become isolated, and which crops reach submergence limits.

---

## SLIDE 3: THE SOLUTION
### Unified End-to-End Intelligence Pipeline
- **Integrated Decision Support**: Fuses 10 operational stages into one live spatial picture:
  `WEATHER → HAZARD → IMPACT → EXPOSURE → ACCESSIBILITY → RESOURCE DEMAND → RESPONSE → FARMER ADVISORY → DAMAGE REPORTING → RECOVERY`
- **Dual Focus**: Protects both **PEOPLE & URBAN INFRASTRUCTURE** and **FARMS, CROPS & LIVESTOCK**.
- **Evidence-Based Action**: Generates prioritized pre-positioning plans for authorities and evidence-backed crop advisories for farmers.

---

## SLIDE 4: TECHNICAL ARCHITECTURE
### Data Fusion & Provenance-Aware Engine
```
IMD / ISRO / GCC / ICAR / Copernicus DEM / OpenStreetMap
                   │
                   ▼
       Central Data Registry (data_registry.py)
  [VERIFIED | OBSERVED | MODELLED | SIMULATED]
                   │
                   ▼
          Data Fusion Engine (data_fusion_engine.py)
 ┌─────────────────┼─────────────────┬─────────────────┐
 ▼                 ▼                 ▼                 ▼
Flood Impact     Road Access     Agri Exposure     Recovery Priority
 Engine           Engine          & Advisory       Engine
 └─────────────────┼─────────────────┴─────────────────┘
                   │
                   ▼
     3D Cesium Command Center & AI Orchestrator
```

---

## SLIDE 5: INNOVATION & KEY DIFFERENTIATORS
- **Provenance Transparency**: Every data layer and decision displays explicit scientific provenance (`● VERIFIED`, `● OBSERVED`, `◐ MODELLED`, `◌ SIMULATED`).
- **Dynamic Road Accessibility**: Classifies road networks into `OPEN`, `CAUTION`, `INACCESSIBLE` and reroutes emergency units around submerged corridors.
- **Agromet Crop Vulnerability**: Evaluates submergence tolerance across crop growth stages (`FLOWERING`, `VEGETATIVE`, `SEEDING`) using ICAR-CRIDA protocols.
- **Explainable Decisions**: Every AI recommendation includes an explicit **"WHY?"** reasoning breakdown.
- **Post-Event Recovery**: Prioritizes infrastructure & agricultural restoration (`RESTORE FIRST`, `RESTORE NEXT`, `MONITOR`).

---

## SLIDE 6: PROTOTYPE STATUS & NATIONAL SCALABILITY
- **Working Pilot**: Full pilot active for Greater Chennai Region (200 GCC Wards, 15 Zones, 37.3k Road Edges, Copernicus DEM 90m DSM).
- **Extensible Architecture**: Multi-region template ready for Bhubaneswar (Odisha), Guwahati (Assam), Pune (Maharashtra), and Ahmedabad (Gujarat).
- **API & Digital Twin**: RESTful FastAPI backend with open endpoints (`/api/v1/data/catalog`, `/api/v1/agriculture/*`, `/api/v1/event/*`).
