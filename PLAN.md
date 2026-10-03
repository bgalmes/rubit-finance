# Rubit Finance

Application to manage personal finances. It shows results to the user based on the data they enter. It will have several modules, each one with its own objective. The project starts with a module in charge of showing all the data derived from a mortgage, given its conditions.

This document defines the **MVP**: the Mortgage module plus the application stack. Sections marked as future are out of scope.

## Rubit Finance Mortgage module (MVP)

This module computes all the data of a given mortgage. Given its conditions, it shows all the derived data to the user.

### Objective

Help the user compare different loans with real data, or help the user make decisions about a loan they are already paying.

It will help the user make decisions about future mortgage amortizations, cancellation, ...

### Restrictions or limitations

* Variable mortgages won't show all the real data of the mortgage, as the app can only make an estimation.
* It won't have any integration with external APIs, so all data will be computed with financial maths.
* It will only consider the French amortization system.
* Amounts are in EUR. The UI is in English only (i18n is set up so other languages can be added later).

### Details

The application lets you enter the data of different mortgages, save them, and then compare them in a table.

The next sections specify the input and the output of a mortgage.

#### Fixed interest rate mortgages configuration

To configure a mortgage you must enter the data that defines the mortgage conditions. You can either enter the purchase information (mode A) or the loan amount directly (mode B).

These fields are always shown, whichever mode you use:

| Field                  | Default value | Additional info                                  |
|------------------------|---------------|--------------------------------------------------|
| Descriptive name       | `Mortgage N`  | Optional. `N` is the next free number.           |
| Interest rate (TIN)    |               | Required. Nominal annual rate, in %.             |
| Duration (years)       |               | Required. Whole years.                           |
| Payment frequency      | Monthly       | Required. Monthly (12 payments/year) or Annual (1 payment/year). |

**Mode A: from purchase.** Fill in the next fields:

| Field                  | Default value | Additional info                                  |
|------------------------|---------------|--------------------------------------------------|
| Purchase price         |               | Required.                                        |
| Initial savings        | 0             | Money you contribute at the start.               |
| Initial expenses       | 0             | Taxes, notary, registry, agency, ...             |

**Mode B: loan amount.** Fill in only:

| Field                  | Default value | Additional info                                  |
|------------------------|---------------|--------------------------------------------------|
| Loan amount            |               | Required. The amount you need to borrow.         |

Validation rules:

* Purchase price > 0 and the resulting loan amount > 0.
* 0 ≤ TIN ≤ 100.
* 1 ≤ duration ≤ 50 years.
* Initial savings ≥ 0 and initial expenses ≥ 0.
* Mode A: initial savings < purchase price + initial expenses (otherwise there is nothing to borrow).

Once all the required fields are filled in and the mortgage is saved, you will see a summary of the configured mortgage with the next fields:

* Loan amount
* Payment per period
* Mortgage percentage of the purchase price (mode A only; `—` in mode B)
* Amortization table

> In the future you will be able to configure a mortgage which are you already paying. It will allow you to inspect the status of your mortgage.

#### Calculations

Notation:

* `k`: payments per year (12 for monthly, 1 for annual).
* `n = years · k`: total number of payments.
* `r = TIN / 100 / k`: interest rate per period.

Formulas:

* **Down payment** (mode A) = initial savings − initial expenses. The savings pay the expenses first, and the rest goes towards the price.
* **Loan amount** `L` = purchase price + initial expenses − initial savings (mode A), or the entered value (mode B).
* **Mortgage percentage of the purchase price** = `L / purchase price` (mode A only).
* **Payment per period** `P = L · r / (1 − (1 + r)^−n)`. If `r = 0`, then `P = L / n`.
* **Amortization table**, for each period `i = 1..n`, starting from balance = `L`:
  * interest = balance · r
  * principal = P − interest
  * balance = balance − principal
  * amortized capital = amortized capital + principal
* **Total interest** = sum of the interest column.
* **Total amount paid** = L + total interest.

Money handling: all calculations use Python `Decimal` at full precision. Results are rounded to 2 decimals (half-up) per period in the amortization table, and the last payment is adjusted so the outstanding balance ends at exactly 0.00.

