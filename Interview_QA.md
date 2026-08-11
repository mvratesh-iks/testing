# Interview Questions & Answers
**3+ Years Full-Stack Development Experience**

---

## GENERAL / BEHAVIORAL

### Q1: Tell me about your background and experience
**A:** I have 3+ years of full-stack software development experience, specializing in healthcare tech applications. I'm proficient in both backend (Python/FastAPI, C#/.NET) and frontend (React/TypeScript) technologies. My expertise spans building scalable web applications, designing multi-tenant architectures, and working with complex healthcare workflows. I've worked on production systems handling patient data, risk adjustment algorithms, and clinical quality metrics, requiring strong understanding of healthcare domain logic, data security, and compliance.

### Q2: What's your strongest technology and why?
**A:** Python/FastAPI for backend development. I've built multiple production microservices with async/await patterns, SQLAlchemy 2.0 ORM, and database migrations using Alembic. I appreciate FastAPI's automatic OpenAPI documentation, strong typing with Pydantic, and built-in async support. I've also worked extensively with React/TypeScript on the frontend, building component-driven UIs with state management (Zustand), routing, and real-time features.

### Q3: Describe a challenging project you worked on
**A:** RiskAdjMain was my most complex project—a multi-tenant SaaS platform for healthcare risk adjustment. Challenges included:
- Designing a multi-tenant database schema ensuring data isolation
- Implementing JWT-based authentication with role-based access control
- Building async workflows for inventory/quality management with proper error handling
- Deploying to GCP Cloud Run with auto-scaling and monitoring
- Coordinating async backend tasks with frontend state management (Zustand)
I solved these by studying multi-tenant architecture patterns, implementing proper database indexing for tenant filtering, and using containerization for reliable deployments.

### Q4: Tell me about a time you debugged a production issue
**A:** In the QualityMetrics application, users reported missing data in cancer screening summaries. I investigated by:
1. Checking database queries and patient filtering logic
2. Reviewing the ETL pipeline for data gaps
3. Tracing the React component state and API response payloads
4. Found the issue: a race condition where async data fetches weren't properly sequenced
I fixed it by implementing proper Promise chaining and loading states, and added logging to catch similar issues early.

### Q5: How do you approach learning new technologies?
**A:** I learn by doing. When starting with Docker, I containerized the LiveStreamPlatform project—reading docs, writing Dockerfile/docker-compose.yml, testing locally, then deploying. For Vite, I migrated a React project from Create React App, learning bundler configuration and hot module replacement. I supplement hands-on work with documentation, open-source code review, and asking experienced colleagues.

### Q6: Describe your experience with code reviews
**A:** I've both given and received code reviews. As a reviewer, I focus on:
- Logic correctness and edge cases
- Code clarity and maintainability
- Security (SQL injection, XSS, auth checks)
- Performance (N+1 queries, unnecessary re-renders)
As an author, I write clear commit messages, self-review before requesting review, and incorporate feedback gracefully. I see reviews as collaboration, not criticism.

---

## BACKEND / PYTHON / FASTAPI

### Q7: Explain your FastAPI architecture
**A:** My typical FastAPI structure:
```
backend/
├── main.py (app initialization, middleware, CORS)
├── config.py (environment variables, database URL)
├── database.py (SQLAlchemy engine, session management)
├── models/ (SQLAlchemy ORM models)
├── schemas/ (Pydantic request/response schemas)
├── routes/ (API endpoints organized by feature)
├── services/ (business logic, database queries)
├── middleware/ (auth, logging, error handling)
└── migrations/ (Alembic)
```
Pydantic validates requests, SQLAlchemy manages ORM, async functions improve concurrency. I separate endpoints (routes) from business logic (services) for testability.

### Q8: How do you handle database migrations?
**A:** I use Alembic (SQLAlchemy migration tool):
1. Define ORM models in SQLAlchemy
2. Run `alembic revision --autogenerate -m "description"` to detect changes
3. Review generated migration file for correctness
4. Run `alembic upgrade head` to apply
5. Version control migrations with code
This ensures database schema is tracked and deployable. For RiskAdjMain, I've handled multi-tenant schema migrations carefully to avoid data loss.

### Q9: Describe your async/await experience
**A:** I use async heavily in FastAPI:
- `async def` for route handlers that call async database operations
- `await` for I/O-bound work (database queries, API calls, file uploads)
- AsyncSession from SQLAlchemy 2.0 for non-blocking database access
- `asyncio.gather()` to run multiple async tasks concurrently
For example, in RiskAdjMain's inventory endpoint, I fetch patient data, quality metrics, and risk scores in parallel using `gather()` rather than sequential awaits, improving response time by 3x.

### Q10: How do you structure database queries for performance?
**A:** 
- Use ORM joins instead of multiple queries (avoid N+1)
- Index frequently filtered columns (tenant_id, user_id, created_at)
- Use pagination for large result sets
- Eager load relationships with SQLAlchemy's `joinedload()` or `selectinload()`
- Profile slow queries with `EXPLAIN ANALYZE` in PostgreSQL
- Cache non-changing data (reference tables) in memory or Redis
For QualityMetrics, I optimized screening queries from 5s to 200ms by adding indexes and eager loading patient demographics.

### Q11: Explain authentication flow in your projects
**A:** 
- User logs in with email/password
- Backend validates credentials, generates JWT token (HS256 or RS256)
- Frontend stores token in localStorage/sessionStorage
- Each request includes Authorization header: `Bearer <token>`
- Backend middleware decodes JWT, validates expiry, extracts user/claims
- Role-based access control (RBAC) checks user permissions
In RiskAdjMain, I implemented this with FastAPI's `Depends()` for dependency injection, ensuring protected routes validate tokens and check tenant membership.

### Q12: How do you handle errors and logging?
**A:** 
- Create custom exception classes inheriting from HTTPException
- Log with Python's logging module (console in dev, file/cloud in prod)
- Include context: user ID, request ID, timestamp, stack trace
- Return structured JSON errors: `{"detail": "...", "error_code": "...", "request_id": "..."}`
- For debugging, use correlation IDs to trace requests across microservices
Example:
```python
try:
    patient = await db.query(Patient).filter_by(id=id).first()
except Exception as e:
    logger.error(f"Failed to fetch patient {id}: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")
```

### Q13: How do you secure APIs?
**A:** 
- HTTPS/TLS for all traffic (enforced in production)
- JWT for stateless authentication
- CORS configured to allow only trusted origins
- SQL parameterized queries (SQLAlchemy prevents SQL injection)
- Input validation with Pydantic (type checking, constraints)
- Rate limiting on sensitive endpoints (login, password reset)
- Hash passwords with bcrypt, never store plaintext
- Validate JWT expiry, refresh token rotation
- Log security events (failed logins, unauthorized access)

