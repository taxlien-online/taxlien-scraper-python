# System Architecture SDD - Quick Reference

> Last Updated: 2025-12-31
> Status: REQUIREMENTS phase (DRAFT)

## 🎯 One-Liner

Полная переработка TAXLIEN.online в **cloud-native microservices платформу**, масштабируемую от 100 до 1M+ пользователей с линейными затратами.

---

## 🏗️ Architecture Vision

### From → To

| Aspect | Current (Monolith) | Target (Microservices) |
|--------|-------------------|------------------------|
| **Backend** | Magento (PHP) | FastAPI microservices (Python) |
| **Frontend** | Flutter app + web | Flutter + Next.js + Admin Dashboard |
| **Database** | SQLite local + MySQL | PostgreSQL + MongoDB + Redis + ClickHouse |
| **AI/ML** | Mock data | Real ML pipeline (4+ models) |
| **Scraping** | Manual, limited | Distributed cluster (100K props/day) |
| **Deployment** | Single server | Kubernetes cluster (auto-scaling) |
| **Blockchain** | ICP only | Multi-chain (Polygon, Ethereum, ICP) |

---

## 📦 15 Microservices Overview

### Core Services (Must-Have)
1. **API Gateway** - Single entry point, rate limiting, auth validation
2. **Auth Service** - JWT, OAuth, 2FA, email verification
3. **User Service** - Profiles, preferences, KYC/AML
4. **Search Service** - Elasticsearch, <50ms response time
5. **Payment Service** - Stripe, subscriptions, transaction fees

### Data Services
6. **Scraper Service** - Distributed scraping (Celery + Redis)
7. **Data Pipeline** - ETL (Airflow), data warehouse (ClickHouse)
8. **ML Service** - 4 models (redemption, risk, price, portfolio)

### Feature Services
9. **NFT Service** - Multi-chain tokenization, marketplace
10. **Data API** - B2B data monetization ($99-999/mo)
11. **Analytics Service** - BI dashboards, metrics tracking
12. **Notification Service** - Email, SMS, push notifications

### Client Apps
13. **Mobile App** - Flutter (iOS/Android)
14. **Web App** - Next.js (marketing + web platform)
15. **Admin Dashboard** - Next.js (ops, support, monitoring)

---

## 💰 Cost vs Revenue Model

### Infrastructure Costs (Monthly)

| Scale | Users | Cost | Per-User Cost |
|-------|-------|------|---------------|
| **Small** | 1K | $360 | $0.36 |
| **Medium** | 10K | $1,080 | $0.11 |
| **Large** | 100K | $5,000 | $0.05 |

### Revenue Model (100K users scenario)

```
100,000 total users
× 10% conversion = 10,000 paying users
× $49.99 ARPU = $499,900 MRR

Infrastructure: -$5,000
Other costs: -$10,000 (15 employees @ $100K salary = ~$8,333/mo salaries)

NET PROFIT: ~$485,000/mo (97% margin)
ANNUAL: ~$5.8M profit
```

**ROI:** Infrastructure costs scale linearly, revenue scales exponentially.

---

## 🗄️ Database Strategy

### PostgreSQL (Primary OLTP)
- Users, subscriptions, transactions
- Tax lien metadata (structured)
- Partitioning by county/date
- Read replicas for analytics

### MongoDB (Document Store)
- Raw scraped HTML (debugging)
- Logs, unstructured data
- Sharding by county

### Redis (Cache & Queues)
- API response caching
- Rate limiting
- Session storage
- Celery broker

### ClickHouse (OLAP Warehouse)
- Business analytics
- ML training data
- Historical reporting
- 10B+ rows, <1s queries

### S3/MinIO (Object Storage)
- Images, PDFs, videos
- ML model artifacts
- Database backups

---

## 🔄 Inter-Service Communication

### Synchronous (REST)
```
Client → API Gateway → Service → Response
Timeout: 5s max
Retry: 3 attempts with exponential backoff
```

### Asynchronous (Event Bus)
```
Kafka / EventBridge

Events:
- user.subscribed → Notification, Analytics, Payment
- lien.created → Search indexing, ML scoring, Alerts
- scrape.completed → Data pipeline, Analytics
```

---

## 🚀 Implementation Timeline (12 Months)

### Phase 1: Foundation (Months 1-2)
- ✅ Core infrastructure (K8s, databases)
- ✅ Auth Service
- ✅ User Service
- ✅ API Gateway
- **Deliverable:** Users can signup/login

### Phase 2: Data Ingestion (Months 2-4)
- Rebuild Scraper Service (distributed)
- Data Pipeline (Airflow)
- Search Service (Elasticsearch)
- **Deliverable:** 100+ counties scraped

### Phase 3: Core Features (Months 4-6)
- Mobile app rebuild (Flutter)
- Educational content system
- ML Service (real models)
- Payment Service
- **Deliverable:** MVP beta launch

### Phase 4: Monetization (Months 6-8)
- Subscription tiers
- Educational products store
- Transaction fees
- NFT minting
- Data API (B2B)
- **Deliverable:** $10K+ MRR

### Phase 5: Scale (Months 8-12)
- NFT Marketplace
- Advanced ML
- Admin dashboard
- Multi-language
- SOC 2 compliance
- **Deliverable:** $50K+ MRR, 10K+ users

---

## 🎯 Success Metrics

### Technical KPIs
| Metric | Target |
|--------|--------|
| API Latency (p95) | <200ms |
| Uptime | 99.9% |
| Error Rate | <0.1% |
| Scraper Success | >95% |
| Deployment Freq | Daily |

### Business KPIs (12-Month Targets)
| Metric | Target |
|--------|--------|
| Total Users | 10,000 |
| Paying Users | 1,000 (10% conversion) |
| MRR | $50,000 |
| CAC | <$30 |
| LTV | >$800 |
| Churn | <4% |

