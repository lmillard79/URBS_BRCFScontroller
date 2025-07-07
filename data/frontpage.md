The [2015 Final Hydrology Report](https://www.publications.qld.gov.au/dataset/7761ae95-ea44-4c0d-a3ea-53448c0d89f7/resource/2da11385-8c36-4afa-b609-4b67cf2a1883/download/hydrology-report-draft-final.pdf) delivered as part of BRCFS 2017 study, faced significant usability issues due to reliance on an opaque and cumbersome Excel-based  run interface that did not allow version control, inspection of macros due to password protection, outdated file formats and misplaced data. Our solution leverages **open-source Python-based** run management tools within this *Streamlit web application* to addresses these issues:
1.	*Eliminating Software Dependencies:* The browser-based Streamlit interface eliminates the need for specialised software, enabling stakeholders, including floodplain management professionals, to access URBS and TUFLOW results seamlessly, enhancing usability across Brisbane, Ipswich, Somerset, and Lockyer Valley councils.
2.	*Robust Data Management:* A structured, cloud-based data handover pack, integrated with a comprehensive metadata inventory (dataset name, owner, capture date, limitations), ensures secure storage 🔐and version control on GitHub, accompanied by a detailed README for transparency and replicability.
3.	*Streamlined Model Execution:* Clear instructions and automated scripts to run URBS and TUFLOW models, incorporating scripts (e.g., SUBRAIN utility, TUFLOW CSV outputs) to ensure replicability. This addresses the 2022 Verification Exercise findings regarding difficulties in replicating URBS model runs due to missing batch files and documentation.
4.	*Advanced Technical Integration:* The platform integrates complex hydrologic outputs, including flood frequency analysis and Deltares’ RTC Tools module for dam operations (i.e. loss of communications), presenting high-fidelity results aligned with ARR 2019 Version 4.2.

WRM's proposal is for a transformative Streamlit web-app solution delivers a transparent, secure platform that empowers stakeholders to interactively explore model 🔍 results, collaborate effectively, and meet QRA’s technical and engagement goals. We expect this will set a new standard for ease of access to intuitive, filterable visualisations of the extensive datasets of flood model results. This solution enhances transparency, usability, and resilience, positioning the BRCFS Model Update as a benchmark for flood risk management.

---
#### Setup
```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip     
```
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run urbs_flood_interface.py 
```
---

### WRM's Implementation Strategy
Our team, comprising RPEQ and Chartered Engineers proficient in URBS, advanced hydrologic modelling techniques and software development, will:
-	*Develop the Streamlit App:* Build a modular app with sections for data exploration, model results, calibration/validation, and climate scenarios, using Python libraries (e.g., Pandas, Geopandas, Plotly) for data processing and visualisation.
-	*Integrate with GitHub:* Host the app and data on GitHub, ensuring version control and secure access via authentication protocols, aligning with QRA’s data security requirements.
-	*Engage Stakeholders:* Conduct workshops to demonstrate the app’s functionality, gather feedback, and refine the interface, ensuring alignment with stakeholder needs and IPE review processes.
-	*Deliver Comprehensive Documentation:* Provide a data handover pack with a detailed report, model logs, and instructions for app usage, ensuring future practitioners can replicate and extend the work.
Streamlit as a Collaborative and Accessible Platform

Streamlit, as an open-source Python based web-app, offers an intuitive, interactive interface that allows stakeholders, including those without specialised software expertise, to engage with complex model outputs from URBS and TUFLOW simulations. 

### Key benefits include:
-	*Interactive Data Visualisation:* Stakeholders can explore thousands of Monte Carlo and ARR 2019 ensemble scenarios through dynamic dashboards, enabling real-time investigation of flood behaviour, peak water levels, depths, velocities, and hydraulic hazards across key locations (e.g., Brisbane River, Lockyer Creek, Bremer River). Interactive widgets allow users to filter results by Annual Exceedance Probability (AEP), climate scenarios, or sensitivity tests, fostering a deeper understanding of flood risk.
-	*Stakeholder Engagement:* The web app facilitates seamless collaboration by providing a centralised platform for the QRA, Independent Panel of Experts (IPE), and local councils (Brisbane, Ipswich, Somerset, Lockyer Valley) to review model outputs, calibration results, and climate change impacts. This aligns with the project’s governance requirements for stakeholder workshops and IPE review milestones, ensuring transparent feedback integration.
-	*Climate Change Scenario Integration:* The platform will incorporate ARR Version 4.2 climate change scenarios (e.g., SSP3-T4 for 2030, 2050, 2100) with clear visualisations of rainfall increases and their impacts on design flood levels. Users can toggle between scenarios to assess uncertainty and compare outcomes against the original BRCFS Monte Carlo methodology, addressing the project’s objective to evaluate ARR 2019 ensemble reproducibility.
-	*Open-Source and Future-Proof:* Hosted on GitHub, the Streamlit app leverages open-source software, eliminating licensing barriers (e.g., MapInfo) and ensuring compatibility with modern geospatial formats (Shapefile, GeoPackage). This avoids the issues of the 2017 BRCFS, where proprietary Excel macros with lost passwords hindered usability. GitHub’s version control ensures data integrity and traceability, supporting the project’s data management requirements.
