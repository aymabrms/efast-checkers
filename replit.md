# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.

The workspace now also includes a Python Streamlit prototype at the project root:
**SEC eFAST Checkers – AFS Validation and Figure Extraction MVP**. It is a SEC Philippines-oriented internal QA dashboard prototype for AFS validation, page review, structured figure extraction, reviewer corrections, historical company views, and ranking/research views.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)
- **Prototype app**: Python + Streamlit
- **Prototype storage**: SQLite (`data/sec_efast_checkers.sqlite`)
- **Prototype PDF handling**: PyMuPDF with pdfplumber fallback

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally
- `streamlit run app.py --server.port 5000` — run SEC eFAST Checkers prototype

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.

## SEC eFAST Checkers Editable Demo Content

- `config.py` — app labels, defaults, ranking metric options, file paths
- `demo_data.json` — sample AFS pages, validation rows, extracted figures, historical data, ranking data
- `label_mapping.json` — raw AFS labels mapped to normalized figure fields
- `revert_reasons.json` — reviewer revert reason dropdown values
- `sample_company_master.json` — fictional company master record for Audentia Fortuna Holdings, Inc.
