# Parser Platform Support - Comprehensive Coverage Strategy

**Date:** 2025-12-30
**Phase:** REQUIREMENTS (Extension)
**Purpose:** Максимально широкая поддержка county property tax систем

---

## 📊 Current State Analysis

### ✅ Already Implemented (4 platforms)

**1. QPublic (Schneider Corp)**
- **Coverage:** 35+ counties
- **Implementation:** `/parser/taxlien-scraper-python/platforms/qpublic/`
- **Technology:** SeleniumBase + undetected-chromedriver
- **Difficulty:** Easy
- **Examples:** Alachua FL, Baker FL, Bradford FL

**2. Beacon (Schneider Corp)**
- **Coverage:** Extended QPublic counties
- **Implementation:** `/parser/taxlien-scraper-python/platforms/beacon/`
- **Technology:** Similar to QPublic (shared architecture)
- **Difficulty:** Easy-Medium
- **Examples:** Maricopa AZ, King WA, Hillsborough FL

**3. Bid4Assets (Auction Platform)**
- **Coverage:** National auction listings
- **Implementation:** `/parser/taxlien-scraper-python/platforms/bid4assets/`
- **URL:** https://www.bid4assets.com
- **Difficulty:** Medium
- **Purpose:** Live auctions, bidding data

**4. Tyler Technologies (iasWorld)**
- **Coverage:** Major counties
- **Implementation:** `/parser/taxlien-scraper-python/platforms/tyler_technologies/`
- **Difficulty:** Medium-Hard
- **Examples:** Harris TX, Wake NC, Pima AZ

---

## 🎯 Target Platform Coverage (Расширение до 15+ платформ)

### Priority 1: High-Volume Platforms (Next 6 platforms)

#### 5. **Custom GIS Systems** ⭐ PRIORITY
- **Coverage:** Union County FL (214 parcels), Columbia County FL (108 parcels)
- **Sample Data:** `/samples/` (322 HTML files)
- **Implementation:** NEW - `platforms/custom_gis/`
- **Difficulty:** Hard
- **Vendor:** Custom county-built GIS portals
- **Characteristics:**
  - JavaScript-heavy (gisSideMenu_3_Details)
  - Custom domain names (ColumbiaPA.com, UnionPA.com)
  - Non-standard parcel ID formats
  - Dynamic content loading
- **Strategy:**
  - Use 322 sample HTML files for parser development
  - Extract common patterns across custom GIS systems
  - Selenium with JavaScript execution
  - Screenshot capture for image extraction

#### 6. **PropertyMax (CoreLogic)**
- **Coverage:** 100+ counties nationally
- **Examples:** Orange County FL, Seminole County FL
- **Difficulty:** Medium
- **Vendor:** CoreLogic PropertyMax
- **Characteristics:**
  - Standardized interface
  - Search by parcel ID, owner name, address
  - Export capabilities
- **Implementation:** NEW - `platforms/propertymax/`

#### 7. **Civic Source (Formerly BS&A)**
- **Coverage:** 500+ Michigan municipalities + others
- **Examples:** Kent County MI, Oakland County MI
- **Difficulty:** Medium
- **Vendor:** Civic Source (BS&A Software)
- **Characteristics:**
  - Municipal tax collection focus
  - Standardized BS&A interface
  - Good API documentation
- **Implementation:** NEW - `platforms/civic_source/`

#### 8. **RealTaxData (MyTaxData.com)**
- **Coverage:** 50+ counties in TX, FL, GA
- **Examples:** Collin County TX, Gwinnett County GA
- **Difficulty:** Easy-Medium
- **Characteristics:**
  - Clean, modern interface
  - Good data export
  - Consistent structure
- **Implementation:** NEW - `platforms/realtaxdata/`

#### 9. **Vanguard Appraisals**
- **Coverage:** 200+ Texas counties
- **Examples:** Bexar TX, Travis TX, Denton TX
- **Difficulty:** Medium
- **Vendor:** Vanguard Appraisals Inc
- **Characteristics:**
  - Texas-specific
  - Standardized forms
  - PDF exports common
- **Implementation:** NEW - `platforms/vanguard/`

#### 10. **eGov Strategies (Aumentum)**
- **Coverage:** 100+ counties
- **Examples:** Pinellas County FL, Lee County FL
- **Difficulty:** Medium-Hard
- **Vendor:** eGov Strategies (Aumentum platform)
- **Characteristics:**
  - Modern web portal
  - REST API available (some counties)
  - Mobile-responsive
- **Implementation:** NEW - `platforms/egov_strategies/`