Reference example: L = 200,000 €, TIN 3%, 30 years, monthly → P ≈ 843.21 €.

#### Early amortizations

From the amortization table of a saved mortgage you can register an early amortization on any period. It is applied right after that period's regular payment, and there is at most one per period. There are two types:

* **Capital**: you enter an amount. The term stays the same and the payment is recalculated over the remaining periods: `P' = periodic payment(new balance, r, remaining periods)`.
* **Periods**: the payment stays the same and the term gets shorter. You enter either:
  * an amount: the loan is repaid with the same payment, so it ends earlier (the last payment may be smaller), or
  * a number of periods `N` to cut (months for monthly payments, years for annual ones): the amount is derived as `balance − P · (1 − (1 + r)^−(m − N)) / r` (or `balance − P · (m − N)` if `r = 0`), where `m` is the number of remaining periods.

Rules:

* The amount must be > 0 and at most the outstanding balance after that period's payment. Repaying the whole balance cancels the loan.
* `N` must be ≥ 1 and at most the remaining periods.
* An amortization can't fall on a period after the loan is already paid off, including when earlier amortizations shortened the term.
* Editing the mortgage conditions (anything but the name) deletes its early amortizations, after a confirmation.
* There is no early-repayment fee.

With amortizations, the summary also shows the current payment per period, the total early amortized, the interest saved and how much the term was shortened, compared with the same mortgage without amortizations. Total interest and total amount paid include their effect.

#### Mortgage data

This is a separate view with the details of the saved mortgages. From this view you can switch the mortgage being viewed, edit or delete it, or compare several saved mortgages in a single table.

Single mortgage view:

* Descriptive name and conditions (TIN, duration, payment frequency).
* Loan amount.
* Mortgage percentage of the purchase price (`—` in mode B).
* Payment per period.
* Total interest paid.
* Total amount paid.
* Amortization table.

The amortization table has the next columns: Year (monthly payments only), Period, Payment, Interest, Principal (amortization payment), Early amortization, Outstanding balance (living capital) and Amortized capital. Monthly schedules show one year per page.

Multiple mortgage view:

The user selects two or more saved mortgages. A single table is shown with one column per mortgage and one row for each of the next values:

* Descriptive name.
* Mortgage duration (years).
* Interest rate (TIN).
* Payment frequency.
* Purchase price.
* Initial savings.
* Total initial expenses.
* Down payment (initial savings minus initial expenses).
* Loan amount.
* Mortgage percentage of the purchase price.
* Payment per period.

For mortgages entered in mode B, the purchase-related rows (purchase price, initial savings, initial expenses, down payment and percentage of the purchase price) show `—`.

### Future implementation

* Variable interest rate mortgages.
* Mixed interest rate mortgages.
* Desktop packaging (Linux and Windows installers).

## Rubit Finance loans module

Future definition.

## Rubit Finance investing module

Future definition.

## Rubit Finance savings module

Future definition.

## Implementation

The MVP is a **local web app**: a Nuxt frontend and a FastAPI backend, run on the user's machine (Linux and Windows). Packaging it as a desktop app is listed under [Future implementation](#future-implementation).

### Architecture

```
Nuxt 4 SPA  ──REST/JSON──▶  FastAPI  ──▶  SQLite
 (web/)                      (api/)
```

* All finance maths lives in a pure-Python domain package in the API, with no framework dependencies, so it can be unit-tested in isolation.
* Layers are kept separate (SOLID): `domain` (calculations and models), `persistence` (repository over SQLite), `api` (HTTP routers and schemas).
* The mortgage inputs are what gets stored. Derived data (payment, amortization table, totals) is computed on request.
* The SQLite database file lives in the OS app-data directory (for example with `platformdirs`).

### Repository layout

Monorepo:

