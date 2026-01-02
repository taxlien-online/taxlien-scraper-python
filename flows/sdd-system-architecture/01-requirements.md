# Requirements: TAXLIEN.online - Complete System Architecture (от нуля)

> Version: 1.0
> Status: DRAFT
> Last Updated: 2025-12-30

## Executive Summary

### Vision

Построить **масштабируемую, cloud-native платформу** для инвестиций в tax liens с следующими характеристиками:

- 🚀 **Scalable**: От 100 до 1M+ пользователей без архитектурных изменений
- 💰 **Cost-Effective**: $500/месяц для 1K users → $5K/месяц для 100K users (linear scaling)
- 🔒 **Secure**: Enterprise-grade безопасность, SOC 2 compliance готовность
- ⚡ **Fast**: <100ms API response time, real-time updates
- 🌍 **Global**: Multi-region deployment, CDN для статики
- 🤖 **AI-Powered**: Real ML models, не mock data
- 🔄 **Event-Driven**: Async processing, resilient to failures

### Current Problems with Existing System

| Problem | Impact | Solution |
|---------|--------|----------|
| Monolithic Flutter app | Hard to maintain, slow builds | Microservices + BFF pattern |
| Magento backend | Overkill, slow, expensive | Custom FastAPI services |
| Mock AI | No real value | Real ML pipeline |
| Manual scraping | Doesn't scale | Distributed scraper cluster |
| No data warehouse | Can't do analytics | Data lake architecture |
| SQLite local storage | Sync issues | Cloud-first with offline fallback |
| ICP blockchain | Expensive, slow | Multi-chain support (Polygon) |

---

## System Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  Flutter App (iOS/Android)  │  Next.js Web App  │  Admin    │
│  - Mobile-first UI          │  - Marketing site  │  Dashboard│
│  - Offline-capable          │  - SEO optimized   │  - Ops    │
└──────────────┬──────────────┴──────────┬─────────┴──────────┘
               │                         │
               ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                       │
├─────────────────────────────────────────────────────────────┤
│              Kong API Gateway / AWS API Gateway              │
│  - Rate limiting  │ Auth │ Load balancing │ Caching         │
└──────────────┬──────────────────────────────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND SERVICES (Microservices)          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Auth Service │  │ User Service │  │ Search Service│      │
│  │  FastAPI     │  │  FastAPI     │  │  FastAPI     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐      │
│  │Payment Service│  │Scraper Service│  │ ML Service  │      │
│  │  FastAPI     │  │  Python       │  │  Python     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐      │
│  │  NFT Service │  │  Data API    │  │ Analytics    │      │
│  │  FastAPI     │  │  FastAPI     │  │  Service     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
└──────────────┬───────────────────────────────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     MESSAGE BUS & EVENTS                     │
├─────────────────────────────────────────────────────────────┤
│              Apache Kafka / AWS EventBridge                  │
│  Events: lien.created │ user.subscribed │ scrape.completed  │
└──────────────────────────────────────────────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                              │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL     │  MongoDB      │  Redis        │  S3/MinIO │
│  (Relational)   │  (Documents)  │  (Cache)      │  (Objects)│
│  - Users        │  - Raw scrapes│  - Sessions   │  - Images │
│  - Subscriptions│  - Logs       │  - API cache  │  - PDFs   │
│  - Transactions │  - Analytics  │  - Rate limit │  - Videos │
└─────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA WAREHOUSE                            │
├─────────────────────────────────────────────────────────────┤
│                  ClickHouse / BigQuery                       │
│  - OLAP queries  │  ML training data  │  Business analytics│
└─────────────────────────────────────────────────────────────┘
```

---

## Microservices Breakdown

### 1. API Gateway Service

**Responsibility:** Entry point для всех клиентских запросов

**Tech Stack:**
- Kong Gateway (open-source) или AWS API Gateway
- Lua plugins for custom logic
- Redis для rate limiting

**Key Features:**
- Authentication validation (JWT)
- Rate limiting (per user tier: Free/Premium/Enterprise)
- Request routing
- Response caching
- CORS handling
- API versioning (/v1/, /v2/)

**SDD:** [`sdd-api-gateway/`](sdd-api-gateway/)

---

### 2. Auth Service

**Responsibility:** Аутентификация и авторизация

**Tech Stack:**
- FastAPI (Python)
- JWT tokens
- PostgreSQL (user credentials)
- Redis (session store)

**Key Features:**
- Email/password signup
- OAuth (Google, Apple, Facebook)
- JWT token issuance & refresh
- Password reset flow
- Email verification
- 2FA (TOTP)
- Device management

**API Endpoints:**
```
POST   /v1/auth/signup
POST   /v1/auth/login
POST   /v1/auth/refresh
POST   /v1/auth/forgot-password
POST   /v1/auth/verify-email
GET    /v1/auth/me
```

**SDD:** [`sdd-auth-service/`](sdd-auth-service/)

---

### 3. User Service

**Responsibility:** User profiles, preferences, settings

**Tech Stack:**
- FastAPI (Python)
- PostgreSQL (user data)
- S3 (profile images)

**Key Features:**
- Profile CRUD
- Subscription tier management
- User preferences (language, currency, notifications)
- KYC/AML compliance (for transactions)
- User analytics tracking

**Database Schema:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    subscription_tier VARCHAR(20) DEFAULT 'free',
    trial_end_date TIMESTAMP,
    kyc_status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE user_preferences (
    user_id UUID REFERENCES users(id),
    language VARCHAR(10) DEFAULT 'en',
    currency VARCHAR(3) DEFAULT 'USD',
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT true
);
```