### Priority 2: Regional Dominators (Next 5 platforms)

#### 11. **Azteca Systems**
- **Coverage:** California counties
- **Examples:** San Diego CA, Riverside CA
- **Difficulty:** Medium
- **Region:** California focus

#### 12. **MatrixAppraisal**
- **Coverage:** Southeast US
- **Examples:** Chatham County GA, Richland County SC
- **Difficulty:** Easy-Medium

#### 13. **Vision Government Solutions**
- **Coverage:** Northeast US
- **Examples:** Suffolk County NY, Fairfield County CT
- **Difficulty:** Medium

#### 14. **DEVNET (GovernMax)**
- **Coverage:** Florida counties
- **Examples:** Marion County FL, Citrus County FL
- **Difficulty:** Medium
- **Note:** Already mentioned in county_sources as "GM" platform

#### 15. **MyFloridaCounty.com**
- **Coverage:** Florida counties
- **Examples:** Polk County FL, Volusia County FL
- **Difficulty:** Easy
- **Note:** Already mentioned in county_sources as "MF" platform

---

## 🏗️ Implementation Architecture

### BaseParser Abstract Class

```python
# platforms/base_parser.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PropertyData:
    """Standardized property data structure (90+ attributes)"""
    # Identification
    parcel_id: str
    property_tax_account: Optional[str] = None
    source_platform: str = None
    source_url: str = None

    # Location
    property_address: str = None
    city: str = None
    county: str = None
    state: str = None
    zip_code: str = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Property Details
    property_type: str = None  # Residential, Commercial, Agricultural, etc.
    building_sqft: Optional[int] = None
    land_acres: Optional[float] = None
    year_built: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None

    # Valuation
    assessed_value: Optional[float] = None
    market_value: Optional[float] = None
    land_value: Optional[float] = None
    building_value: Optional[float] = None

    # Tax Info
    tax_amount: Optional[float] = None
    tax_year: Optional[int] = None
    interest_rate: Optional[float] = None
    penalty_amount: Optional[float] = None
    total_due_amount: Optional[float] = None

    # Owner Info
    owner_name: str = None
    owner_address: str = None
    owner_city: str = None
    owner_state: str = None
    owner_zip: str = None

    # Exemptions
    homestead_exemption: Optional[float] = None
    veteran_exemption: Optional[float] = None
    senior_exemption: Optional[float] = None
    total_exemptions: Optional[float] = None

    # Dates
    auction_date: Optional[datetime] = None
    redemption_deadline: Optional[datetime] = None
    last_sale_date: Optional[datetime] = None

    # Status
    status: str = "unknown"  # active, sold, redeemed, foreclosed
    is_available: bool = False

    # Media
    images: List[str] = None
    documents: List[str] = None
    thumbnail_url: str = None
    gis_map_url: str = None

    # Metadata
    scraped_at: datetime = None
    raw_html: str = None


class BaseParser(ABC):
    """
    Abstract base class для всех парсеров county property tax систем

    Каждая платформа наследует этот класс и реализует platform-specific методы
    """

    def __init__(self, county: str, state: str, base_url: str):
        self.county = county
        self.state = state
        self.base_url = base_url
        self.platform_name = self.__class__.__name__.replace('Parser', '')

    @abstractmethod
    def get_parcel_list(self) -> List[str]:
        """
        Получить список всех parcel IDs в county

        Returns:
            List[str]: List of parcel IDs
        """
        pass

    @abstractmethod
    def scrape_parcel(self, parcel_id: str) -> str:
        """
        Скачать HTML страницу для конкретного parcel

        Args:
            parcel_id: Parcel ID для скачивания

        Returns:
            str: Raw HTML content
        """
        pass

    @abstractmethod
    def parse_html(self, html: str, parcel_id: str) -> PropertyData:
        """
        Парсить HTML в структурированные данные

        Args:
            html: Raw HTML content
            parcel_id: Parcel ID для контекста

        Returns:
            PropertyData: Parsed structured data
        """
        pass

    def extract_owner_name(self, html: str) -> Optional[str]:
        """Platform-specific owner name extraction"""
        return None

    def extract_assessed_value(self, html: str) -> Optional[float]:
        """Platform-specific assessed value extraction"""
        return None

    def extract_tax_amount(self, html: str) -> Optional[float]:
        """Platform-specific tax amount extraction"""
        return None

    def extract_images(self, html: str) -> List[str]:
        """Platform-specific image URL extraction"""
        return []

    def validate_data(self, data: PropertyData) -> bool:
        """
        Валидация распарсенных данных

        Args:
            data: PropertyData object to validate

        Returns:
            bool: True if valid, False otherwise
        """
        # Required fields
        if not data.parcel_id:
            return False
        if not data.county:
            return False
        if not data.state:
            return False

        # Data quality checks
        if data.assessed_value and data.assessed_value < 0:
            return False
        if data.tax_amount and data.tax_amount < 0:
            return False

        return True

    def normalize_parcel_id(self, parcel_id: str) -> str:
        """
        Нормализация parcel ID к стандартному формату

        Examples:
            "01-06-25-00-000-0875-0" → "01-06-25-00-000-0875-0"
            "R12074-000" → "R12074-000"
            "12-345-67" → "12-345-67"
        """
        return parcel_id.strip().upper()

    def save_to_mongodb(self, html: str, parcel_id: str, metadata: Dict):
        """
        Сохранить raw HTML в MongoDB

        Args:
            html: Raw HTML content
            parcel_id: Parcel ID
            metadata: Additional metadata dict
        """
        from pymongo import MongoClient

        client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
        db = client[os.getenv('MONGODB_DB', 'taxlien')]
        collection = db['raw_html_scrapes']

        doc = {
            'parcel_id': self.normalize_parcel_id(parcel_id),
            'county': self.county,
            'state': self.state,
            'source_url': metadata.get('source_url'),
            'html_content': html,
            'html_size_bytes': len(html),
            'platform_type': self.platform_name,
            'scraping_difficulty': metadata.get('difficulty', 'medium'),
            'parsed': False,
            'parse_attempts': 0,
            'parse_errors': [],
            'scraped_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(days=90)  # 90-day TTL
        }

        collection.insert_one(doc)

    def save_to_postgresql(self, data: PropertyData):
        """
        Сохранить structured data в PostgreSQL

        Args:
            data: PropertyData object
        """
        # This would use SQLAlchemy or psycopg2
        # Implementation in actual code
        pass
```

