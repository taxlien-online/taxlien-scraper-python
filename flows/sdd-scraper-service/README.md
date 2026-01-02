# SDD: Scraper Service - Multi-Platform Support

> Parser/Scraper infrastructure for 15+ county property tax platforms
> Status: Requirements Complete ✅
> Last Updated: 2025-12-31

## 🎯 Overview

This SDD defines the scraper/parser service architecture for TAXLIEN.online, supporting 15+ county property tax platforms with unified interface.

**Key Features:**
- **15+ platform support** (QPublic, Beacon, Tyler, Custom GIS, PropertyMax, Civic Source, etc.)
- **BaseParser architecture** for unified platform integration
- **PropertyData model** (90+ attributes standardized)
- **95%+ parse success rate** target
- **JavaScript rendering support** for custom GIS systems
- **Year 1 goal:** 3,000+ counties, 25M+ properties

## 📁 Documentation

### Platform Support
- **[01-platform-support.md](01-platform-support.md)** - Comprehensive platform coverage strategy
  - Current state: 4 platforms implemented (QPublic, Beacon, Bid4Assets, Tyler)
  - Target: 15 platforms by Year 1
  - BaseParser abstract class (full implementation)
  - CustomGISParser for Union/Columbia County FL (322 samples)
  - Platform priority matrix
  - Implementation roadmap

## 🏗️ Architecture

### BaseParser Pattern

All platform-specific parsers inherit from `BaseParser` abstract class:

```python
class BaseParser(ABC):
    @abstractmethod
    def get_parcel_list() -> List[str]

    @abstractmethod
    def scrape_parcel(parcel_id: str) -> str

    @abstractmethod
    def parse_html(html: str) -> PropertyData

    def validate_data(data: PropertyData) -> bool
    def save_to_mongodb(html: str)
    def save_to_postgresql(data: PropertyData)
```

### Platform Implementations

**Already Done:**
1. QPublicParser (35+ counties)
2. BeaconParser (20+ counties)
3. Bid4AssetsParser (auction platform)
4. TylerTechnologiesParser (50+ counties)

**Priority 1 (Next):**
5. **CustomGISParser** (Union/Columbia FL - 322 samples)
6. PropertyMaxParser (100+ counties)
7. CivicSourceParser (500+ counties)
8. RealTaxDataParser (50+ counties)
9. VanguardParser (200+ TX counties)
10. eGovStrategiesParser (100+ counties)

**Priority 2 (Future):**
11-15. Azteca, MatrixAppraisal, VisionGov, DEVNET, MyFloridaCounty

## 📊 Coverage Goals

| Timeframe | Platforms | Counties | Properties |
|-----------|-----------|----------|------------|
| Week 1-2 | 5 (add CustomGIS) | 350+ | 322 samples parsed |
| Month 1 | 5 | 350+ | 1,000 |
| Month 3 | 8 | 1,000+ | 10,000 |
| Month 6 | 12 | 2,000+ | 100,000 |
| Year 1 | 15 | 3,000+ | 25,000,000+ |

## 🎯 Success Metrics

**Parser Quality:**
- ✅ 95%+ successful parse rate
- ✅ 90%+ field coverage (90+ attributes)
- ✅ <2% error rate
- ✅ <5 sec average parse time

**Data Quality:**
- ✅ 99%+ parcel ID uniqueness
- ✅ 95%+ owner name extraction
- ✅ 90%+ assessed value extraction
- ✅ 85%+ tax amount extraction
- ✅ 70%+ property details (sqft, year built)

## 🔗 Related SDDs

- **[sdd-data-structure](../sdd-data-structure/)** - Database schemas, 90+ attributes spec
- **[sdd-data-pipeline](../sdd-data-pipeline/)** - ETL workflow, scraping → parsing → storage

## 🚀 Next Steps

1. **Implement CustomGISParser** (using 322 samples for testing)
2. **Test on Union County FL** (214 parcels)
3. **Test on Columbia County FL** (108 parcels)
4. **Achieve 95%+ parse success rate**
5. **Begin PropertyMax, Civic Source parsers**

---

**Status:** REQUIREMENTS COMPLETE
**Phase:** Ready for SPECIFICATIONS
**Blocker:** None