**SDD:** [`sdd-user-service/`](sdd-user-service/)

---

### 4. Scraper Service

**Responsibility:** Distributed web scraping для tax lien данных

**Tech Stack:**
- Python (AsyncIO)
- Celery (distributed task queue)
- Redis (broker & result backend)
- Selenium/Playwright (browser automation)
- BeautifulSoup / lxml (HTML parsing)
- ScrapingBee / Bright Data (proxy rotation)
- MongoDB (raw HTML storage)
- PostgreSQL (parsed structured data)

**Architecture:**
```
┌──────────────────────────────────────────────────┐
│            Scraper Orchestrator                   │
│  - Schedules scraping jobs                       │
│  - Prioritizes counties by demand                │
│  - Manages scraper workers                       │
└──────────────┬───────────────────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Worker Pool │  │ Worker Pool │  │ Worker Pool │
│  QPublic    │  │  Beacon     │  │ Bid4Assets  │
│  (10 nodes) │  │  (5 nodes)  │  │  (5 nodes)  │
└─────┬───────┘  └─────┬───────┘  └─────┬───────┘
      │                │                 │
      └────────┬───────┴─────────────────┘
               ▼
    ┌──────────────────────┐
    │  Parser & Validator   │
    │  - Extracts data      │
    │  - Validates fields   │
    │  - Deduplicates       │
    └──────┬────────────────┘
           ▼
    ┌──────────────────────┐
    │  Data Enrichment      │
    │  - Geocoding          │
    │  - Property valuation │
    │  - ML scoring         │
    └──────┬────────────────┘
           ▼
    ┌──────────────────────┐
    │  Storage (PostgreSQL) │
    └───────────────────────┘
```

**Key Features:**
- Platform adapters (QPublic, Beacon, Bid4Assets, Tyler)
- Proxy rotation (avoid bans)
- Incremental updates (only new/changed data)
- Priority queue (scrape high-demand counties first)
- Error handling & retries
- Data validation pipeline
- Duplicate detection

**Scaling:**
- Horizontal: Add more Celery workers
- Vertical: Increase worker concurrency
- Target: 100K properties/day

**SDD:** [`sdd-scraper-service/`](sdd-scraper-service/)

---

### 5. Data Processing Pipeline

**Responsibility:** ETL для scraped data

