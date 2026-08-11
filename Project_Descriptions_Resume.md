# Project Descriptions for Resume
**Full-Stack Developer | 3+ Years Experience**

---

## CURRENT / ACTIVE PROJECTS

### 1. RiskAdjMain — Healthcare Risk Adjustment Platform
**Role:** Full-Stack Developer (Primary Contributor)

**Tech Stack:** 
- Frontend: React 18 + Vite + TypeScript + Tailwind CSS + Zustand (state management)
- Backend: Python + FastAPI + async SQLAlchemy 2.0 + PostgreSQL
- DevOps: Docker + GCP Cloud Run + Cloud Secret Manager
- Architecture: Multi-tenant SaaS

**Key Contributions:**
- Designed and implemented multi-tenant database architecture ensuring data isolation across clients
- Built real-time patient dashboard with risk score calculations and trend analytics
- Developed async API endpoints for patient inventory, quality metrics, and clinical data management
- Implemented JWT-based authentication with role-based access control (RBAC)
- Optimized complex database queries (10s → 200ms) using proper indexing and eager loading
- Deployed to GCP Cloud Run achieving auto-scaling (0-10 instances) and 70% cost reduction

**Impact:** Platform handles 100k+ patients across multiple healthcare organizations; automated risk score calculations saving 40 hours/month of manual work

---

### 2. QualityMetrics — Healthcare Quality Measure Platform
**Role:** Full-Stack Developer

**Tech Stack:**
- Frontend: React 18 + Vite + TypeScript + Tailwind CSS + Recharts (visualizations)
- Backend: Python + FastAPI + SQLAlchemy + PostgreSQL
- DevOps: Docker + docker-compose
- Features: Real-time dashboards, patient filtering, gap identification

**Key Contributions:**
- Built screening eligibility algorithm for colorectal/breast cancer and HbA1c testing
- Implemented patient gap identification and closure tracking workflows
- Created analytics dashboards showing care gap rates and closure trends by provider/clinic
- Optimized patient queries from 5s to 200ms using strategic indexing and eager loading
- Developed automated daily batch jobs for gap detection and reminder emails
- Built comprehensive filtering system (by condition, age, screening status, clinic)

**Impact:** Tracks quality metrics for 50k+ patients; improved cancer screening rates by identifying 2,000+ care gaps monthly

---

### 3. CoderScreen-RA — Medical Coder Screening Platform
**Role:** Full-Stack Developer

**Tech Stack:**
- Frontend: React + TypeScript + Tailwind CSS
- Backend: Python + FastAPI + Alembic (migrations) + PostgreSQL
- Features: Coder interface for ICD-10 coding, decision support, audit workflows

**Key Contributions:**
- Designed coder UI for reviewing claims and assigning diagnoses with real-time validation
- Built decision support engine suggesting ICD-10 codes based on documentation
- Implemented audit module for QA review and feedback loop
- Created coding accuracy metrics and performance dashboards
- Set up database migrations with Alembic for schema evolution

**Impact:** Reduced coding turnaround time by 30%; improved accuracy through decision support

---

### 4. LiveStreamPlatform (StreamHub) — Self-Hostable Video Platform
**Role:** Full-Stack Developer

**Tech Stack:**
- Frontend: React 18 + Vite + TypeScript + Tailwind CSS
- Backend: Python + FastAPI + async SQLAlchemy + PostgreSQL
- Storage: AWS S3 / MinIO (object storage)
- DevOps: Docker + docker-compose
- Features: User auth, video upload/streaming, creator studio, public feed

**Key Contributions:**
- Implemented chunked file upload with progress tracking and resume capability
- Built video streaming backend with S3 integration and CDN support
- Created creator studio with video management and basic analytics
- Implemented public feed with search, filtering, and pagination
- Set up Docker environment for local development and production deployment
- Designed schema for users, videos, metadata, and engagement tracking

**Impact:** Proof-of-concept platform demonstrating video hosting capabilities; supports uploads up to 4GB with reliable resumption

---

### 5. PVS (Pre-Visit Summary) — Clinical Summarization Tool
**Role:** Full-Stack Developer

**Tech Stack:**
- Frontend: React
- Backend: Python
- DevOps: Docker
- Purpose: Generate AI-powered pre-visit clinical summaries

**Key Contributions:**
- Developed backend service to aggregate patient medical history and generate summaries
- Built React UI for clinicians to review and customize pre-visit summaries
- Implemented integration with clinical data sources
- Automated summary generation reducing clinician prep time

**Impact:** Enables clinicians to quickly review patient history before appointments

---

## LEGACY / REFERENCE PROJECTS

### 6. VBC-HCC — Healthcare HCC Coding Application
**Role:** Developer

**Tech Stack:**
- Frontend: ASP.NET (Razor Pages / MVC)
- Backend: C# + .NET Framework
- Database: SQL Server
- Structure: Business/, CodingWeb/, CodingWeb.Test/, HCCTests/, Database/

**Purpose:**
Web application for healthcare organizations to manage ICD-10 to HCC code mapping, calculate patient risk adjustment factors (RAF), track coding accuracy, and generate compliance reports.

**Key Features:**
- Capture and validate ICD-10 diagnoses from claims
- Auto-map diagnoses to Hierarchical Condition Categories (HCC) codes with risk weights
- Calculate RAF (Risk Adjustment Factor) per patient
- Track coder performance and accuracy metrics
- Audit module for QA review and compliance
- Generate reports for CMS submission

**Technical Highlights:**
- Implemented HCC hierarchy logic (e.g., if both HCC-A and HCC-B apply, only count higher-weighted one)
- Created complex SQL stored procedures for RAF calculation
- Built role-based access control for coders, auditors, administrators