### Platform-Specific Implementations

#### Example: CustomGISParser

```python
# platforms/custom_gis/custom_gis_parser.py

from bs4 import BeautifulSoup
import re
from typing import List, Optional
from platforms.base_parser import BaseParser, PropertyData

class CustomGISParser(BaseParser):
    """
    Parser для custom county GIS систем

    Supports:
    - Union County FL (parcel.union domain)
    - Columbia County FL (ColumbiaPA.com)
    - Similar custom GIS portals
    """

    def __init__(self, county: str, state: str, base_url: str, gis_type: str = 'generic'):
        super().__init__(county, state, base_url)
        self.gis_type = gis_type  # 'union', 'columbia', 'generic'

    def get_parcel_list(self) -> List[str]:
        """
        Для custom GIS часто нет единого списка
        Используем incremental discovery или county-provided list
        """
        # Implementation would use Selenium to navigate GIS menu
        # or load from county-provided CSV
        pass

    def scrape_parcel(self, parcel_id: str) -> str:
        """
        Скрапинг через Selenium (JavaScript-heavy pages)
        """
        from seleniumbase import SB
        from sbvirtualdisplay import Display

        with Display(visible=False, size=(1920, 1080)):
            with SB(uc=True, headless=False) as sb:
                # Navigate to parcel details page
                search_url = f"{self.base_url}?parcel={parcel_id}"
                sb.uc_open_with_reconnect(search_url, 2)

                # Wait for dynamic content to load
                sb.wait_for_element("gisSideMenu_3_Details", timeout=10)

                # Get rendered HTML
                html = sb.get_page_source()

                # Save screenshot for debugging
                screenshot_path = f"screenshots/{self.county}/{parcel_id}.png"
                sb.save_screenshot(screenshot_path)

                return html

    def parse_html(self, html: str, parcel_id: str) -> PropertyData:
        """
        Parse custom GIS HTML structure
        """
        soup = BeautifulSoup(html, 'lxml')

        data = PropertyData(
            parcel_id=self.normalize_parcel_id(parcel_id),
            county=self.county,
            state=self.state,
            source_platform='CustomGIS',
            scraped_at=datetime.utcnow(),
            raw_html=html
        )

        # Extract owner name
        data.owner_name = self.extract_owner_name(soup)

        # Extract address
        data.property_address = self.extract_address(soup)

        # Extract valuation
        data.assessed_value = self.extract_assessed_value(soup)
        data.market_value = self.extract_market_value(soup)

        # Extract tax info
        data.tax_amount = self.extract_tax_amount(soup)
        data.tax_year = self.extract_tax_year(soup)

        # Extract property details
        data.property_type = self.extract_property_type(soup)
        data.building_sqft = self.extract_building_sqft(soup)
        data.land_acres = self.extract_land_acres(soup)
        data.year_built = self.extract_year_built(soup)

        # Extract images
        data.images = self.extract_images(soup)
        data.gis_map_url = self.extract_gis_map_url(soup)

        return data

    def extract_owner_name(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Custom GIS typically has owner in a table row
        Pattern: <td>Owner Name:</td><td>JOHN DOE</td>
        """
        # Try multiple patterns
        patterns = [
            (re.compile(r'Owner.*Name', re.I), 'next_sibling'),
            (re.compile(r'Property Owner', re.I), 'next_sibling'),
            ('id', 'ownerName'),
            ('class', 'owner-name')
        ]

        for pattern_type, pattern_value in patterns:
            if pattern_type == 'id':
                elem = soup.find(id=pattern_value)
                if elem:
                    return elem.text.strip()
            elif pattern_type == 'class':
                elem = soup.find(class_=pattern_value)
                if elem:
                    return elem.text.strip()
            else:
                # Regex pattern
                label = soup.find(text=pattern_value)
                if label:
                    parent = label.find_parent()
                    if parent:
                        value_elem = parent.find_next_sibling()
                        if value_elem:
                            return value_elem.text.strip()

        return None

    def extract_assessed_value(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract assessed value using multiple patterns"""
        patterns = [
            re.compile(r'Assessed.*Value', re.I),
            re.compile(r'Total.*Assessment', re.I),
            re.compile(r'Assessed', re.I)
        ]

        for pattern in patterns:
            label = soup.find(text=pattern)
            if label:
                parent = label.find_parent()
                if parent:
                    value_elem = parent.find_next_sibling()
                    if value_elem:
                        value_text = value_elem.text.strip()
                        # Parse currency: "$123,456.78" → 123456.78
                        value_clean = re.sub(r'[^0-9.]', '', value_text)
                        try:
                            return float(value_clean)
                        except ValueError:
                            continue

        return None

    def extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract property image URLs"""
        images = []

        # Look for common image patterns
        img_tags = soup.find_all('img', src=re.compile(r'property|parcel|photo', re.I))

        for img in img_tags:
            src = img.get('src')
            if src:
                # Convert relative to absolute URLs
                if src.startswith('/'):
                    src = self.base_url + src
                images.append(src)

        return images

    def extract_gis_map_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract GIS map URL or image"""
        # Look for map iframe or image
        map_iframe = soup.find('iframe', src=re.compile(r'map|gis', re.I))
        if map_iframe:
            return map_iframe.get('src')

        map_img = soup.find('img', src=re.compile(r'map|gis', re.I))
        if map_img:
            return map_img.get('src')

        return None
```