### Q14: Explain multi-tenant architecture challenges
**A:** Multi-tenant means multiple customers share infrastructure. Challenges:
- **Data isolation**: Ensure tenant A can't see tenant B's data. Solution: filter all queries by `tenant_id`
- **Performance**: One tenant's load shouldn't slow others. Solution: proper indexing, query optimization
- **Schema design**: Shared schema vs. separate schemas. I use shared schema (one table, filtered by tenant_id) for simplicity
- **Billing/Quotas**: Track usage per tenant. Solution: audit logs, usage counters
- **Migration complexity**: Deploying schema changes across all tenants safely
RiskAdjMain handles this by checking `request.user.tenant_id` in every query, enforcing it at the service layer.

### Q15: How do you test backend code?
**A:** 
- Unit tests for business logic (services) with mocked database
- Integration tests with real test database
- Use `pytest` with fixtures for setup/teardown
- Mock external services (S3, email) to avoid side effects
- Test happy paths, edge cases, error handling
- Aim for >80% coverage on critical paths
Example:
```python
@pytest.mark.asyncio
async def test_create_patient(db_session):
    patient = await create_patient(db_session, name="John", age=45)
    assert patient.id is not None
    assert patient.name == "John"
```

---

## FRONTEND / REACT / TYPESCRIPT

### Q16: Describe your React component structure
**A:** I use functional components with hooks:
```
src/
├── components/
│   ├── common/ (Button, Modal, Input - reusable UI)
│   ├── features/ (Patient, Risk, Quality - domain components)
│   └── layout/ (Header, Sidebar, Footer)
├── pages/ (route pages)
├── hooks/ (custom hooks for logic)
├── store/ (Zustand state management)
├── services/ (API calls)
├── utils/ (helpers, formatters)
├── types/ (TypeScript interfaces)
└── App.tsx
```
Each component is single-responsibility, props are typed, state is centralized with Zustand. I prefer composition over inheritance.

### Q17: Explain your state management approach
**A:** I use Zustand for global state:
```typescript
const useRiskStore = create((set) => ({
  risks: [],
  setRisks: (risks) => set({ risks }),
  addRisk: (risk) => set((state) => ({
    risks: [...state.risks, risk]
  }))
}));
```
Advantages: minimal boilerplate, easy to use, no provider wrapper needed. Local component state with `useState` for UI state (form inputs, modals). Zustand for shared data (user, patients, risks).

### Q18: How do you handle API calls in React?
**A:** 
- Create `services/api.ts` with axios or fetch
- Use custom hooks like `useFetch(url)` or `useQuery()` (from react-query)
- Handle loading, error, success states
- Cache responses to avoid duplicate requests
- Include auth tokens in headers
Example:
```typescript
const usePatients = () => {
  const [data, setData] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetch('/api/patients', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json()).then(setData).finally(() => setLoading(false));
  }, []);
  
  return { data, loading };
};
```

### Q19: Explain TypeScript benefits you've experienced
**A:** 
- **Catch errors early**: Type checking at compile time prevents runtime errors
- **Better IDE support**: Autocomplete, refactoring, navigation
- **Self-documenting code**: Props and return types are explicit
- **Refactoring confidence**: Change a type, compiler tells you what breaks
- **Team communication**: Types serve as contracts between functions
I've caught bugs (wrong parameter types, missing fields) before running code. On RiskAdjMain, switching to TypeScript reduced production bugs by ~40%.

### Q20: How do you optimize React performance?
**A:** 
- **Memoization**: `React.memo()` for expensive components
- **useCallback/useMemo**: Prevent unnecessary function/object recreation
- **Code splitting**: `React.lazy()` and `Suspense` for large bundles
- **Virtual scrolling**: For long lists, render only visible items
- **Debouncing**: Expensive operations (search) with debounce
- **Lighthouse audits**: Identify bottlenecks
Example: QualityMetrics list with 10k patients needed virtual scrolling. I used `react-window`, reducing render time from 3s to 300ms.

### Q21: Explain your experience with CSS frameworks
**A:** I use **Tailwind CSS** extensively:
- Utility-first approach: compose styles with classes
- No naming conflicts, consistent spacing/colors
- Responsive design: `md:flex`, `lg:grid` for breakpoints
- Easy dark mode support
- Smaller CSS bundles than Bootstrap
For LiveStreamPlatform, I styled the video feed, upload form, and creator dashboard entirely with Tailwind, achieving a polished look without custom CSS.

### Q22: How do you handle forms in React?
**A:** 
- Controlled components: store form state in component state or Zustand
- Validation: client-side (immediate feedback) + server-side (security)
- Libraries: `react-hook-form` for complex forms (less re-renders), `formik` for simpler cases
Example with react-hook-form:
```typescript
const { register, handleSubmit, errors } = useForm();
const onSubmit = (data) => api.createPatient(data);
<input {...register('name', { required: true })} />
{errors.name && <span>Required</span>}
```

### Q23: Describe your experience with routing
**A:** I use **React Router v6**:
- Define routes in `App.tsx` or nested route configs
- `<BrowserRouter>`, `<Routes>`, `<Route path="/patients/:id" element={<PatientDetail/>} />`
- `useNavigate()` for programmatic navigation
- `useParams()` to access route parameters
- Lazy load pages for code splitting
- Protected routes: wrap with auth check
```typescript
<Route element={<ProtectedRoute />}>
  <Route path="/dashboard" element={<Dashboard />} />
</Route>
```

### Q24: How do you debug React issues?
**A:** 
- React DevTools browser extension: inspect component hierarchy, props, state
- Console logs strategically (not everywhere)
- Debugger: set breakpoints in Chrome DevTools
- Network tab: inspect API requests/responses
- Performance tab: identify re-render issues
- Browser DevTools Lighthouse: audit performance
For a bug in RiskAdjMain where risk scores weren't updating, I used React DevTools to trace state changes in Zustand, found the action wasn't being called, fixed the button onClick handler.

---

## DATABASE / SQL

### Q25: Compare PostgreSQL and SQL Server
**A:** 
| Aspect | PostgreSQL | SQL Server |
|--------|------------|-----------|
| Cost | Open-source, free | Commercial, licensing $ |
| JSON support | Excellent (JSONB) | Good |
| Async drivers | asyncpg (Python), excellent | Requires libraries |
| Full-text search | Native, powerful | Built-in, good |
| Extensions | 100+ available | Limited |
| Stored procedures | PL/pgSQL | T-SQL |
I used PostgreSQL for Python/FastAPI projects (better async support), SQL Server for C#/.NET (native integration).