---

### 7. VBC-HCC-New — HCC Platform (Refactored Version)
**Role:** Developer

**Tech Stack:**
- Frontend: ASP.NET
- Backend: C# + .NET
- Database: SQL Server
- Architecture: Same as VBC-HCC with modernized patterns

**Purpose:**
Updated version of VBC-HCC with improved architecture, performance optimizations, and additional features for healthcare HCC management.

**Key Improvements Over VBC-HCC:**
- Refactored code organization for better maintainability
- Performance optimizations for large-scale patient processing
- Enhanced user interface and workflow
- Improved test coverage with unit and integration tests

---

### 8. QM-QA (QualityMetrics QA Environment)
**Role:** DevOps / QA Support

**Tech Stack:**
- Same as QualityMetrics (FastAPI + React + PostgreSQL)
- Purpose: QA and staging environment

**Responsibilities:**
- Maintained QA environment for testing before production deployment
- Configured test data and patient scenarios
- Supported QA team with environment setup and troubleshooting

---

### 9. POC-pdf-RA — PDF-Based Risk Adjustment Proof of Concept
**Role:** Developer

**Tech Stack:**
- Backend: Python
- Frontend: React
- Purpose: Explore PDF processing for risk adjustment workflows

**Objective:**
Proof-of-concept project to evaluate feasibility of extracting medical data from PDF documents (claims, lab results) for automated risk adjustment calculations.

**Key Learnings:**
- PDF parsing challenges (varied formats, OCR limitations)
- Integration of extracted data into risk adjustment pipeline
- Document validation and error handling

---

## TECHNICAL SKILLS REFERENCE

### By Tech Stack

**Python / FastAPI (Primary)**
- Async/await patterns with asyncio
- SQLAlchemy ORM with async support (SQLAlchemy 2.0)
- Pydantic for input validation
- Alembic for database migrations
- JWT authentication
- RESTful API design with OpenAPI/Swagger docs

**Frontend / React (Primary)**
- React 18 + Hooks (useState, useEffect, useContext, custom hooks)
- TypeScript for type safety
- Vite for fast bundling
- Tailwind CSS for styling
- Zustand for state management
- React Router for navigation
- Data visualization (Recharts)

**Databases**
- PostgreSQL: async queries, migrations, indexes, partitioning
- SQL Server: stored procedures, T-SQL, complex calculations
- Database design: normalization, relationships, constraints

**DevOps / Deployment**
- Docker: multi-stage builds, image optimization
- docker-compose: local development environments
- GCP Cloud Run: serverless deployment, auto-scaling
- Cloud Secret Manager for secure credential storage
- GitHub Actions / CI-CD pipelines

**Healthcare Domain**
- HCC (Hierarchical Condition Categories): ICD-10 mapping, RAF calculation
- Risk Adjustment: capitation models, CMS compliance
- Quality Metrics: HEDIS/MIPS standards, gap identification, care closure
- Medical Coding: ICD-10/CPT codes, audit workflows

---

## KEY ACHIEVEMENTS

✅ **Designed Multi-Tenant Architecture** for RiskAdjMain ensuring data isolation across clients and supporting 100k+ patients

✅ **Optimized Database Performance** reducing query time from 10s to 200ms through proper indexing and query design

✅ **Full-Stack Delivery** consistently shipping features from design through testing and production deployment

✅ **Healthcare Domain Expertise** gained through 3+ years building HCC, quality metrics, and risk adjustment platforms

✅ **Modern Tech Stack** proficiency in React 18, FastAPI, async Python, PostgreSQL, Docker, and cloud deployment

✅ **Code Quality** practices including unit/integration testing, code reviews, and maintaining clean, maintainable code

---

## TECHNOLOGY SUMMARY

**Languages:** Python, C#, TypeScript, JavaScript, SQL (PostgreSQL, SQL Server)

**Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Zustand, React Router, Recharts

**Backend:** FastAPI, ASP.NET, SQLAlchemy 2.0, Pydantic, async/await

**Databases:** PostgreSQL (primary), SQL Server, Alembic migrations

**DevOps:** Docker, docker-compose, GCP Cloud Run, GitHub Actions, Cloud Secret Manager

**Tools:** VS Code, Git, Figma (design collaboration), Postman (API testing)

**Methodology:** Agile, code review culture, test-driven development, continuous deployment

---

## PROJECT MATRIX

| Project | Backend | Frontend | Database | Domain |
|---------|---------|----------|----------|--------|
| RiskAdjMain | FastAPI | React 18 | PostgreSQL | Risk Adjustment (SaaS) |
| QualityMetrics | FastAPI | React 18 | PostgreSQL | Quality Metrics |
| CoderScreen-RA | FastAPI | React | PostgreSQL | Medical Coding |
| LiveStreamPlatform | FastAPI | React 18 | PostgreSQL | Video Streaming |
| PVS | Python | React | - | Clinical Summarization |
| VBC-HCC | C# .NET | ASP.NET | SQL Server | HCC Coding |
| VBC-HCC-New | C# .NET | ASP.NET | SQL Server | HCC Coding |

---

## CAREER HIGHLIGHTS

**3+ Years of Full-Stack Development** in healthcare technology, with deep expertise in:
- Building scalable, multi-tenant SaaS platforms
- Healthcare domain knowledge (HCC, risk adjustment, quality metrics)
- Modern Python/React stack with async best practices
- Cloud deployment and DevOps practices

**From Concept to Production:** Consistently took projects from initial requirements through design, implementation, testing, and deployment to cloud platforms supporting real healthcare organizations.

**Impact-Driven:** Projects directly improved workflows for healthcare professionals and administrators, reducing manual work, improving data quality, and supporting compliance.