---

## 🔒 Security & Compliance

### Security Layers
- HTTPS/TLS 1.3 everywhere
- JWT authentication (15min access, 30day refresh)
- API Gateway (WAF, DDoS protection)
- Private subnets (services not internet-accessible)
- Encryption at rest & in transit
- Secrets management (AWS Secrets Manager)

### Compliance Roadmap
- [ ] SOC 2 Type II (Month 12)
- [ ] PCI DSS Level 1 (for payments)
- [ ] GDPR compliant (EU users)
- [ ] CCPA compliant (California users)

---

## 🛠️ Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| **Frontend** | Flutter (mobile), Next.js (web) |
| **Backend** | FastAPI (Python) |
| **API Gateway** | Kong / AWS API Gateway |
| **Message Bus** | Kafka / AWS EventBridge |
| **Databases** | PostgreSQL, MongoDB, Redis, ClickHouse |
| **Storage** | S3 / MinIO |
| **Search** | Elasticsearch / Meilisearch |
| **ML** | scikit-learn, TensorFlow, PyTorch, MLflow |
| **Scraping** | Selenium, Celery, BeautifulSoup |
| **Blockchain** | Web3.py, Polygon, Ethereum |
| **Orchestration** | Kubernetes, Helm, ArgoCD |
| **CI/CD** | GitHub Actions, Docker |
| **Monitoring** | Prometheus, Grafana, Datadog, Sentry |
| **Payments** | Stripe, Stripe Connect |

---

## 🔗 Related SDD Flows

### Individual Service SDDs (to be created)
- [sdd-api-gateway/](../sdd-api-gateway/)
- [sdd-auth-service/](../sdd-auth-service/)
- [sdd-user-service/](../sdd-user-service/)
- [sdd-scraper-service/](../sdd-scraper-service/)
- [sdd-ml-service/](../sdd-ml-service/)
- [sdd-search-service/](../sdd-search-service/)
- [sdd-payment-service/](../sdd-payment-service/)
- [sdd-nft-service/](../sdd-nft-service/)
- [sdd-data-api-service/](../sdd-data-api-service/)
- [sdd-analytics-service/](../sdd-analytics-service/)
- [sdd-notification-service/](../sdd-notification-service/)
- [sdd-mobile-app/](../sdd-mobile-app/)
- [sdd-web-app/](../sdd-web-app/)
- [sdd-admin-dashboard/](../sdd-admin-dashboard/)
- [sdd-data-pipeline/](../sdd-data-pipeline/)

### Completed/Active SDDs
- ✅ [sdd-mobile-app/](../sdd-mobile-app/) - Requirements COMPLETE
- 🔄 [sdd-ml-service/](../sdd-ml-service/) - In progress
- 🔄 [sdd-data-structure/](../sdd-data-structure/) - In progress
- 🔄 [sdd-scraper-service/](../sdd-scraper-service/) - In progress

---

## ⚠️ Critical Decisions Needed

### 1. Build vs Buy
- [ ] **API Gateway:** Kong (open-source) vs AWS API Gateway (managed)?
- [ ] **Message Bus:** Kafka (self-hosted) vs AWS EventBridge (managed)?
- [ ] **Monitoring:** Prometheus+Grafana (free) vs Datadog (expensive but easier)?

### 2. Hosting Strategy
- [ ] **Cloud Provider:** AWS (expensive) vs DigitalOcean (cheaper) vs Hybrid?
- [ ] **Kubernetes:** Managed (EKS/GKE) vs Self-managed?

### 3. Migration Strategy
- [ ] **Big Bang:** Shut down old, launch new (risky)
- [ ] **Strangler Pattern:** Gradually replace services (safer, slower)
- [ ] **Parallel Run:** Both systems running, gradual user migration (expensive)

### 4. Team Structure
- [ ] Hire specialists (expensive, fast) vs upskill existing team (cheaper, slower)?
- [ ] Contractors (Upwork/Fiverr) vs full-time employees?

---

## 📊 Comparison with Current System

| Aspect | Current | New Architecture | Benefit |
|--------|---------|------------------|---------|
| **Scalability** | 1K users max | 1M+ users | 1000x |
| **Cost/User** | $5-10/mo | $0.05-0.36/mo | 10-100x cheaper |
| **API Speed** | 500-2000ms | <200ms | 10x faster |
| **AI Quality** | Mock data | Real ML models | Infinitely better |
| **Scraping** | Manual | Automated, 100K/day | 100x throughput |
| **Deployment** | Manual | CI/CD, daily | 10x frequency |
| **Uptime** | 95%? | 99.9% | 50x less downtime |

---

## 📝 Next Steps

### For User Review
1. **Validate Architecture:** Is microservices approach right for us?
2. **Prioritize Services:** Which to build first? (Recommend: Auth → Scraper → ML → NFT)
3. **Budget Approval:** $5K/mo infrastructure + team costs
4. **Timeline Feasibility:** 12 months acceptable?

### For Development
1. **Create Individual SDDs:** One for each microservice
2. **Define API Contracts:** OpenAPI specs for inter-service communication
3. **Database Schema Design:** ER diagrams, migrations
4. **Prototype Core Services:** Auth + API Gateway + one feature service
5. **Setup Infrastructure:** K8s cluster, databases, monitoring

---

**Last Updated:** 2025-12-31 by Claude (AI Assistant)
**Current Status:** Architecture REQUIREMENTS drafted, awaiting approval
**Next Milestone:** Break down into individual service SDDs
**Timeline:** 12 months to production-ready system
**Investment:** ~$60K infrastructure + team costs Year 1
**Expected ROI:** $5.8M profit at 100K users (97x return)