**Tech Stack:**
- Apache Airflow (orchestration)
- Python (data transformations)
- PostgreSQL → ClickHouse (OLAP)
- dbt (data transformations)

**Pipeline Stages:**
1. **Extract**: Read raw data from scraper service
2. **Transform**:
   - Geocode addresses
   - Calculate risk scores
   - Enrich with property data (Zillow API)
   - Deduplicate
3. **Load**: Write to data warehouse
4. **Index**: Update search indexes (Elasticsearch)

**Airflow DAG Example:**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator

dag = DAG('tax_lien_etl', schedule_interval='@daily')

extract = PythonOperator(
    task_id='extract_raw_data',
    python_callable=extract_from_mongodb,
    dag=dag
)

transform = PythonOperator(
    task_id='transform_data',
    python_callable=transform_tax_liens,
    dag=dag
)

load = PythonOperator(
    task_id='load_to_warehouse',
    python_callable=load_to_clickhouse,
    dag=dag
)

extract >> transform >> load
```

**SDD:** [`sdd-data-pipeline/`](sdd-data-pipeline/)

---

### 6. Search Service

**Responsibility:** Fast, relevant search для tax liens

**Tech Stack:**
- FastAPI (Python)
- Elasticsearch / Meilisearch (search engine)
- Redis (result caching)

**Key Features:**
- Full-text search (address, county, parcel ID)
- Filters (price range, interest rate, county, property type)
- Sorting (price, ROI, risk score)
- Autocomplete
- Fuzzy matching
- Geospatial search (within X miles of location)
- Result pagination
- Search analytics

**API Endpoints:**
```
GET    /v1/search?q=miami&price_max=5000&sort=roi_desc&page=1
GET    /v1/search/autocomplete?q=mia
GET    /v1/search/filters (returns available filter options)
```

**Performance:**
- <50ms search response time
- 10K+ queries per second capacity
- 1M+ documents indexed

**SDD:** [`sdd-search-service/`](sdd-search-service/)

---

### 7. ML/AI Service

**Responsibility:** Machine learning models для predictions

**Tech Stack:**
- Python (scikit-learn, TensorFlow, PyTorch)
- FastAPI (model serving)
- MLflow (model versioning)
- PostgreSQL (training data)
- S3 (model artifacts)

**Models:**

#### Model 1: Redemption Probability Predictor
**Input:** Tax lien features (county, property value, tax amount, owner tenure, etc.)
**Output:** Probability (0-1) that owner will redeem vs foreclose
**Algorithm:** Random Forest Classifier
**Accuracy Target:** 75%+

#### Model 2: Auction Price Forecaster
**Input:** Historical auction prices, economic indicators
**Output:** Predicted winning bid
**Algorithm:** Prophet (time series)
**MAE Target:** <15%

#### Model 3: Property Risk Scorer
**Input:** Property characteristics, location, liens
**Output:** Risk score (1-100)
**Algorithm:** Gradient Boosting
**Use Case:** Show "Safety Score" in app

#### Model 4: Portfolio Optimizer
**Input:** User constraints (budget, risk tolerance, counties)
**Output:** Recommended portfolio allocation
**Algorithm:** Reinforcement Learning (PPO)
**Use Case:** Enterprise tier feature

**API Endpoints:**
```
POST   /v1/ml/predict/redemption
POST   /v1/ml/predict/auction-price
POST   /v1/ml/score/risk
POST   /v1/ml/optimize/portfolio
```

**Training Pipeline:**
```
1. Data Collection (from warehouse)
2. Feature Engineering
3. Model Training (MLflow tracking)
4. Model Evaluation
5. Model Deployment (if better than current)
6. A/B Testing (gradual rollout)
```

**SDD:** [`sdd-ml-service/`](sdd-ml-service/)

---

### 8. NFT Service

**Responsibility:** Tokenization & marketplace для tax liens

**Tech Stack:**
- FastAPI (Python)
- Web3.py (blockchain interaction)
- Polygon/Ethereum (EVM chains)
- PostgreSQL (NFT metadata)
- IPFS (decentralized storage)

**Key Features:**
- Mint tax lien as NFT
- List NFT for sale
- Buy/sell NFT (marketplace)
- Fractional ownership (ERC-1155)
- Royalties (platform fee on secondary sales)
- Wallet integration (MetaMask, WalletConnect)

**Smart Contracts (Solidity):**
```solidity
// TaxLienNFT.sol
contract TaxLienNFT is ERC721URIStorage {
    struct TaxLien {
        string parcelId;
        uint256 taxAmount;
        uint256 assessedValue;
        uint16 interestRate;
        address county;
    }

    mapping(uint256 => TaxLien) public liens;

    function mintTaxLien(
        address to,
        string memory parcelId,
        uint256 taxAmount,
        uint256 assessedValue,
        uint16 interestRate,
        address county
    ) public onlyOwner returns (uint256) {
        uint256 tokenId = _tokenIdCounter.current();
        _safeMint(to, tokenId);

        liens[tokenId] = TaxLien({
            parcelId: parcelId,
            taxAmount: taxAmount,
            assessedValue: assessedValue,
            interestRate: interestRate,
            county: county
        });

        _setTokenURI(tokenId, _buildTokenURI(tokenId));
        _tokenIdCounter.increment();

        return tokenId;
    }
}
```

**Multi-Chain Support:**
- Polygon (low fees, fast)
- Ethereum (prestige, liquidity)
- ICP (already partially integrated)

**SDD:** [`sdd-nft-service/`](sdd-nft-service/)

---

### 9. Payment Service

**Responsibility:** Обработка платежей и fees

**Tech Stack:**
- FastAPI (Python)
- Stripe (payment processing)
- Stripe Connect (escrow & splits)
- PostgreSQL (transaction ledger)
- Kafka (payment events)

**Key Features:**
- Subscription management (Premium, Enterprise)
- One-time payments (educational products)
- Transaction fees (purchase liens, NFT minting)
- Escrow (hold funds until conditions met)
- Payouts (withdraw earnings)
- Refunds
- Webhooks (Stripe → our system)
- Invoice generation
- Tax reporting (1099-K)

**Database Schema:**
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    type VARCHAR(50), -- 'subscription', 'purchase', 'nft_mint', 'withdrawal'
    amount DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20), -- 'pending', 'completed', 'failed', 'refunded'
    stripe_payment_intent_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE subscription_history (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    plan VARCHAR(50), -- 'starter', 'premium', 'enterprise'
    status VARCHAR(20), -- 'active', 'canceled', 'past_due'
    stripe_subscription_id VARCHAR(255),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP
);
```

