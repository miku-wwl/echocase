# EchoCase

**An Evidence-Driven Full-Stack Investigation Web Application**

**Project 2 — Master of Software Engineering Capstone**

## 1. Project Overview

EchoCase is a full-stack web application for investigating fictional cases, managing evidence, constructing evidence relationships, tracking investigation progress, and submitting evidence-based conclusions.

The investigation scenario serves as a practical domain for studying and applying enterprise software engineering principles.

**Primary goal:** Develop a deep understanding of full-stack application architecture, domain-driven design, database consistency, frontend state management, automated testing, and reliable software delivery.

This is a software engineering capstone project, not a game-development or AI demonstration project.

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Backend | C#, ASP.NET Core 10 |
| Architecture | Clean Architecture, DDD, CQRS |
| Project Foundation | Jason Taylor CleanArchitecture |
| Frontend | React 19, TypeScript, Vite |
| UI Components | Official shadcn/ui, Tailwind CSS |
| Interactive Graph | React Flow |
| Server State | TanStack Query |
| Database | PostgreSQL, Entity Framework Core |
| Backend Testing | NUnit, Integration Tests |
| Frontend Testing | Playwright |
| Containerization | Docker |
| Deployment | Azure |
| CI/CD | GitHub Actions |

Technology choices will be validated during the foundation phase.

## 3. Core Functional Scope

The initial version contains five business modules.

### 3.1 Case Management
- Browse available cases
- Start a new investigation
- View case information
- Resume an existing investigation

### 3.2 Evidence Management
- View and examine evidence
- Track discovered evidence
- Enforce evidence visibility and access rules

### 3.3 Evidence Linking
- Create relationships between evidence items
- Validate relationships against domain rules
- Visualize evidence using an interactive React graph

### 3.4 Investigation Progress
- Save and restore investigation state
- Track state transitions
- Handle concurrent modifications
- Prevent duplicate operations

### 3.5 Verdict Submission
- Submit conclusions supported by evidence
- Validate business invariants
- Persist final decisions
- Present deterministic evaluation results

**MVP:** One complete fictional case with enough evidence and rules to exercise the full application architecture.

## 4. Architecture Design

EchoCase follows Clean Architecture principles.

### Domain Layer
- Entities and Value Objects
- Aggregate Roots
- Business Invariants
- Investigation State Machine
- Domain Rules

### Application Layer
- Commands and Queries
- Use Case Handlers
- Validation
- Authorization
- Transaction Coordination

### Infrastructure Layer
- EF Core Persistence
- PostgreSQL
- Database Migrations
- External Service Adapters

### Presentation Layer
- ASP.NET Core Web API
- React and TypeScript
- shadcn/ui
- React Flow
- Typed API Client

Dependencies should point inward toward the core business logic.

## 5. Primary Technical Learning Objectives

### T1 — Clean Architecture & DDD
Study dependency inversion, aggregate design, domain invariants, application boundaries, and architectural trade-offs.

### T2 — EF Core & PostgreSQL
Study migrations, LINQ, transactions, indexes, optimistic concurrency, database constraints, and query performance.

### T3 — Advanced React Engineering
Study component design, TypeScript typing, local versus server state, optimistic updates, query invalidation, error handling, and complex interactive components.

### T4 — API Security & Data Consistency
Study authentication, resource-level authorization, idempotency, concurrency conflict handling, and secure API design.

### T5 — Testing & Software Quality
Study unit, functional, integration, architecture, and end-to-end tests, along with observability and performance measurement.

## 6. Engineering Experiments

| ID | Experiment |
|---|---|
| E01 | Clean Architecture dependency validation |
| E02 | Domain invariant and state transition testing |
| E03 | Database migration and data preservation |
| E04 | Optimistic concurrency conflict handling |
| E05 | Idempotent API operations |
| E06 | Resource authorization and security testing |
| E07 | React state synchronization and error recovery |
| E08 | PostgreSQL query performance benchmarking |
| E09 | Maintainability and architecture change analysis |
| E10 | Reproducible CI/CD and deployment |