### Q26: Explain your database design approach
**A:** 
- Normalize to 3NF for most tables (avoid redundancy)
- Denormalize strategically for performance (materialized views, audit tables)
- Primary keys: use auto-increment (serial) or UUID
- Foreign keys: enforce referential integrity
- Indexes: on frequently searched/joined columns
- Partitioning: for large tables (by date, tenant_id)
For QualityMetrics with 100k patients, I partitioned by year and indexed patient_id + screening_date, improving query speed 10x.

### Q27: What's your experience with stored procedures?
**A:** 
- Write in SQL Server (T-SQL) or PostgreSQL (PL/pgSQL)
- Use for complex business logic, batch operations
- Parameters for input/output
- Transactions for multi-step operations
Example: risk adjustment calculation stored procedure
```sql
CREATE PROCEDURE CalculateHCC (@PatientId INT, @Year INT)
AS BEGIN
  SELECT diagnosis, hcc_code, weight INTO @results
  FROM Diagnoses d
  JOIN HCCMapping h ON d.code = h.icd_code
  WHERE d.patient_id = @PatientId AND d.year = @Year;
END;
```
I use them sparingly—ORMs (SQLAlchemy) are preferred for maintainability.

### Q28: Explain indexing strategy
**A:** 
- Single-column indexes on WHERE, JOIN, ORDER BY columns
- Composite indexes for queries filtering on multiple columns: `INDEX(tenant_id, created_at)` if querying both
- Avoid over-indexing: write performance degrades
- Monitor unused indexes, drop them
- Use `EXPLAIN ANALYZE` to verify index usage
For RiskAdjMain: added INDEX(tenant_id, user_id) on the patient table, halved query time for user's patient list.

### Q29: How do you handle transactions?
**A:** 
- ACID properties: Atomicity, Consistency, Isolation, Durability
- Use transactions for multi-step operations that must succeed/fail together
```python
async with db.begin():
    patient = await db.execute(insert(Patient).values(...))
    await db.execute(insert(PatientHistory).values(...))
    # If second insert fails, both rollback
```
Isolation level: READ_COMMITTED (default) for most cases, SERIALIZABLE for financial operations.

### Q30: Describe backup and recovery strategy
**A:** 
- Full backup daily (overnight)
- Transaction log backups hourly (enables point-in-time recovery)
- Store backups off-site (cloud storage, separate datacenter)
- Test recovery regularly (restore to staging, verify)
- Monitor backup job success/failure
- For PostgreSQL: `pg_dump` for logical backups, WAL archiving for continuous backups
For production systems, I ensured backups were automated and tested monthly.

---

## DEVOPS / DEPLOYMENT / DOCKER

### Q31: Explain your Docker experience
**A:** 
- Write Dockerfile: base image, dependencies, code copy, command
- Minimize layers: combine RUN commands
- Use multi-stage builds to reduce image size
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
CMD ["uvicorn", "main:app"]
```
- Tag images: `myapp:1.0`, `myapp:latest`
- Push to registry (Docker Hub, ECR, GCR)

### Q32: Describe docker-compose usage
**A:** 
- Define multi-container app: backend, database, cache, frontend
```yaml
version: '3'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db]
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/app
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: pass
```
- `docker-compose up`: start all services
- `docker-compose down`: stop and remove
I used this for local development in LiveStreamPlatform and QualityMetrics—matches production setup.

### Q33: Explain your GCP Cloud Run deployment
**A:** 
- Containerize app (Dockerfile)
- Build image: `gcloud builds submit --tag gcr.io/project/app`
- Deploy: `gcloud run deploy app --image gcr.io/project/app --region us-central1`
- Cloud Run auto-scales: 0 to 1000 instances based on traffic
- Pay only for used CPU/memory
- Set environment variables, secrets (Cloud Secret Manager)
For RiskAdjMain, I deployed the FastAPI backend to Cloud Run, achieving auto-scaling and reducing idle costs by 70%.

### Q34: How do you manage environment variables?
**A:** 
- `.env` file locally (not in git)
- `.env.example` in git with dummy values
- Production: manage with:
  - GCP Cloud Secret Manager
  - AWS Secrets Manager
  - Kubernetes ConfigMaps
- Load in code: `os.getenv('DATABASE_URL')`
- Use `python-dotenv` for local development
Never commit secrets!

### Q35: Describe CI/CD experience
**A:** 
- Write `.github/workflows` (GitHub Actions) or similar
- On push: run tests, lint, build Docker image
- On PR: run checks, report results
- On merge to main: deploy to staging, run smoke tests, deploy to production
Example workflow:
```yaml
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pip install -r requirements.txt
      - run: pytest
      - run: docker build -t app .