**SDD:** [`sdd-payment-service/`](sdd-payment-service/)

---

### 10. Data API Service (B2B)

**Responsibility:** Monetize data через API access

**Tech Stack:**
- FastAPI (Python)
- PostgreSQL (query caching)
- Redis (rate limiting)
- Kong (API key management)

**Key Features:**
- RESTful API для institutional investors
- Rate limiting (по pricing tier)
- API key management
- Usage analytics
- Webhooks (data updates)
- Batch export (CSV, JSON)

**Pricing Tiers:**
```
Starter:      $99/mo  (1K requests/month, 5 counties)
Professional: $299/mo (10K requests/month, 50 counties)
Enterprise:   $999/mo (Unlimited, all counties, webhooks)
```

**API Endpoints:**
```
GET    /v1/data/counties/{state}
GET    /v1/data/liens/{county}?status=active&limit=100
GET    /v1/data/properties/{parcel_id}
GET    /v1/data/auctions/upcoming?days=30
GET    /v1/data/statistics/{county}
POST   /v1/data/webhooks (subscribe to updates)
```

**SDD:** [`sdd-data-api-service/`](sdd-data-api-service/)

---

### 11. Analytics Service

**Responsibility:** Business intelligence & reporting

**Tech Stack:**
- FastAPI (Python)
- ClickHouse (OLAP database)
- Metabase / Superset (BI dashboards)
- Kafka (event streaming)