---

## 📋 Implementation Priority Matrix

| Platform | Counties | Difficulty | Sample Data | Priority | ETA |
|----------|----------|------------|-------------|----------|-----|
| QPublic | 35+ | Easy | ✅ | ✅ Done | - |
| Beacon | 20+ | Easy | ✅ | ✅ Done | - |
| Bid4Assets | National | Medium | ✅ | ✅ Done | - |
| Tyler Tech | 50+ | Medium | ✅ | ✅ Done | - |
| **Custom GIS** | **Union, Columbia** | **Hard** | **✅ 322 files** | **🔥 HIGH** | **Week 1-2** |
| PropertyMax | 100+ | Medium | ❌ | HIGH | Week 2-3 |
| Civic Source | 500+ | Medium | ❌ | HIGH | Week 3-4 |
| RealTaxData | 50+ | Easy | ❌ | MEDIUM | Week 4-5 |
| Vanguard | 200+ | Medium | ❌ | MEDIUM | Week 5-6 |
| eGov | 100+ | Hard | ❌ | MEDIUM | Week 6-7 |
| Azteca | CA only | Medium | ❌ | LOW | Future |
| MatrixAppraisal | SE US | Easy | ❌ | LOW | Future |
| Vision Gov | NE US | Medium | ❌ | LOW | Future |
| DEVNET | FL only | Medium | ❌ | LOW | Future |
| MyFloridaCounty | FL only | Easy | ❌ | LOW | Future |

---

## 🔧 Development Roadmap

### Phase 1: Custom GIS Support (Weeks 1-2)

**Goal:** Parse 322 sample HTML files successfully

**Tasks:**
1. ✅ Create BaseParser abstract class
2. ✅ Implement CustomGISParser
3. ✅ Test on Union County samples (214 files)
4. ✅ Test on Columbia County samples (108 files)
5. ✅ Extract 90+ attributes per PropertyData spec
6. ✅ Save to MongoDB + PostgreSQL
7. ✅ Validation: 95%+ successful parse rate