```

---

## HEALTHCARE DOMAIN

### Q36: Explain HCC (Hierarchical Condition Categories)
**A:** HCC is a risk adjustment model used in healthcare for:
- **Purpose**: Predict patient healthcare costs based on diagnoses
- **How it works**: ICD-10 diagnoses map to HCC codes, each with a risk weight (e.g., diabetes = HCC 22, weight 0.289)
- **Calculation**: RAF (Risk Adjustment Factor) = sum of patient's HCC weights
- **Use**: CMS uses it for Medicare Advantage plan payments
In VBC-HCC projects, I coded business logic to:
- Parse ICD-10 codes from claims
- Map to HCC codes (with age/gender adjustments)
- Aggregate into a patient RAF score
- Handle coding hierarchies (if HCC A and HCC B both apply, only higher-weighted one counts)

### Q37: What's Risk Adjustment in healthcare?
**A:** Risk Adjustment compensates health plans/providers for treating sicker patients:
- **Problem**: Plans treating sicker patients incur higher costs. Without adjustment, they'd go bankrupt.
- **Solution**: CMS calculates each patient's risk score (RAF) based on diagnoses/conditions
- **Payment**: Plans receive higher capitation payments for sicker members
- **Importance**: Incentivizes treating all patients (including sick ones) vs. cherry-picking healthy ones
RiskAdjMain platform automates this: capture diagnoses, calculate RAF, report to CMS, manage submissions.

### Q38: Explain quality metrics in healthcare (HEDIS/MIPS)
**A:** Quality metrics measure how well providers deliver care:
- **HEDIS** (Healthcare Effectiveness Data and Information Set): insurance metrics (e.g., % diabetics getting HbA1c test)
- **MIPS** (Merit-Based Incentive Payment System): clinician metrics
- **Examples**: Colorectal cancer screening rate, breast cancer screening rate, diabetic HbA1c control
QualityMetrics project tracks these:
- Identify eligible patients (age, conditions)
- Check if they completed required care (screening, testing)
- Calculate "gap closure" (% who completed care)
- Report to CMS/payers
I implemented algorithms to identify gaps and suggest interventions.

### Q39: What's a gap closure in healthcare?
**A:** Gap closure = closing a care gap (missing preventive care):
- **Gap**: Patient due for screening/testing but hasn't completed it
- **Gap closure**: Patient completes the care (e.g., gets colonoscopy)
- **Workflows**: Send reminder, schedule appointment, provider performs care
QualityMetrics project included:
- Gap identification: query patients due for screening
- Patient engagement: email/SMS reminders
- Tracking: record when care is delivered
- Reporting: calculate closure rates

### Q40: Explain medical coding challenges
**A:** 
- **Accuracy**: ICD-10 has 70k+ codes, easy to code wrong or miss codes
- **Compliance**: coded diagnoses must be documented, not assumed
- **Appeal risk**: under-coding costs money, over-coding invites audits
- **Training**: coders need ongoing education on new codes
- **Volume**: large provider organizations code 1000s of claims/day
VBC-HCC and CoderScreen-RA addressed this:
- Coder interface to review claims and assign codes
- Decision support: suggest codes based on documentation
- Audit: flag suspicious patterns (missing codes, age-inappropriate diagnoses)
- Education: feedback to improve coder accuracy

---

## PROJECTS DEEP DIVE

### Q41: Tell me about RiskAdjMain architecture
**A:** 
**Frontend** (React 18 + Vite + Zustand + TypeScript):
- Dashboard: real-time KPIs, patient counts, RAF trends
- Patient manager: search, filter by conditions/risk, review RAF
- Quality module: gap identification, closure tracking
- Admin: user/tenant management

**Backend** (FastAPI + async SQLAlchemy 2.0 + PostgreSQL):
- Multi-tenant: all queries filter by tenant_id
- Auth: JWT tokens, role-based access
- APIs: RESTful with OpenAPI docs
  - `/patients`: CRUD patients, calculate RAF
  - `/quality/gaps`: identify gaps, track closures
  - `/inventory`: manage claims/diagnoses
  - `/analytics`: dashboards data
- Async: concurrent database queries, external API calls
- Database: 
  - Patients, Diagnoses, Claims (indexed by tenant_id, patient_id)
  - HCC mappings (reference table)
  - Audit logs (compliance)

**Deployment** (GCP Cloud Run):
- Auto-scales to 0-10 instances
- PostgreSQL Cloud SQL (managed, backed up)
- Cloud Secret Manager for credentials
- Load balancer for HTTPS

**Key features**:
- Multi-tenant isolation
- Real-time analytics
- Batch imports (claims files)
- Email notifications
- Export reports (PDF, CSV)

### Q42: Describe LiveStreamPlatform
**A:** 
A self-hostable YouTube-like video platform:

**Features**:
- User signup/login with email verification
- Video upload (chunked, progress tracking) to S3/MinIO
- Public feed: browse creator videos, search, filter by category
- Creator studio: manage uploaded videos, analytics, monetization settings
- Comments, likes, subscriptions
- Admin dashboard: monitor platform, manage users

**Stack**:
- Frontend: React 18 + Vite + Tailwind + TypeScript
- Backend: FastAPI + async SQLAlchemy
- Database: PostgreSQL 16
- Storage: AWS S3 (production) or MinIO (self-hosted)
- Deployment: Docker

**Key technical aspects**:
- Chunked file upload: resume capability, progress UI
- Transcoding: convert uploaded videos to multiple resolutions (async task queue)
- CDN: serve videos from S3 CloudFront
- Scaling: stateless backend, database as bottleneck (optimized queries)

### Q43: Tell me about QualityMetrics project
**A:** 
Healthcare quality measure tracking and gap closure platform.

**Purpose**:
- Track cancer screenings (colorectal, breast)
- Monitor HbA1c testing for diabetics
- Identify patients with care gaps
- Automate gap closure workflows

**Features**:
- Patient lists: filter by screening status, condition, age
- Gap identification: show who's overdue for screening
- Patient engagement: send reminders, schedule appointments
- Reporting: gap rates, closure rates, trends by clinic/provider
- Historical tracking: see performance over time

**Technical**:
- FastAPI backend with complex business logic (screening eligibility, gap detection)
- React frontend with interactive dashboards (Recharts for visualizations)
- PostgreSQL with smart indexing (handle 100k+ patients efficiently)
- Docker for local dev and production
- Automated daily job: run gap detection, send reminders

### Q44: Explain VBC-HCC project
**A:** 
.NET/C# HCC coding and audit web application for healthcare coding teams.

**Purpose**:
- Capture medical diagnoses from claim documents
- Auto-map to HCC codes
- Calculate patient RAF (Risk Adjustment Factor)
- Track coding accuracy, audit results
- Report to CMS

**Features**:
- Coder interface: review claims, assign ICD-10 codes
- Decision support: AI-powered suggestions based on documentation
- Audit module: QA team reviews coder work, flags errors
- Reporting: coding accuracy metrics, HCC capture rates
- User management: roles (coder, auditor, admin)

**Stack**:
- Frontend: ASP.NET Razor Pages or MVC
- Backend: C# business logic, stored procedures
- Database: SQL Server with HCC lookup tables
- Structure: Business/ (logic), CodingWeb/ (UI), HCCTests/ (unit tests), Database/ (schema, sprocs)

---

## SOFT SKILLS / SITUATIONAL

### Q45: Describe how you handle technical debt
**A:** 
I balance shipping features with code quality:
- **Identify**: code review, refactoring, testing coverage gaps
- **Prioritize**: only fix high-impact (frequently used, causing bugs) debt
- **Schedule**: allocate ~20% of sprint capacity to debt reduction
- **Prevent**: enforce code standards in PR reviews, write tests upfront
Example: In RiskAdjMain, I noticed 5 places with duplicate query logic. I extracted into a shared service, reducing lines and bugs, completed in 1 day with 0 production impact.

### Q46: Tell me about a mistake you made and learned from
**A:** 
Early in CoderScreen-RA, I didn't validate user input properly on a medical coder screening endpoint. A user passed invalid ICD-10 codes, causing the backend to crash. I learned:
- Always validate input, even from "trusted" internal users
- Use Pydantic to enforce schema
- Add logging for debugging
- Write integration tests for edge cases
- Document assumptions
I fixed it and added input validation + tests. No recurrence.

### Q47: How do you stay updated with tech trends?
**A:** 
- Read: blogs (Real Python, FastAPI docs), GitHub trending
- Hands-on: try new tools in side projects
- Community: attend meetups, follow Twitter/Reddit
- Colleagues: learn from code reviews, pair programming
- Courses: structured learning for new areas (e.g., GCP for Cloud Run)

### Q48: Describe a time you mentored or helped a colleague
**A:** 
I helped a junior developer struggling with async Python. I:
- Explained event loop, coroutines, await semantics
- Shared examples from RiskAdjMain codebase
- Pair-programmed, walked through debugging
- Recommended learning resources
They became comfortable with async, now writes async code confidently. Helping others solidified my own understanding.

### Q49: How do you handle tight deadlines?
**A:** 
- **Prioritize**: focus on MVP, defer nice-to-haves
- **Communicate**: flag risks early, adjust expectations
- **Efficiency**: reduce context switching, focus time
- **Automation**: use scripts, templates to save time
- **Help**: ask for support if overwhelmed
Example: QualityMetrics report feature due in 3 days. I:
- Built basic report (table, CSV export), tested thoroughly
- Deferred charts/advanced filtering to next sprint
- Delivered on time, quality intact

### Q50: Why should we hire you?
**A:** 
I bring 3+ years of full-stack experience in healthcare tech, with proven ability to:
- Ship production features end-to-end (design, code, test, deploy)
- Work independently and in teams
- Write clean, maintainable, secure code
- Learn new technologies quickly
- Understand healthcare domain logic (HCC, quality metrics, coding)
- Deliver on tight deadlines without sacrificing quality
I'm looking for a role where I can contribute immediately and grow as an engineer.

---

## CODING / TECHNICAL CHALLENGES

### Q51: Optimize a slow query
**Problem**: List all patients for a tenant, with their latest risk score. Query takes 10s for 10k patients.

```sql
-- Slow (N+1)
SELECT * FROM patients WHERE tenant_id = ?;
FOR EACH patient:
  SELECT * FROM risk_scores WHERE patient_id = ? ORDER BY created_at DESC LIMIT 1;
