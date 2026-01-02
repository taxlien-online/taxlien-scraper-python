# SDD: System Architecture

> **Status:** REQUIREMENTS (Draft)
> **Started:** 2025-12-30
> **Owner:** Anton (Product Owner)

## Overview

Complete architectural redesign of TAXLIEN.online from monolithic system to cloud-native microservices platform.

### Vision

Transform from single-server monolith to distributed, scalable architecture capable of handling 1M+ users with 99.9% uptime and <200ms API response times.

### Key Objectives

- **Scalability:** Linear cost scaling from 1K to 1M users
- **Performance:** 10x faster API responses (<200ms vs current 500-2000ms)
- **Reliability:** 99.9% uptime (vs current ~95%)
- **Cost-Efficiency:** $0.05-0.36 per user/month at scale
- **Developer Velocity:** Daily deployments vs manual releases

---

## 📁 Documentation

### Quick Reference
- **[SUMMARY.md](SUMMARY.md)** - Quick reference guide 📋
  - 15 microservices overview
  - Cost vs revenue model
  - Technology stack summary
  - Implementation timeline (12 months)
  - Success metrics

### Requirements
- **[01-requirements.md](01-requirements.md)** - Complete requirements ✅
  - Architecture vision & problems solved
  - 15 microservices breakdown (detailed specs)
  - Database architecture (PostgreSQL, MongoDB, Redis, ClickHouse)
  - Inter-service communication (REST + Kafka)
  - Deployment architecture (Kubernetes, CI/CD)
  - Security & compliance (SOC 2, PCI DSS, GDPR)
  - Cost estimation by scale ($360/mo → $5K/mo)
  - Implementation timeline (5 phases, 12 months)

### Status
- **[_status.md](_status.md)** - Current phase and progress
  - Phase: REQUIREMENTS (DRAFT)
  - Progress: Requirements drafted ✅
  - Next: User approval

---

## 🏗️ Architecture Highlights