**Key Features:**
- Revenue analytics
- User engagement metrics
- Scraper performance monitoring
- ML model performance tracking
- Funnel analysis (trial → paid conversion)
- Cohort analysis
- Real-time dashboards

**Metrics Tracked:**
```
Business Metrics:
- MRR (Monthly Recurring Revenue)
- ARPU (Average Revenue Per User)
- LTV (Lifetime Value)
- CAC (Customer Acquisition Cost)
- Churn Rate
- Trial Conversion Rate

Technical Metrics:
- API latency (p50, p95, p99)
- Error rates
- Scraper success rate
- Database query performance
- Cache hit rate
```

**SDD:** [`sdd-analytics-service/`](sdd-analytics-service/)

---

### 12. Notification Service

**Responsibility:** Email, SMS, push notifications

**Tech Stack:**
- FastAPI (Python)
- SendGrid (email)
- Twilio (SMS)
- Firebase Cloud Messaging (push)
- Kafka (event triggers)

**Notification Types:**
```
Transactional:
- Welcome email (signup)
- Email verification
- Password reset
- Purchase confirmation
- Subscription renewal

Marketing:
- Weekly digest (new liens in watchlist)
- Abandoned cart (trial ending soon)
- Upsell (Premium features teaser)

Alerts:
- Auction reminder (24h before)
- Price drop alert
- New liens in saved search
- Redemption update
```

**Templates:**
- HTML email templates (MJML)
- SMS templates (140 chars)
- Push notification templates (title + body)

**SDD:** [`sdd-notification-service/`](sdd-notification-service/)

---

### 13. Admin Dashboard

**Responsibility:** Internal ops & support tools

**Tech Stack:**
- Next.js (TypeScript)
- TailwindCSS (styling)
- Recharts (data viz)
- FastAPI (admin API)

**Features:**
- User management (view, edit, impersonate)
- Subscription management (upgrades, refunds)
- Content management (educational courses)
- Scraper monitoring (success rates, errors)
- Transaction ledger (all payments)
- Support tickets (Zendesk integration)
- Feature flags (LaunchDarkly)

**Access Control:**
- Admin (full access)
- Support (read-only + refund capability)
- Developer (scraper monitoring, logs)

**SDD:** [`sdd-admin-dashboard/`](sdd-admin-dashboard/)

---

### 14. Mobile App (Flutter)

**Responsibility:** iOS & Android client

**Tech Stack:**
- Flutter (Dart)
- Riverpod (state management)
- Dio (HTTP client)
- Hive (local database)
- Firebase (analytics, crashlytics, messaging)

**Architecture:**
```
lib/
├── core/
│   ├── network/          # API clients
│   ├── storage/          # Local persistence
│   ├── models/           # Data models
│   └── constants/        # App constants
├── features/
│   ├── auth/             # Login, signup
│   ├── search/           # Tax lien search
│   ├── portfolio/        # User portfolio
│   ├── marketplace/      # NFT marketplace
│   ├── education/        # In-app courses
│   └── profile/          # User settings
├── shared/
│   ├── widgets/          # Reusable UI components
│   └── utils/            # Helper functions
└── main.dart
```

**Offline Capability:**
- Cache API responses (Hive)
- Queue mutations when offline
- Sync when reconnected

**SDD:** [`sdd-mobile-app/`](sdd-mobile-app/)

---

### 15. Web App (Next.js)

**Responsibility:** Marketing site + web platform

**Tech Stack:**
- Next.js 14 (TypeScript, App Router)
- TailwindCSS + shadcn/ui
- Vercel (hosting)
- MDX (blog content)

**Pages:**
```
/ (homepage)
/features
/pricing
/about
/blog
/app (web version of mobile app)
/login
/signup
```

**SEO Features:**
- Server-side rendering
- Dynamic OG images
- Sitemap generation
- Structured data (schema.org)
- County landing pages (3,143 pages for SEO!)