```

**Solution**:
```sql
SELECT p.*, rs.score
FROM patients p
LEFT JOIN LATERAL (
  SELECT score FROM risk_scores
  WHERE patient_id = p.id
  ORDER BY created_at DESC LIMIT 1
) rs ON true
WHERE p.tenant_id = ?;
```
- Use LATERAL join for latest relationship
- Single query instead of N+1
- Add index: `(patient_id, created_at DESC)`
- Result: 10s → 200ms

### Q52: Implement a feature: gap closure workflow
**Requirements**:
1. Identify patients due for cancer screening
2. Send email reminder
3. Track if they complete care
4. Report closure rate

```python
# FastAPI endpoint
@app.post("/quality/identify-gaps")
async def identify_gaps(tenant_id: str, db: AsyncSession):
    # Find patients overdue for screening
    gaps = await db.execute(
        select(Patient)
        .where(Patient.tenant_id == tenant_id)
        .where(Patient.last_screening < today() - timedelta(days=365))
    )
    
    for patient in gaps.scalars():
        # Send reminder
        await send_email(patient.email, "Time for screening")
        
        # Log gap
        await db.execute(
            insert(GapLog).values(
                patient_id=patient.id,
                gap_type='screening',
                created_at=now()
            )
        )
    
    await db.commit()
    return {"gaps_identified": len(gaps.scalars())}

# Track closure
@app.post("/quality/close-gap/{gap_id}")
async def close_gap(gap_id: str, db: AsyncSession):
    gap = await db.get(GapLog, gap_id)
    gap.closed_at = now()
    await db.commit()
    return gap

# Report closure rate
@app.get("/quality/closure-rate")
async def closure_rate(tenant_id: str, db: AsyncSession):
    result = await db.execute(
        select(
            func.count(GapLog.id).filter(GapLog.closed_at != None) / func.count(GapLog.id)
        )
        .where(GapLog.tenant_id == tenant_id)
    )
    return {"closure_rate": result.scalar()}
```

---

## PROJECT FLOWS & ARCHITECTURE

This section provides visual flows and architecture diagrams you can reference and explain during interviews.

---

### PROJECT 1: RiskAdjMain — Multi-Tenant Risk Adjustment Platform

**System Architecture Overview:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                        RISK ADJUSTMENT PLATFORM                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐         ┌──────────────────┐                  │
│  │   React Frontend │         │   React Frontend │                  │
│  │  (Tenant A)      │         │  (Tenant B)      │                  │
│  │ • Dashboard      │         │ • Dashboard      │                  │
│  │ • Patients List  │         │ • Patients List  │                  │
│  │ • Quality Gaps   │         │ • Quality Gaps   │                  │
│  └────────┬─────────┘         └────────┬─────────┘                  │
│           │                            │                             │
│           │     HTTPS / JWT Auth       │                             │
│           ▼                            ▼                             │
│  ┌────────────────────────────────────────────┐                     │
│  │     FastAPI Backend (Cloud Run)            │                     │
│  │  • /patients (CRUD, RAF calculation)       │                     │
│  │  • /quality/gaps (identify gaps)           │                     │
│  │  • /analytics (dashboard data)             │                     │
│  │  • /auth (JWT token management)            │                     │
│  │  • Middleware: tenant_id validation        │                     │
│  └────────┬─────────────────────────────────┘                       │
│           │                                                          │
│           │    Async SQLAlchemy Queries                             │
│           ▼                                                          │
│  ┌────────────────────────────────────────────┐                     │
│  │   PostgreSQL Cloud SQL (Multi-Tenant DB)   │                     │
│  │  Tables:                                   │                     │
│  │  • patients (tenant_id PK)                 │                     │
│  │  • diagnoses (icd_code, patient_id)        │                     │
│  │  • risk_scores (raf, patient_id)           │                     │
│  │  • quality_gaps (screening_due, status)    │                     │
│  │  • hcc_mappings (icd→hcc conversion)       │                     │
│  │  • audit_logs (compliance tracking)        │                     │
│  └────────────────────────────────────────────┘                     │
│                                                                       │
│  ┌────────────────────────────────────────────┐                     │
│  │  GCP Cloud Storage                         │                     │
│  │  • Backup files, audit trails              │                     │
│  │  • Secret Manager (DB credentials)         │                     │
│  └────────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Patient Data Flow (RAF Calculation):**
```
1. USER UPLOADS CLAIMS FILE (CSV)
   ├─ Frontend: File selection & upload
   └─ Backend: `/api/patients/bulk-import` endpoint