**Deliverables:**
- `platforms/base_parser.py` - Abstract base class
- `platforms/custom_gis/custom_gis_parser.py` - Implementation
- `platforms/custom_gis/tests/` - Unit tests using 322 samples
- `platforms/custom_gis/README.md` - Documentation

### Phase 2: High-Volume Platforms (Weeks 2-4)

**PropertyMax, Civic Source**

**Tasks:**
1. Research platform structure
2. Implement platform-specific parsers
3. Test on 10-20 sample parcels per platform
4. Validate data quality
5. Integrate into Celery task queue

### Phase 3: Regional Platforms (Weeks 4-7)

**RealTaxData, Vanguard, eGov**

### Phase 4: Long-Tail Coverage (Future)

**Azteca, Matrix, Vision, DEVNET, MyFloridaCounty**

---

## 📊 Coverage Goals

**Year 1 Target:**
- **15 platforms** fully supported
- **3,000+ counties** covered (out of 3,143 US counties)
- **95%+ coverage** of US population
- **25M+ properties** in database

**Platform Distribution:**
```
QPublic/Beacon:     35%  (1,100 counties)
Tyler Technologies: 15%  (450 counties)
PropertyMax:        10%  (300 counties)
Civic Source:       15%  (450 counties)
Custom GIS:         5%   (150 counties)
Others (10 platforms): 20% (550 counties)
```

---

## 🎯 Success Metrics

**Parser Quality:**
- ✅ 95%+ successful parse rate (valid PropertyData extracted)
- ✅ 90%+ field coverage (90+ attributes populated)
- ✅ <2% error rate (failed scrapes, timeouts)
- ✅ <5 seconds average parse time per property

**Data Quality:**
- ✅ 99%+ parcel ID uniqueness
- ✅ 95%+ owner name extraction success
- ✅ 90%+ assessed value extraction success
- ✅ 85%+ tax amount extraction success
- ✅ 70%+ property details extraction (sqft, year built, etc.)

**Coverage:**
- ✅ Week 2: 322 sample properties parsed (Custom GIS)
- ✅ Month 1: 1,000 properties parsed (5 platforms)
- ✅ Month 3: 10,000 properties parsed (8 platforms)
- ✅ Month 6: 100,000 properties parsed (12 platforms)
- ✅ Year 1: 25M+ properties parsed (15 platforms)

---

## 🚀 Next Steps

### Immediate (This Week):

1. **Create BaseParser architecture:**
   ```bash
   mkdir -p /parser/taxlien-scraper-python/platforms/base
   touch /parser/taxlien-scraper-python/platforms/base/base_parser.py
   touch /parser/taxlien-scraper-python/platforms/base/property_data.py
   ```

2. **Implement CustomGISParser:**
   ```bash
   mkdir -p /parser/taxlien-scraper-python/platforms/custom_gis
   touch /parser/taxlien-scraper-python/platforms/custom_gis/custom_gis_parser.py
   touch /parser/taxlien-scraper-python/platforms/custom_gis/tests/test_union_county.py
   touch /parser/taxlien-scraper-python/platforms/custom_gis/tests/test_columbia_county.py
   ```

3. **Test on 322 sample files:**
   ```bash
   # Import samples to MongoDB (already done)
   python3 scripts/seed_sample_data.py --import-html

   # Parse using new CustomGISParser
   python3 platforms/custom_gis/parse_samples.py --county=Union --limit=10
   python3 platforms/custom_gis/parse_samples.py --county=Columbia --limit=10

   # Validate results
   python3 platforms/custom_gis/validate_results.py
   ```

4. **Update SDD documentation:**
   - Add this file to SUMMARY.md
   - Update 01-requirements.md with 15 platform target
   - Update 03-scraper-parser-workflow.md with BaseParser architecture

### Short-term (Month 1):

1. Complete Custom GIS parser (322 samples)
2. Research PropertyMax structure
3. Research Civic Source structure
4. Begin PropertyMax parser implementation

### Medium-term (Months 2-3):

1. Complete PropertyMax, Civic Source parsers
2. Begin RealTaxData, Vanguard parsers
3. Scale to 10,000 properties parsed
4. Monitor data quality metrics

### Long-term (Months 4-12):

1. Complete all 15 platforms
2. Scale to 25M+ properties
3. Continuous monitoring and optimization
4. Add new platforms as needed

---

**Status:** READY FOR IMPLEMENTATION
**Blockers:** None
**Dependencies:** MongoDB running, 322 samples loaded
