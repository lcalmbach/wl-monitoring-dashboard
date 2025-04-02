# Groundwater Monitoring Basel-Stadt

An interactive dashboard for visualizing and analyzing groundwater data in the canton of Basel-Stadt.  
The app is built with [Panel](https://panel.holoviz.org/) and uses data from [data.bs.ch](https://data.bs.ch). Three datasets are integrated: groundwater levels, precipitation data, and borehole records. By combining them in a single application, the dashboard provides additional insights and gives users convenient access to related environmental data sources.

![Header](./header-trinkwasser_lange-erlen-grundwasserwerk_1280px.jpg)

> [📷 Image source](https://www.iwb.ch/klimadreh/ratgeber/sauberes-trinkwasser/wie-funktioniert-die-trinkwasserversorgung-in-basel)

---

## 🔧 Features

- Filterable visualization of groundwater levels from various measuring stations
- Historical data overview (since 1977)
- Interactive map view (based on station coordinates)
- Annual pattern comparison across stations
- Responsive layout using `MaterialTemplate` from `panel`

---

## 🧪 Tech Stack

- **Python** (3.9+ recommended)
- **Panel**
- **Altair**
- **Folium**

---

## 🚀 Getting Started

### 1. Clone the repository and create a virtual environment (on Windows)

```bash
git clone https://github.com/lcalmbach/wl-monitoring-dashboard.git
cd wl-monitoring-dashboard
>py -m venv .venv
>.venv/scripts/activate
>(.venv) pip install -r requirements.txt
> panel serve app/dashboard.py --dev
```

## 📊 Data Source

All data is sourced from the official open data portal of the Canton of Basel-Stadt:

- 🌐 [data.bs.ch](https://data.bs.ch)

---

## 👤 Author

Lukas Calmbach  
📧 [lcalmbach@gmail.com](mailto:lcalmbach@gmail.com)  
🔗 [GitHub Profile](https://github.com/lcalmbach)

---

## 📄 License

This project is licensed under the **MIT License** – see [LICENSE](./LICENSE) for details.