### Current Problems
- Magento backend (overkill, slow, expensive)
- Mock AI (no real value)
- Manual scraping (doesn't scale)
- SQLite local storage (sync issues)
- Single ICP blockchain (expensive, slow)

### New Architecture
- **15 Microservices** (FastAPI Python)
- **Multi-Database** (PostgreSQL, MongoDB, Redis, ClickHouse)
- **Event-Driven** (Kafka for async communication)
- **Kubernetes** (auto-scaling, HA)
- **Real ML** (4+ models: redemption, risk, price, portfolio)
- **Multi-Chain** (Polygon, Ethereum, ICP)

---

## 💰 Business Case

### Infrastructure Costs

| Scale | Monthly Cost | Per-User Cost |
|-------|-------------|---------------|
| 1,000 users | $360 | $0.36 |
| 10,000 users | $1,080 | $0.11 |
| 100,000 users | $5,000 | $0.05 |

### Revenue Projection (100K users)

```
100,000 users × 10% conversion = 10,000 paying
10,000 × $49.99 ARPU = $499,900 MRR

Infrastructure: -$5,000/mo
Salaries (15 ppl): -$125,000/mo
Other costs: -$10,000/mo

NET PROFIT: $359,900/mo
ANNUAL: $4.3M profit (73% margin)
```

**ROI:** Infrastructure cost is 1% of revenue at scale.

---

## 📋 15 Microservices

### Core Services
1. **API Gateway** - Rate limiting, auth, routing
2. **Auth Service** - JWT, OAuth, 2FA
3. **User Service** - Profiles, KYC/AML
4. **Search Service** - Elasticsearch, <50ms
5. **Payment Service** - Stripe, subscriptions

### Data Services
6. **Scraper Service** - Distributed, 100K props/day
7. **Data Pipeline** - Airflow ETL, ClickHouse warehouse
8. **ML Service** - 4 models (redemption, risk, price, portfolio)

### Feature Services
9. **NFT Service** - Multi-chain tokenization
10. **Data API** - B2B monetization
11. **Analytics Service** - BI dashboards
12. **Notification Service** - Email, SMS, push

### Client Apps
13. **Mobile App** - Flutter (iOS/Android)
14. **Web App** - Next.js (marketing + platform)
15. **Admin Dashboard** - Next.js (ops, support)

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (Python) |
| **Frontend** | Flutter (mobile), Next.js (web) |
| **Databases** | PostgreSQL, MongoDB, Redis, ClickHouse |
| **Message Bus** | Kafka / AWS EventBridge |
| **Search** | Elasticsearch / Meilisearch |
| **ML** | scikit-learn, TensorFlow, MLflow |
| **Blockchain** | Web3.py, Polygon, Ethereum |
| **Orchestration** | Kubernetes, Helm, ArgoCD |
| **Monitoring** | Prometheus, Grafana, Datadog |
| **Payments** | Stripe Connect |

---

## 📅 Implementation Timeline

### Phase 1: Foundation (Months 1-2)
- Kubernetes cluster, databases
- Auth Service, User Service
- API Gateway, CI/CD
- **Deliverable:** Users can signup/login

### Phase 2: Data (Months 2-4)
- Rebuild Scraper (distributed)
- Data Pipeline (Airflow)
- Search Service (Elasticsearch)
- **Deliverable:** 100+ counties scraped

### Phase 3: Features (Months 4-6)
- Mobile app rebuild
- Educational content
- ML Service (real models)
- Payment Service
- **Deliverable:** MVP beta launch

### Phase 4: Monetization (Months 6-8)
- Subscriptions, educational store
- Transaction fees, NFT minting
- Data API (B2B)
- **Deliverable:** $10K+ MRR

### Phase 5: Scale (Months 8-12)
- NFT Marketplace
- Advanced ML, Admin dashboard
- Multi-language, SOC 2
- **Deliverable:** $50K+ MRR

---

## 🎯 Success Metrics

### Technical KPIs
- API Latency (p95): <200ms
- Uptime: 99.9%
- Error Rate: <0.1%
- Scraper Success: >95%

### Business KPIs (Month 12)
- Total Users: 10,000
- Paying Users: 1,000 (10%)
- MRR: $50,000
- CAC: <$30
- LTV: >$800
- Churn: <4%

---

## ⚠️ Critical Decisions

### 1. Build vs Buy
- [ ] API Gateway: Kong (OSS) vs AWS (managed)?
- [ ] Message Bus: Kafka (self-host) vs EventBridge (managed)?
- [ ] Monitoring: Prometheus (free) vs Datadog (easy)?

### 2. Hosting
- [ ] Cloud: AWS (expensive) vs DigitalOcean (cheap) vs Hybrid?
- [ ] Kubernetes: Managed (EKS) vs Self-managed?

### 3. Migration
- [ ] Big Bang (risky) vs Strangler (safe) vs Parallel (expensive)?

### 4. Team
- [ ] Hire specialists vs upskill existing team?
- [ ] Contractors vs full-time?

---

## 🔗 Related SDD Flows

### Individual Service SDDs (to be created)
Each microservice will have its own SDD flow under `flows/sdd-{service-name}/`

### Active Flows
- ✅ [sdd-mobile-app](../sdd-mobile-app/) - Requirements complete
- 🔄 [sdd-ml-service](../sdd-ml-service/) - In progress
- 🔄 [sdd-data-structure](../sdd-data-structure/) - In progress
- 🔄 [sdd-scraper-service](../sdd-scraper-service/) - In progress

---

## 📞 Quick Links

**Master Architecture:**
- [Requirements](01-requirements.md) - Full architecture specification (1,353 lines)
- [Summary](SUMMARY.md) - Quick reference
- [Status](_status.md) - Current phase, blockers

**Comparison:**
- Current system: Monolithic, single-server, manual deployments
- New system: Microservices, Kubernetes, CI/CD, 1000x scalability

---

**Last Updated:** 2025-12-31 by Claude (AI Assistant)
**Current Status:** REQUIREMENTS drafted ✅
**Next Milestone:** User approval → Create individual service SDDs
**Timeline:** 12 months to production
**Investment:** ~$60K infrastructure + team costs Year 1
**Expected ROI:** $4.3M profit at 100K users (72x return)