**SDD:** [`sdd-web-app/`](sdd-web-app/)

---

## Inter-Service Communication

### Synchronous (REST APIs)

**Use Cases:**
- Client → API Gateway → Services
- Service → Service (when response needed immediately)

**Example:**
```
User signs up:
Client → API Gateway → Auth Service (creates user) → User Service (creates profile)
```

**Protocol:** HTTP/REST с JSON
**Timeout:** 5 seconds max
**Retry:** 3 attempts с exponential backoff

---

### Asynchronous (Event Bus)

**Use Cases:**
- Service → Service (fire-and-forget)
- Background processing
- Decoupling services

**Technology:** Apache Kafka or AWS EventBridge

**Example Events:**
```json
{
  "event_type": "user.subscribed",
  "user_id": "uuid",
  "plan": "premium",
  "timestamp": "2025-12-30T12:00:00Z"
}

{
  "event_type": "lien.created",
  "lien_id": "uuid",
  "county": "Miami-Dade",
  "tax_amount": 1500.00
}

{
  "event_type": "scrape.completed",
  "county": "Orange",
  "properties_scraped": 245,
  "errors": 3
}
```

**Event Subscribers:**
```
user.subscribed →
  - Notification Service (send welcome email)
  - Analytics Service (track conversion)
  - Payment Service (create subscription record)

lien.created →
  - Search Service (index new lien)
  - ML Service (calculate risk score)
  - Notification Service (alert users with saved searches)
```

---

## Database Architecture

### PostgreSQL (Primary Relational DB)

**Use Cases:**
- User accounts
- Subscriptions
- Transactions
- Tax lien metadata (structured data)

**Scaling:**
- Read replicas (for analytics queries)
- Partitioning (by county or date)
- Connection pooling (PgBouncer)

**Backup:**
- Daily snapshots
- Point-in-time recovery
- 30-day retention

---

### MongoDB (Document Store)

**Use Cases:**
- Raw scraped HTML (for debugging)
- Logs
- Unstructured data

**Scaling:**
- Sharding by county
- Replica sets for redundancy

---

### Redis (Cache & Session Store)

**Use Cases:**
- API response caching
- Rate limiting counters
- Session storage (JWT)
- Celery broker

**Data Structures:**
```
SET    user:session:{user_id}  (JWT token)
HASH   api:cache:search:{query_hash}  (search results)
ZSET   ratelimit:{user_id}  (request timestamps)
LIST   celery:tasks  (task queue)
```

**Eviction Policy:** LRU (Least Recently Used)
**Max Memory:** 8GB → 64GB (scales with traffic)

---

### ClickHouse (OLAP / Data Warehouse)

**Use Cases:**
- Business analytics
- ML training data
- Historical reporting

**Schema:**
```sql
CREATE TABLE tax_liens_fact (
    lien_id UUID,
    parcel_id String,
    county String,
    state String,
    tax_amount Decimal(10, 2),
    assessed_value Decimal(12, 2),
    interest_rate UInt8,
    auction_date Date,
    redemption_date Nullable(Date),
    created_at DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(auction_date)
ORDER BY (county, auction_date);
```

**Performance:**
- 10B+ rows
- <1s query time для complex aggregations
- Columnar storage (compress ratio 10:1)

---

### S3 / MinIO (Object Storage)

**Use Cases:**
- Profile images
- Educational content PDFs
- Video courses
- ML model artifacts
- Database backups

**Buckets:**
```
taxlien-user-uploads/
taxlien-educational-content/
taxlien-ml-models/
taxlien-database-backups/
```

**Lifecycle Policies:**
- Educational content: Never delete
- User uploads: Delete after 90 days if user deleted
- Backups: Delete after 30 days

---

## Deployment Architecture

### Kubernetes (K8s)

**Cluster Setup:**
```
Production Cluster:
- 3 Master Nodes (HA)
- 10+ Worker Nodes (auto-scaling)
- Load Balancer (Nginx Ingress)
```