2. BACKEND PROCESSING
   ├─ Parse CSV (patient_id, diagnoses, dates)
   ├─ Validate ICD-10 codes
   └─ For each patient:
      ├─ Extract diagnoses
      ├─ Query HCC mapping table (ICD → HCC)
      ├─ Apply HCC hierarchy (keep only highest weight)
      ├─ SUM HCC weights = RAF
      └─ Store in risk_scores table

3. STORE IN DATABASE
   ├─ INSERT patients (if new)
   ├─ INSERT diagnoses (link to patient)
   ├─ INSERT risk_scores (RAF per patient)
   └─ INSERT audit_log (who, when, what changed)

4. FRONTEND DASHBOARD DISPLAY
   ├─ Query `/api/analytics/dashboard?tenant_id=X`
   ├─ Receive: patient_count, avg_raf, trends
   └─ Render: KPI cards, charts (Recharts)

5. QUALITY METRICS FLOW
   ├─ Identify patients DUE for screening
   ├─ Query: WHERE last_screening < (today - 365 days)
   ├─ Store in quality_gaps table
   └─ Send email reminders (async task)

6. GAP CLOSURE TRACKING
   ├─ User marks screening as COMPLETED
   ├─ UPDATE quality_gaps SET closed_at = now()
   └─ Dashboard shows: closure_rate = closed/total
```

**Multi-Tenant Isolation (Critical):**
```
Every query enforces tenant isolation:

❌ BAD (data leak):
  SELECT * FROM patients WHERE patient_id = 123;

✅ GOOD (tenant-safe):
  SELECT * FROM patients 
  WHERE patient_id = 123 AND tenant_id = request.user.tenant_id;

Implementation:
  1. JWT token includes tenant_id
  2. FastAPI dependency injects tenant_id: Depends(get_current_tenant)
  3. All queries filter by tenant_id
  4. Database indexes: (tenant_id, patient_id)
  5. Audit logs track access per tenant
```

---

### PROJECT 2: QualityMetrics — Healthcare Quality Measure Platform

**User Journey & Feature Flow:**
```
HEALTHCARE ORGANIZATION ADMIN
│
├─ LOGIN
│  ├─ Email/Password
│  ├─ Validate (backend auth service)
│  └─ Receive JWT token (store in localStorage)
│
├─ VIEW DASHBOARD
│  ├─ Fetch: `/api/quality/metrics?org_id=X`
│  ├─ Display KPIs:
│  │  • Colorectal screening rate: 72%
│  │  • Breast cancer screening: 68%
│  │  • HbA1c testing: 85%
│  └─ Show trends (line chart over 12 months)
│
├─ IDENTIFY CARE GAPS
│  ├─ Query: `/api/quality/gaps?screening=colonoscopy`
│  ├─ Backend SQL:
│  │  SELECT patients WHERE
│  │    - Age >= 50 AND age <= 75
│  │    - last_colonoscopy < (today - 1460 days)  -- 4 years
│  │    - NOT in exclusion_list
│  ├─ Display: 432 patients due for colonoscopy
│  └─ Show: Patient name, age, days_overdue, MRN
│
├─ CLOSE GAPS (WORKFLOW)
│  ├─ Option 1: Send reminder email
│  │  ├─ POST `/api/quality/send-reminder`
│  │  ├─ Backend: Generate email body
│  │  ├─ Send via email service (async)
│  │  └─ Log reminder sent
│  │
│  ├─ Option 2: Schedule appointment
│  │  ├─ POST `/api/appointments/schedule`
│  │  ├─ Store appointment details
│  │  └─ Send appointment confirmation
│  │
│  └─ Option 3: Record care completed
│      ├─ POST `/api/quality/record-screening`
│      ├─ Update: patients.last_colonoscopy = today
│      ├─ Close gap: UPDATE gaps SET closed_at = now()
│      └─ Decrement gap count in dashboard
│
├─ VIEW REPORTS
│  ├─ GET `/api/quality/reports/closure-rate`
│  ├─ Return: 
│  │  {
│  │    "total_gaps": 1200,
│  │    "closed_gaps": 864,
│  │    "closure_rate": 0.72,
│  │    "trends": [...]
│  │  }
│  └─ Export as PDF/CSV
│
└─ BACKGROUND JOB (Runs daily 2 AM)
   ├─ Query all patients in org
   ├─ Check screening due dates
   ├─ Identify NEW gaps
   ├─ Generate reminders
   └─ Send emails (async tasks)
```

**Data Model:**
```
patients
├─ id (PK)
├─ org_id (FK)
├─ name, dob, age
├─ last_colonoscopy (nullable)
├─ last_mammo (nullable)
├─ last_hba1c (nullable)
└─ created_at, updated_at

quality_gaps
├─ id (PK)
├─ patient_id (FK)
├─ org_id (FK)
├─ gap_type ('colonoscopy' | 'mammo' | 'hba1c')
├─ identified_at
├─ closed_at (nullable)
├─ closure_method ('reminder' | 'completed' | 'excluded')
└─ created_at

screenings_performed
├─ id (PK)
├─ patient_id (FK)
├─ screening_type ('colonoscopy' | 'mammo' | 'hba1c')
├─ performed_date
├─ result (normal | abnormal)
└─ provider
```

---

### PROJECT 3: CoderScreen-RA — Medical Coder Screening Tool

**Coder Workflow:**
```
MEDICAL CODER
│
├─ LOGIN
│  └─ Authenticate with credentials
│
├─ VIEW ASSIGNED CLAIMS
│  ├─ Dashboard shows: 15 claims pending review
│  ├─ Queue sorted by: date received, priority
│  └─ Display: Claim ID, Patient Name, DOB, Service Date
│
├─ REVIEW CLAIM DETAILS
│  ├─ Medical Record Content
│  │  ├─ Provider notes
│  │  ├─ Diagnoses mentioned
│  │  ├─ Test results
│  │  └─ Medications
│  │
│  ├─ Current Coding (from ML model)
│  │  ├─ Suggested ICD-10 codes
│  │  ├─ Confidence scores
│  │  └─ Reasoning (which doc excerpt supports code)
│  │
│  └─ Action: Accept / Modify / Add Codes
│
├─ ASSIGN CODES (Workflow)
│  ├─ Search ICD-10: Type "diabetes" 
│  │  └─ Autocomplete: E11.9 (Type 2 DM), E10.9 (Type 1 DM), etc.
│  │
│  ├─ Select code: E11.22 (T2DM with neuropathy)
│  │  ├─ Validate: Code exists, not outdated
│  │  ├─ Check: Supported by medical record
│  │  └─ Show: Description, Related codes, Risk category
│  │
│  ├─ Assign 5-10 codes per claim
│  │  └─ Frontend state: codes = [{code: 'E11.22', section: 'Diagnoses'}]
│  │
│  └─ SUBMIT for audit
│     ├─ POST `/api/coding/submit-claim`
│     ├─ Backend validation:
│     │  ├─ Verify coder authorized
│     │  ├─ Check codes are valid
│     │  └─ No missing required codes
│     └─ Store: claim_codings table
│
├─ AUDIT FEEDBACK LOOP
│  ├─ Auditor reviews coder work
│  ├─ Flags issues: Missing codes, incorrect codes, over-coding
│  ├─ Coder sees feedback: "Missed E11.22 (in note: 'patient has neuropathy')"
│  └─ Coder corrects and resubmits
│
├─ PERFORMANCE METRICS
│  ├─ Accuracy: % codes correct vs. audit
│  ├─ Completeness: % required codes captured
│  ├─ Turnaround: avg time per claim
│  └─ Trending: improved over last 30 days?
│
└─ HCC IMPACT
   ├─ Show: "These codes map to HCC 22 (Diabetes with complications)"
   ├─ Risk weight: 0.289
   └─ Note: Improves patient RAF (risk adjustment factor)