```
rubit-finance/
├── api/                  # FastAPI backend
│   ├── pyproject.toml
│   ├── src/rubit/
│   │   ├── domain/       # mortgage maths, pure Python
│   │   ├── persistence/  # SQLModel models + repository
│   │   └── api/          # FastAPI app, routers, schemas
│   └── tests/
├── web/                  # Nuxt frontend
│   ├── app/              # pages, components, composables
│   └── ...
└── .github/workflows/
```

### API

Stack: Python 3.13, FastAPI, SQLModel (SQLite), managed with `uv`.

Endpoints:

| Method | Path                               | Description                                               |
|--------|------------------------------------|-----------------------------------------------------------|
| GET    | `/api/mortgages`                   | List saved mortgages, with their summary.                 |
| POST   | `/api/mortgages`                   | Create a mortgage.                                        |
| GET    | `/api/mortgages/{id}`              | Get the inputs, summary, totals and amortization table.   |
| PUT    | `/api/mortgages/{id}`              | Edit a mortgage.                                          |
| DELETE | `/api/mortgages/{id}`              | Delete a mortgage.                                        |
| GET    | `/api/mortgages/compare?ids=1,2,…` | Comparison rows for the selected mortgages.               |
| PUT    | `/api/mortgages/{id}/amortizations/{period}` | Create or replace the early amortization of a period. |
| DELETE | `/api/mortgages/{id}/amortizations/{period}` | Delete the early amortization of a period.   |

* Decimal amounts are serialized as strings to avoid losing precision.
* The OpenAPI schema is used to generate the TypeScript types for the frontend (`openapi-typescript`).

Checks (run from `api/`):

```sh
ruff check .
ruff format --check .
pyright
pytest -q
```

Tooling: `ruff` (lint and format), `pyright` in strict mode, `pytest` with `pytest-cov`. The domain package should have full test coverage of the calculations, including the reference example and the `r = 0` case.

### Webapp

Stack: Nuxt 4 in SPA mode (`ssr: false`), TypeScript strict, Nuxt UI, `@nuxtjs/i18n` (English only), managed with `pnpm`.

Pages:

| Route                   | Description                                      |
|-------------------------|--------------------------------------------------|
| `/`                     | List of saved mortgages.                         |
| `/mortgages/new`        | Configuration form (mode A or mode B).           |
| `/mortgages/[id]`       | Single mortgage view.                            |
| `/mortgages/[id]/edit`  | Edit form.                                       |
| `/compare`              | Select mortgages and show the comparison table.  |

* Amounts are formatted with `Intl.NumberFormat('en', { style: 'currency', currency: 'EUR' })`.

Checks (run from `web/`):

```sh
pnpm lint        # @nuxt/eslint
pnpm typecheck   # nuxi typecheck
pnpm test        # vitest + @nuxt/test-utils
```

### Running locally

* **Development:** run `uv run fastapi dev` in `api/` and `pnpm dev` in `web/`. Nuxt proxies `/api` to FastAPI (`nitro.devProxy`).
* **Production:** `pnpm generate` builds the static SPA. FastAPI serves it from `web/.output/public` next to the API on a single port, and `uv run rubit` starts the server and opens the app on `localhost`.

### CI/CD

GitHub Actions:

* `ci.yml`, on every pull request and push to `main`:
  * `api` job: `uv sync`, then the API checks above.
  * `web` job: `pnpm install`, then the web checks above.
* `release.yml`, on `main`: follows the release process in [CONTRIBUTING.md](CONTRIBUTING.md) (`python-semantic-release`, `-rc.N` prereleases, manual promotion to stable). Until desktop packaging exists, releases attach a zipped build (API + static SPA) instead of installers.

## Coding guidelines

* SOLID principles.
* Python: `ruff` for lint and format, `pyright` in strict mode.
* Web: ESLint (`@nuxt/eslint`) and TypeScript strict.
* Conventional Commits, GitHub Flow and the release process are described in [CONTRIBUTING.md](CONTRIBUTING.md).

### Known inconsistencies in CONTRIBUTING.md

To be fixed separately:

* It links to `README.md#development`, but there is no `README.md`. The development instructions are in [Implementation](#implementation) in this file.
* It mentions installers and a `website/` folder, which the MVP doesn't have (installers are deferred to desktop packaging).