**Namespaces:**
```
- production (live services)
- staging (pre-prod testing)
- development (dev environment)
```

**Example Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: taxlien/auth-service:v1.2.3
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: connection-string
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

**Auto-Scaling:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: auth-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: auth-service
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

### CI/CD Pipeline

**Tools:**
- GitHub Actions (CI)
- ArgoCD (CD)
- Docker (containerization)
- Helm (K8s package manager)

**Pipeline Stages:**
```
1. Code Push (GitHub)
   ↓
2. Run Tests (pytest, jest)
   ↓
3. Build Docker Image
   ↓
4. Push to Registry (Docker Hub / ECR)
   ↓
5. Deploy to Staging (ArgoCD)
   ↓
6. Run Integration Tests
   ↓
7. Manual Approval
   ↓
8. Deploy to Production (ArgoCD)
   ↓
9. Monitor (Datadog, Sentry)
```

---

### Monitoring & Observability

**Tools:**
- Prometheus (metrics)
- Grafana (dashboards)
- Loki (logs)
- Jaeger (distributed tracing)
- Sentry (error tracking)
- Datadog (all-in-one alternative)

**Dashboards:**
```
1. Infrastructure Health
   - CPU, Memory, Disk usage
   - Network traffic
   - Pod status

2. Application Performance
   - API latency (p50, p95, p99)
   - Error rates (4xx, 5xx)
   - Request throughput

3. Business Metrics
   - Active users (DAU, MAU)
   - MRR, ARPU
   - Conversion rates
```

**Alerts:**
```
Critical:
- API error rate > 5%
- Database connection pool exhausted
- Payment processing failures

Warning:
- API latency > 500ms
- Scraper success rate < 90%
- Disk usage > 80%
```

---

## Security Architecture

### Authentication & Authorization

**Flow:**
```
1. User logs in → Auth Service
2. Auth Service validates credentials
3. Issues JWT with claims:
   {
     "user_id": "uuid",
     "email": "user@example.com",
     "tier": "premium",
     "exp": 1735581600
   }
4. Client includes JWT in requests: Authorization: Bearer <token>
5. API Gateway validates JWT
6. Forwards to downstream services with user context
```

**Token Types:**
- Access Token (15 minutes TTL)
- Refresh Token (30 days TTL, stored in DB)

---

### Network Security

- **HTTPS Everywhere** (TLS 1.3)
- **API Gateway** (single entry point)
- **Private Subnets** (services not internet-accessible)
- **VPN** (admin access only)
- **WAF** (Web Application Firewall) - blocks SQL injection, XSS
- **DDoS Protection** (Cloudflare)

---

### Data Security