Each experiment should include a hypothesis, implementation, reproducible procedure, observations, and conclusions.

## 7. Development Roadmap

### Stage 0 — Foundation & Template Dissection
- Initialize Jason Taylor CleanArchitecture
- Establish backend, frontend, and PostgreSQL
- Run existing tests
- Trace a complete API request
- Review dependency boundaries and third-party licenses
- Integrate official shadcn/ui

**Gate:** Reproducible baseline with passing tests.

### Stage 1 — Domain Engineering
- Design the investigation domain
- Implement InvestigationSession aggregate
- Define business invariants
- Implement investigation state transitions
- Write domain unit tests

**Gate:** Core domain behavior verified independently of infrastructure.

### Stage 2 — Persistence & API Engineering
- Design the PostgreSQL schema
- Implement EF Core mappings and migrations
- Develop commands, queries, and REST endpoints
- Implement concurrency and idempotency handling
- Test using a real database

**Gate:** Correct and repeatable backend behavior.

### Stage 3 — React Full-Stack Integration
- Build React pages with official shadcn/ui
- Integrate generated API clients
- Implement evidence visualization
- Implement TanStack Query server-state management
- Handle errors, retries, and conflicts

**Gate:** Complete functional frontend-to-database workflow.

### Stage 4 — Quality & Reliability Engineering
- Add security and authorization tests
- Add integration and Playwright E2E tests
- Benchmark critical database queries
- Introduce observability
- Configure Docker and CI/CD

**Gate:** Verified quality and reproducible deployment.

### Stage 5 — Capstone Technical Evaluation
- Evaluate architectural decisions
- Conduct engineering experiments
- Refactor based on measured evidence
- Document technical trade-offs
- Complete the final capstone report

**Gate:** Working application with reproducible technical evidence.

## 8. Explicit Non-Goals

The initial project will not include:

- Complex AI agents or autonomous NPCs
- AI-generated storylines
- 3D graphics or Unity integration
- Multiplayer functionality
- Microservices architecture
- Kubernetes-based production orchestration
- Multi-tenant SaaS capabilities
- Full Event Sourcing
- Complex branching narratives
- Extensive multimedia production

These features are excluded to preserve the project's software engineering learning objectives.

## 9. Definition of Done

The project will be considered complete when:

- The full-stack application runs from a clean environment
- All five core business modules work
- Domain invariants are verified by automated tests
- Database persistence and concurrency are validated
- Authorization boundaries are tested
- A complete investigation passes browser E2E testing
- CI/CD and deployment are reproducible
- Technical experiments and architectural decisions are documented

## 10. Documentation

Planned documents:

- `docs/requirements/PRD.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/decisions/`
- `docs/domain/DOMAIN-MODEL.md`
- `docs/api/API-DESIGN.md`
- `docs/testing/TEST-STRATEGY.md`
- `docs/experiments/`
- `docs/deployment/DEPLOYMENT.md`
- `docs/learning/LEARNING-JOURNAL.md`

## 11. Development Principles

1. Understand the technology before implementing major features.
2. Prefer explicit, testable domain behavior over framework complexity.
3. Keep business logic independent of infrastructure.
4. Measure engineering quality instead of claiming it.
5. Avoid unnecessary abstractions and premature optimization.
6. Use AI coding assistants to support implementation, not replace architectural understanding.
7. Document architectural decisions and lessons learned.
8. Clearly distinguish original contributions from third-party starter code.

## 12. Attribution

EchoCase plans to use Jason Taylor's CleanArchitecture as its initial project foundation.

Upstream repository:
https://github.com/jasontaylordev/CleanArchitecture

Third-party licenses, notices, and the distinction between inherited and original code will be documented as the project develops.

## 13. Project Status

**Status: Planning — Initial Repository Setup**

Implementation, testing, and deployment have not yet been completed.