```

**Backend Decision Support Engine:**
```
INCOMING CLAIM
│
├─ NLP EXTRACTION
│  ├─ Parse medical notes
│  ├─ Extract entities: diagnoses, treatments, findings
│  └─ Example: "Patient has Type 2 diabetes with peripheral neuropathy"
│     ├─ Entity 1: "Type 2 diabetes" → possible codes: E11.x
│     └─ Entity 2: "peripheral neuropathy" → possible codes: E11.22, G63.9x
│
├─ CODE SUGGESTION ENGINE
│  ├─ Rank codes by confidence (ML model or rules-based)
│  ├─ Validate: Code is billable for this service date
│  └─ Return top 5 suggestions to UI
│
├─ CODER ACCEPTS/MODIFIES
│  └─ Final code set submitted
│
└─ STORE & AUDIT
   ├─ Save in database
   ├─ Queue for auditor review
   └─ Calculate accuracy after audit completes
```

---

### PROJECT 4: LiveStreamPlatform — Self-Hostable Video Platform

**User Journey:**
```
VISITOR
│
├─ BROWSE PUBLIC FEED
│  ├─ Load homepage
│  ├─ GET `/api/videos?sort=trending&limit=20`
│  ├─ Display: 20 videos (thumbnail, title, creator, view count)
│  │  ├─ Filter: by category, creator
│  │  └─ Search: search bar
│  └─ Click video → watch
│
├─ CLICK VIDEO TO WATCH
│  ├─ GET `/api/videos/{video_id}`
│  ├─ Fetch: metadata, creator info, comments, like count
│  ├─ Stream video from S3/MinIO
│  │  ├─ CloudFront CDN (if AWS)
│  │  └─ Load 1080p/720p/480p based on bandwidth
│  ├─ ACTIONS:
│  │  ├─ Like video (POST `/api/videos/{id}/like`)
│  │  ├─ Add comment (POST `/api/comments`)
│  │  └─ Subscribe to creator (POST `/api/subscriptions`)
│  └─ View count increments (UPDATE videos SET views = views + 1)
│
└─ SIGN UP / LOGIN
   ├─ Email verification
   ├─ Create profile
   └─ Proceed to creator mode

CREATOR
│
├─ ACCESS CREATOR STUDIO
│  ├─ Dashboard: 
│  │  • Videos uploaded: 12
│  │  • Total views: 45,230
│  │  • Subscribers: 342
│  │  • Trending video: "React Hooks Tutorial" (8,923 views)
│  └─ Analytics (line chart): views over last 30 days
│
├─ UPLOAD VIDEO
│  ├─ Select file (MP4, WebM)
│  ├─ Show upload progress (chunked upload)
│  │  ├─ Browser splits video into 5MB chunks
│  │  ├─ Upload chunks in parallel
│  │  ├─ Show: "45% uploaded" progress bar
│  │  ├─ Resume capability if interrupted
│  │  └─ Backend reassembles chunks
│  │
│  ├─ Upload metadata
│  │  ├─ Title: "React Hooks Tutorial"
│  │  ├─ Description: "..."
│  │  ├─ Category: "Education"
│  │  ├─ Thumbnail (auto-generated or custom)
│  │  └─ Privacy: Public / Private
│  │
│  ├─ BACKEND PROCESSING (Async Queue)
│  │  ├─ Store file in S3/MinIO
│  │  ├─ Generate thumbnail (extract frame at 5 sec)
│  │  ├─ Transcode video → multiple resolutions
│  │  │  ├─ 1080p (5GB)
│  │  │  ├─ 720p (2GB)
│  │  │  ├─ 480p (800MB)
│  │  │  └─ Task queue: Celery / async worker
│  │  └─ Send email when ready: "Your video is live!"
│  │
│  └─ VIDEO LIVE
│     ├─ Appears in feed
│     ├─ Creator can share link
│     └─ Views/comments start coming in
│
├─ MANAGE VIDEOS
│  ├─ Edit title, description, thumbnail
│  ├─ Delete video
│  ├─ View analytics: views, likes, comments, watch time
│  └─ Monitor monetization (if enabled)
│
└─ MONETIZATION SETTINGS
   ├─ Enable ads
   ├─ Set revenue share
   └─ Track earnings