- **Encryption at Rest** (database, S3)
- **Encryption in Transit** (HTTPS, TLS)
- **PII Masking** (logs don't contain SSN, credit cards)
- **Secrets Management** (AWS Secrets Manager, Vault)
- **Database Access Control** (principle of least privilege)

---

### Compliance

**Target Certifications:**
- SOC 2 Type II (within 12 months)
- PCI DSS Level 1 (for payment processing)
- GDPR compliant (EU users)
- CCPA compliant (California users)

**Requirements:**
- Data retention policies
- Right to deletion (GDPR)
- Audit logs (all data access)
- Incident response plan

---

## Cost Estimation

### Monthly Infrastructure Costs (by scale)

#### 1,000 Users

| Service | Provider | Cost |
|---------|----------|------|
| Kubernetes Cluster | DigitalOcean | $150 (3 nodes) |
| PostgreSQL | Managed DB | $60 |
| Redis | Managed | $30 |
| MongoDB | Atlas | $50 |
| S3 Storage | AWS | $20 |
| CDN | Cloudflare | $20 |
| Monitoring | Datadog | $30 |
| **TOTAL** | | **$360/mo** |

**Per-User Cost:** $0.36/mo

---

#### 10,000 Users

| Service | Provider | Cost |
|---------|----------|------|
| Kubernetes Cluster | DigitalOcean | $400 (8 nodes) |
| PostgreSQL | Managed DB | $200 |
| Redis | Managed | $80 |
| MongoDB | Atlas | $150 |
| S3 Storage | AWS | $100 |
| CDN | Cloudflare | $50 |
| Monitoring | Datadog | $100 |
| **TOTAL** | | **$1,080/mo** |

**Per-User Cost:** $0.11/mo

---

#### 100,000 Users

| Service | Provider | Cost |
|---------|----------|------|
| Kubernetes Cluster | AWS EKS | $2,000 (20+ nodes) |
| PostgreSQL | RDS | $800 |
| Redis | ElastiCache | $400 |
| MongoDB | Atlas | $600 |
| S3 Storage | AWS | $500 |
| CDN | Cloudflare | $200 |
| Monitoring | Datadog | $500 |
| **TOTAL** | | **$5,000/mo** |

**Per-User Cost:** $0.05/mo

**Revenue at 100K users (assume 10% paid at $49.99/mo):**
- 10,000 paying users × $49.99 = $499,900/mo
- **Profit Margin:** 99% ($494,900 profit)

---

## Implementation Timeline

### Phase 1: Foundation (Months 1-2)

**Goal:** Core infrastructure & auth

- [ ] Setup Kubernetes cluster
- [ ] Deploy PostgreSQL, Redis, MongoDB
- [ ] Implement Auth Service
- [ ] Implement User Service
- [ ] Setup API Gateway
- [ ] CI/CD pipeline
- [ ] Basic monitoring

**Deliverable:** Users can signup, login, manage profile

---

### Phase 2: Data Ingestion (Months 2-4)

**Goal:** Scraping & data pipeline working

- [ ] Rebuild Scraper Service (distributed)
- [ ] Data Processing Pipeline (Airflow)
- [ ] Database schema for tax liens
- [ ] Search Service (Elasticsearch)
- [ ] Data validation & quality checks

**Deliverable:** 100+ counties scraped, searchable

---

### Phase 3: Core Features (Months 4-6)

**Goal:** Feature parity with current app

- [ ] Mobile app (Flutter rebuild)
- [ ] Educational content system
- [ ] AI/ML Service (real models)
- [ ] Payment Service (Stripe integration)
- [ ] Portfolio management

**Deliverable:** MVP launch, can onboard beta users

---

### Phase 4: Monetization (Months 6-8)

**Goal:** Revenue streams operational

- [ ] Subscription tiers live
- [ ] Educational products store
- [ ] Transaction fees system
- [ ] NFT Service (basic minting)
- [ ] Data API (B2B)

**Deliverable:** $10K+ MRR

---

### Phase 5: Scale & Optimize (Months 8-12)

**Goal:** Production-ready, scale to 10K+ users

- [ ] NFT Marketplace (secondary sales)
- [ ] Advanced ML models
- [ ] Multi-language support
- [ ] Admin dashboard
- [ ] Analytics dashboards
- [ ] SOC 2 compliance

**Deliverable:** $50K+ MRR, 10K+ users

---

## Success Metrics

### Technical KPIs

| Metric | Target |
|--------|--------|
| API Latency (p95) | <200ms |
| Uptime | 99.9% |
| Error Rate | <0.1% |
| Database Query Time (p95) | <50ms |
| Scraper Success Rate | >95% |
| Deployment Frequency | Daily |
| Mean Time to Recovery | <30 min |

### Business KPIs

| Metric | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|----------|
| Total Users | 500 | 2,000 | 10,000 |
| Paying Users | 25 | 200 | 1,000 |
| MRR | $1,250 | $10,000 | $50,000 |
| CAC | <$50 | <$40 | <$30 |
| LTV | >$500 | >$600 | >$800 |
| Churn Rate | <7% | <5% | <4% |

---

## Approval

- [ ] Reviewed by: Anton (Product Owner)
- [ ] Approved on: [Pending review]
- [ ] Notes: This is a massive undertaking. Prioritize modules based on ROI. Consider hybrid approach: keep some existing services while building new ones.
