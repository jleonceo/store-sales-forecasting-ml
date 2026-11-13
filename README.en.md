Versión en español: [README.md](README.md)

# Daily sales forecasting by store and product

[![pruebas](https://github.com/jleonceo/store-sales-forecasting-ml/actions/workflows/ci.yml/badge.svg)](https://github.com/jleonceo/store-sales-forecasting-ml/actions/workflows/ci.yml)
[![produccion](https://github.com/jleonceo/store-sales-forecasting-ml/actions/workflows/produccion.yml/badge.svg)](https://github.com/jleonceo/store-sales-forecasting-ml/actions/workflows/produccion.yml)

Every morning, a large grocery retailer has to decide how much to buy, where to store it and what to ship to each store. All of that depends on knowing how much will be sold. This project forecasts it for every product and store, 8 days ahead, and runs every day: it adds the previous day's sales and updates the forecast.

A better forecast means less stock sitting in the warehouse, less money tied up in inventory and fewer customers facing an empty shelf.

## Results

In December 2015, a month set aside from the start and never used for training, the model forecasts one day ahead with a **mean error of 7.45 units** over the month's 31 mornings, against 10.43 for the usual purchasing rule. It beats the rule on 20 of the 31 mornings.

| Measure | Model | "Same as last week" rule |
|---|---|---|
| One day ahead, the 31 mornings of December 2015 | **7.45** units | 10.43 units |
| Eight days ahead from 12 dates in 2015, per product and day | **8.87** units | 10.68 units |
| Eight days ahead, both stores combined (24 to 31 December 2015) | **112.75** units/day | 123.25 units/day |
| One-day-ahead validation (November 2015, 3 folds of 8 days) | **7.46** units | 10.09 units |

The baseline is what a purchasing manager would do without a model: forecast for each day what was sold on the same weekday of the previous week. Every figure is a mean absolute error, in units, measured against that rule.

![Actual sales, model and rule for both stores combined, 24 to 31 December 2015](docs/graficos/01_total_dos_tiendas.png)

In Christmas week, for both stores combined, the model's error is 9 % lower than the rule's.

![Mean error by horizon day, from 12 dates in 2015](docs/graficos/02_error_por_horizonte.png)

The test from 12 dates repeats the whole process at each one: it trains on sales up to that day and forecasts the following 8. The error is 17 % lower than the rule's, and the model beats it on all 8 days of the horizon and in 160 of the 240 eight-day forecasts. It also beats two harder baselines: the mean of the last 7 days (9.67) and the mean of the same weekday over the previous 4 weeks (10.10).

Before fixing the model, that same test was repeated with nine configurations: default values, a hyperparameter search, a competition between six algorithms and two data corrections. In 2015 the per-series hyperparameter search was the change that lowered the error the most; in December that advantage was not confirmed. The figures are in the [experiment document](docs/05_experimento.md) and the full results in [`informes/experimento.json`](informes/experimento.json).

![Error of each of the 20 series in the November 2015 validation](docs/graficos/03_error_por_producto.png)

In the November validation, one day ahead, the model improves on the rule in 20 of the 20 series.

The chart titles and labels are in Spanish; the model is shown in blue, the rule in grey and actual sales in black.

## How it is built

```mermaid
flowchart LR
    subgraph S1[Model]
        direction TB
        D[Kaggle M5<br/>daily sales<br/>20 series, 2013 to 2015] --> V[Features from the<br/>series' own history<br/>past sales, averages,<br/>calendar and price]
        V --> M[One model per<br/>product and store<br/>HistGradientBoosting]
    end
    subgraph S2[Forecast]
        direction TB
        P[8-day forecast in a row<br/>each day feeds the next] --> T[Store totals<br/>adding up<br/>the products]
        P --> X[Error against<br/>repeating the<br/>previous week]
        E[Actual sales<br/>of the day] --> X
    end
    S1 --> S2
    S2 --> R{Retraining}
    R -->|Validates as well<br/>or better| N[New model<br/>in use]
    R -->|Validates worse| A[Current model<br/>stays]
    style R fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    style N fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
```


- Data: three years of daily sales (2013 to 2015) for 10 food products in 2 stores, 20 series in total, with calendar, events and weekly prices. The data is public, from the M5 competition on Kaggle (Walmart): [M5 Forecasting - Accuracy](https://www.kaggle.com/competitions/m5-forecasting-accuracy).
- Model: one machine learning model per store and product (HistGradientBoosting, from scikit-learn). The features come from the series' own history: sales on previous days, rolling statistics, calendar and events, price and flags for runs of days without sales.
- **How it is measured:** validation respects the order of time and hyperparameters were searched systematically. December 2015 was held out until the final test.
- **Tests:** every code change runs its automated tests.

## The four challenges of a real forecast

| Challenge | What the project does |
|---|---|
| Several days in a row | Recursive 8-day forecast: each forecast day feeds the next one. |
| Hierarchy | Product, store and total always add up, because they are summed bottom-up. |
| Many series | One model per product and store. The code is the same for any number of series; it has been tested with 20. |
| Days without sales | They are identified and separated: 1,745 single days and 1,259 days with the product out of the store, with dedicated features for zero-sales runs. |

## Production simulation

The project includes the batch process that would run every morning. It checks the incoming data, forecasts the next 8 days with sales known up to the previous day, and scores each forecast once actual sales exist. Retraining produces a candidate model, which replaces the one in use only if, measured against the rule, it validates at least as well, and the previous model can be restored with one command.

A GitHub Actions workflow runs that process over the 31 mornings of December 2015, one after another. December was already used in the final test, so this simulation shows that the process works day by day and does not add a new test of the model.

To see the deployment evidence:

- The [Actions](https://github.com/jleonceo/store-sales-forecasting-ml/actions) tab keeps every run of the `produccion` workflow, with its date, the log of the 31 mornings as the run summary and the outputs as a downloadable artifact. The first one, from 11 November 2026, is [here](https://github.com/jleonceo/store-sales-forecasting-ml/actions/runs/43074677107).
- [`informes/despliegue.json`](informes/despliegue.json) records the latest run of the process in this repository: the 31 mornings expected and completed, the model in use and the check that the morning of 24 December gives the expected figures.
- [`produccion/salidas/`](produccion/salidas/) holds the forecast and the evaluation of each morning, so they can be read without downloading anything.

## How to reproduce it

Python 3.13 is required. Library versions are pinned in `requirements.txt`.

```bash
pip install -r requirements.txt
python ejecutar_todo.py
```

`ejecutar_todo.py` starts from the two databases in `datos/` and rebuilds everything: unit tests, retraining, the December simulation, results and charts. At the end it checks that the figures on this page match the ones just produced. `python ejecutar_todo.py --backtest` also repeats the test from 12 dates, which takes between one and two hours.

To launch the production workflow on GitHub: **Actions** tab, **produccion** workflow, **Run workflow** button. The test workflow (`ci.yml`) runs on every change.

## Documentation

The project follows the CRISP-DM phases, and each document belongs to one. The technical documents are written in Spanish.

| Phase | Document |
|---|---|
| Business understanding | This page: the problem and the rule the model is compared with |
| Data understanding | [Data and quality](docs/01_datos_y_calidad.md): what the data contains and how each issue was handled |
| Data preparation | [Features](docs/02_variables.md): what the model sees for each day and why no feature looks into the future |
| Modeling | [Model and validation](docs/03_modelo_y_validacion.md) and [Experiment](docs/05_experimento.md): the algorithm, the search and the alternatives measured |
| Evaluation | [Evaluation](docs/04_evaluacion.md): results by horizon, by series and by level |
| Deployment | [Production](docs/06_produccion.md), [Model card](docs/ficha_del_modelo.md) and [Input contract](produccion/contrato_entrada.md): the daily process, retraining, rollback and what it needs and delivers |

An external code review found errors in the first version; evaluation led back to data preparation and modeling, as CRISP-DM expects. What changed is in [CHANGELOG.md](CHANGELOG.md).

## Limits and next step

The final test is a single month. In Christmas week, product by product, the model is slightly ahead of the rule (9.61 against 10.05), but the difference is within chance; the clear advantage shows when the stores are added up, one day ahead and in the test from 12 dates. The model tends to forecast slightly too much, and its largest errors are on days without sales. The code has been tested with 20 series.

Beating the rule product by product in weeks like Christmas requires inventory data: knowing whether a day without sales happened because nobody bought or because the shelf was empty.

## License

The code is released under the MIT license ([LICENSE](LICENSE)). The data belongs to its original source: [M5 Forecasting - Accuracy](https://www.kaggle.com/competitions/m5-forecasting-accuracy).