```

**Architecture & File Storage:**
```
┌─────────────────────────────────────────────┐
│         VIDEO UPLOAD & STREAMING             │
├─────────────────────────────────────────────┤
│                                              │
│  CREATOR UPLOADS VIDEO                      │
│  ├─ Chunked upload (5MB chunks)             │
│  ├─ Reassemble on backend                   │
│  └─ Store original in S3/MinIO              │
│                                              │
│  ASYNC TRANSCODING QUEUE                    │
│  ├─ FFmpeg transcode job                    │
│  ├─ Generate 1080p, 720p, 480p              │
│  ├─ Store transcoded versions in S3         │
│  └─ Generate thumbnail                      │
│                                              │
│  VIEWER REQUESTS VIDEO                      │
│  ├─ Request: GET /videos/stream/{id}        │
│  ├─ Backend selects quality (based on BW)   │
│  ├─ Serve from CloudFront CDN               │
│  └─ HLS/DASH streaming (adaptive bitrate)   │
│                                              │
│  DATABASE (PostgreSQL)                      │
│  ├─ videos (title, creator_id, s3_key)     │
│  ├─ users (name, email, subscription)      │
│  ├─ comments (text, user_id, video_id)     │
│  ├─ likes (user_id, video_id, created_at)  │
│  ├─ subscriptions (follower_id, creator_id)│
│  └─ analytics (views, watch_time per video)│
│                                              │
│  STORAGE (S3/MinIO)                         │
│  ├─ /originals/{video_id}.mp4 (5GB)        │
│  ├─ /1080p/{video_id}.mp4 (2GB)            │
│  ├─ /720p/{video_id}.mp4 (1GB)             │
│  ├─ /480p/{video_id}.mp4 (500MB)           │
│  └─ /thumbnails/{video_id}.jpg             │
└─────────────────────────────────────────────┘
```

---

### PROJECT 5: VBC-HCC — .NET HCC Coding Application

**HCC Coding Workflow:**
```
HEALTHCARE BILLING DEPARTMENT
│
├─ UPLOAD CLAIMS FILE
│  ├─ CSV: patient_id, icd_codes, dates
│  └─ Example: Patient 123, diagnoses: E11.9, I10, E11.22
│
├─ SYSTEM PROCESSES CLAIMS
│  ├─ Parse ICD-10 codes
│  ├─ Query HCC mapping table
│  │  └─ E11.9 → HCC 19 (Diabetes w/o complications, weight 0.316)
│  │  └─ I10 → HCC 18 (Hypertension, weight 0.085)
│  │  └─ E11.22 → HCC 22 (Diabetes w/ complications, weight 0.289)
│  │
│  ├─ APPLY HCC HIERARCHY (Critical!)
│  │  ├─ Rule: If both HCC19 and HCC22, only count HCC22 (higher)
│  │  ├─ Rule: If both HCC18 and HCC85, only count HCC85
│  │  └─ Result: Keep only highest-weight codes
│  │
│  ├─ CALCULATE RAF (Risk Adjustment Factor)
│  │  ├─ RAF = 0.289 (E11.22) + 0.085 (I10) = 0.374
│  │  ├─ Store in database
│  │  └─ Display on coder screen
│  │
│  └─ REPORT TO CMS (end of month)
│     ├─ Generate submission file
│     ├─ Include: patient_id, RAF, diagnoses, HCC codes
│     └─ CMS uses for capitation payment calculation
│
├─ CODER REVIEWS & VALIDATES
│  ├─ Check: Are all diagnoses captured?
│  ├─ Check: Are codes accurate to documentation?
│  ├─ Adjust: Add missing codes or remove incorrect ones
│  └─ Lock: Submit for audit
│
├─ AUDITOR QA REVIEW
│  ├─ Random sample: 10% of claims
│  ├─ Verify: codes are accurate
│  ├─ Flag issues: undercoding, overcoding, missing codes
│  ├─ Assign severity: minor / major / critical
│  └─ Send feedback to coder
│
├─ METRICS & REPORTING
│  ├─ Accuracy: % of codes verified as correct
│  ├─ Completeness: % of eligible codes captured
│  ├─ HCC capture rate: which HCC codes are being captured?
│  ├─ RAF trend: is RAF improving over time?
│  └─ Coder performance: leaderboard by accuracy
│
└─ COMPLIANCE & AUDIT TRAIL
   ├─ Who coded it? (user_id)
   ├─ When? (timestamp)
   ├─ What changed? (before/after)
   ├─ Audit log for regulatory review
   └─ Enable CMS audits with full history
```

**Database Schema (SQL Server):**
```
PATIENTS
├─ patient_id (PK)
├─ name, dob, gender
├─ current_raf (calculated, updated)
├─ last_coding_date
└─ created_at

CLAIMS
├─ claim_id (PK)
├─ patient_id (FK)
├─ service_date
├─ icd_codes (comma-sep or normalized)
└─ claim_status (pending / coded / audited / submitted)

HCC_MAPPINGS (Reference Table)
├─ icd_code (E11.9)
├─ hcc_code (19)
├─ description (Diabetes without complications)
├─ risk_weight (0.316)
├─ valid_from, valid_to (ICD-10 versioning)
└─ hierarchy_notes

HCC_CALCULATIONS
├─ patient_id (FK)
├─ hcc_codes (calculated) [22, 18]
├─ raf_score (0.374)
├─ calculated_by (coder_user_id)
├─ calculated_at
└─ is_final (submitted to CMS or not)

AUDIT_LOG
├─ audit_id (PK)
├─ claim_id (FK)
├─ coder_user_id
├─ auditor_user_id
├─ findings (undercoding / overcoding / accurate)
├─ severity (minor / major)
├─ feedback_text
└─ audit_date
```

---

## EXPLAINING PROJECTS IN INTERVIEW

### Framework to Use:

**1. START WITH CONTEXT**
   - "This was a healthcare risk adjustment SaaS platform..."
   - Establish: industry, scale, team size, your role

**2. DESCRIBE THE PROBLEM**
   - "The challenge was calculating accurate RAF (Risk Adjustment Factor) for 100k patients..."
   - Show you understand the domain problem

**3. EXPLAIN YOUR SOLUTION**
   - Frontend: "Built React dashboard to display patient risk scores..."
   - Backend: "FastAPI endpoints with async SQLAlchemy for performance..."
   - Database: "Multi-tenant PostgreSQL with tenant_id filtering..."
   - DevOps: "Deployed to GCP Cloud Run for auto-scaling..."

**4. HIGHLIGHT TECHNICAL DECISIONS**
   - "Why async? Improved response time from 10s to 200ms..."
   - "Why multi-tenant? Each healthcare org is separate but shares infrastructure..."
   - "Why PostgreSQL? Better async driver support in Python than SQL Server..."

**5. DISCUSS TRADE-OFFS**
   - "Considered using Cache (Redis) but decided: Database queries were fast enough after indexing"
   - "Considered microservices but: Monolith was simpler for team size"
   - "Considered NoSQL but: Relational schema was clearer for patient relationships"

**6. MENTION MEASURABLE IMPACT**
   - "Reduced manual coding time by 40 hours/month"
   - "Improved cancer screening rate from 60% to 72%"
   - "Handled 10x traffic increase with auto-scaling"

**7. CLOSE WITH LEARNING**
   - "Learned multi-tenant architecture patterns..."
   - "Improved async/await understanding significantly..."
   - "Realized importance of proper database indexing..."

---

**Tips for interviews**:
- Ask clarifying questions before jumping to solutions
- Discuss trade-offs (performance vs. simplicity, cost vs. reliability)
- Mention testing, monitoring, edge cases
- Relate answers to actual projects you've worked on
- Be honest about gaps ("I haven't worked with X, but I'd learn it quickly")
