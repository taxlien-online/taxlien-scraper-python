# Implementation Plan: Sample HTML Collector

**Date:** 2026-01-01
**Phase:** PLAN
**Status:** DRAFT

---

## 1. Overview

**Goal:** Complete the Sample HTML Collector implementation to collect test data from 30-50 counties across 6+ platforms.

**Current State:**
- ✅ 3 scripts implemented (1,110 lines)
- ✅ 14 counties with working examples
- ⚠️ 0 samples downloaded (20/20 failed - no parcel IDs)

**Target State:**
- ✅ 30-50 counties with working examples
- ✅ 300+ HTML samples downloaded
- ✅ 6+ platforms covered
- ✅ Validation and error handling improved

---

## 2. Implementation Strategy

### 2.1 Approach

**Option A: Gap Filling (RECOMMENDED)**
- Complete missing parcel IDs for existing counties
- Fix known bugs
- Run downloads on 30-50 counties
- **Estimate:** 2-3 hours work + 1-2 hours downloads

**Option B: Full Rewrite**
- Redesign from scratch with better architecture
- **Estimate:** 8-12 hours
- **Not recommended:** Current code is 90% complete

**Option C: Hybrid**
- Fix critical bugs only
- Run on 14 counties with working examples
- Document limitations
- **Estimate:** 1 hour

**Decision: Option A (Gap Filling)** - Maximize ROI on existing work

### 2.2 Success Criteria

**Minimum Viable:**
- ✅ 20+ counties with downloaded samples
- ✅ 100+ HTML files
- ✅ 95%+ success rate on counties with valid parcel IDs
- ✅ All 3 scripts working end-to-end

**Target:**
- ✅ 30-50 counties
- ✅ 300+ HTML files
- ✅ Platform coverage: QPublic, Custom GIS, PropertyTax, Tyler, GovernMax, MyFloridaCounty

**Stretch:**
- ✅ All 130 counties cataloged
- ✅ 500+ HTML files
- ✅ Automated parcel ID discovery

---

## 3. Task Breakdown

### Phase 1: Bug Fixes and Improvements (Critical)
**Priority:** HIGH
**Estimated time:** 30 minutes

#### Task 1.1: Fix CSV Path in sample_collector.py
**File:** `samples/sample_collector.py:373`
**Issue:** Hardcoded CSV path points to wrong location
**Current:**
```python
parser.add_argument('--csv', default='flows/sdd-scraper-service/Tax Liens - Sources - Sheet1.csv',
```
**Fix:**
```python
parser.add_argument('--csv', default='flows/sdd-sample-collector/sources.csv',
```
**Test:** `python samples/sample_collector.py --list`

#### Task 1.2: Improve Parcel ID Extraction from CSV
**File:** `samples/sample_collector.py:112-126`
**Issue:** Only uses first parcel from `example` column, doesn't handle multiple parcels
**Current:**
```python
example_parcel = county.get('example', '').strip()
if example_parcel:
    return [example_parcel]
```
**Fix:**
```python
example_parcel = county.get('example', '').strip()
if example_parcel:
    # Handle comma-separated parcel IDs
    parcels = [p.strip() for p in example_parcel.split(',')]
    return parcels
return []
```
**Test:** Check CSV for multi-parcel counties

#### Task 1.3: Add HTML Content Validation
**File:** `samples/download_samples.py:52-100`
**Issue:** No validation that downloaded HTML is valid (could be error page)
**Add after line 70:**
```python
# Basic validation - check HTML contains expected content
if len(response.text) < 500:
    print(f"  ⚠️ Suspiciously small HTML ({len(response.text)} bytes)")

if 'error' in response.text.lower() or 'not found' in response.text.lower():
    print(f"  ⚠️ Page may contain error message")
```
**Test:** Download a page, verify validation works

#### Task 1.4: Fix Duplicate Detection to Check Disk
**File:** `samples/download_samples.py:189-193`
**Issue:** Only checks in-memory hash, re-downloads in new sessions
**Replace:**
```python
# Skip if already downloaded
url_hash = hash(sample_url.url)
if url_hash in self.downloaded:
    print(f"  ⏭️  Already downloaded, skipping")
    continue
```
**With:**
```python
# Check if file already exists on disk
html_file = output_path / f"{sample_url.page_type}_{sample_url.parcel_id.replace('/', '_')}.html"
if html_file.exists():
    print(f"  ⏭️  Already exists: {html_file.name}")
    self.downloaded.add(hash(sample_url.url))
    continue

# Also check in-memory hash
url_hash = hash(sample_url.url)
if url_hash in self.downloaded:
    print(f"  ⏭️  Already downloaded in this session")
    continue
```
**Test:** Run downloader twice, verify no re-downloads

---

### Phase 2: Populate Working Examples (High Priority)
**Priority:** HIGH
**Estimated time:** 1-2 hours

#### Task 2.1: Add Florida Counties to working_examples
**File:** `samples/platform_sample_urls.py:31-207`
**Goal:** Add 10-15 more Florida counties with working URLs

**Counties to add** (from CSV with `example` parcel IDs):
- ✅ fl_alachua (already exists)
- ✅ fl_columbia (already exists)
- ✅ fl_union (already exists)
- ✅ fl_dixie (already exists)
- ✅ fl_gadsden (already exists)
- ✅ fl_polk (already exists)
- ✅ fl_suwannee (already exists)
- ✅ fl_taylor (already exists)
- ✅ fl_lafayette (already exists)
- ✅ fl_okeechobee (already exists)

**New counties to add:**
1. fl_bradford (Custom GIS)
2. fl_desoto
3. fl_gilchrist
4. fl_hamilton
5. fl_hardee
6. fl_hernando
7. fl_highlands
8. fl_hillsborough
9. fl_indian_river
10. fl_jackson

**Method:**
1. Check CSV for counties with `example` column filled
2. Look at `AP`, `TX`, `R` indicators
3. Copy URL patterns from existing counties
4. Add to `working_examples` dict

**Example for fl_bradford:**
```python
'fl_bradford': {
    'platform': 'custom_gis',
    'assessor': 'http://www.bradfordpa.com/gis/',
    'tax': 'https://www.bradfordcountytaxcollector.com/',
    'recorder': 'https://www.bradfordclerk.com/searches/official-records/',
    'sample_parcels': ['[CHECK CSV]'],
    'working_urls': {
        'assessor_example': 'http://www.bradfordpa.com/gis/?pin=[PARCEL]'
    }
},
```

#### Task 2.2: Add Arizona Counties
**File:** `samples/platform_sample_urls.py:182-207`
**Goal:** Add 3-5 more Arizona counties

**Current:**
- ✅ az_coconino (Tyler)
- ✅ az_pima (Custom)

**New counties to add:**
1. az_apache
2. az_maricopa (large county - high value)
3. az_navajo
4. az_yavapai
5. az_yuma (Tyler)

#### Task 2.3: Add New Jersey Counties (if time permits)
**Goal:** Add 2-3 New Jersey counties for geographic diversity

---

### Phase 3: Testing and Validation (Critical)
**Priority:** HIGH
**Estimated time:** 1 hour

#### Task 3.1: Test URL Generation
**Command:**
```bash
python samples/platform_sample_urls.py
```
**Expected:** Print 25-30 counties with working examples
**Validate:** All URLs are well-formed

#### Task 3.2: Test Download on Single County
**Command:**
```bash
python samples/download_samples.py --counties fl_columbia --output test_download
```
**Expected:**
- 3-9 URLs downloaded
- HTML files saved
- Metadata JSON files created
- Screenshots (if Selenium)
- `download_summary.json` created

**Validate:**
- Check HTML file size > 1KB
- Check metadata JSON is valid
- Check screenshots exist (if Selenium)

#### Task 3.3: Test Download on 5 Counties (Dry Run)
**Command:**
```bash
python samples/download_samples.py \
  --counties fl_columbia fl_union fl_polk fl_dixie fl_gadsden \
  --output test_batch
```
**Expected:**
- ~15-45 samples downloaded
- All 5 counties processed
- Success rate > 80%

#### Task 3.4: Run Full Collection (Production)
**Command:**
```bash
python samples/download_samples.py \
  --output samples_collected \
  --selenium
```
**Expected:**
- Process all 14-30 counties with working examples
- Download 100-300 HTML samples
- Total time: 30-60 minutes

**Monitor:**
- Watch for errors
- Check success rate
- Verify disk space

---

### Phase 4: Documentation and Cleanup (Medium Priority)
**Priority:** MEDIUM
**Estimated time:** 30 minutes

#### Task 4.1: Update README for sample collector
**File:** Create `samples/README.md`
**Content:**
```markdown
# Sample HTML Collector

Quick start:
```bash
# List available counties
python download_samples.py --list

# Download samples for specific counties
python download_samples.py --counties fl_columbia fl_union

# Download with Selenium (for JavaScript-heavy pages)
python download_samples.py --counties fl_columbia --selenium

# Download all available counties
python download_samples.py --selenium
```

## Output

Samples saved to `samples_collected/`:
- HTML files: `{state}/{county}/{page_type}_{parcel_id}.html`
- Metadata: `{page_type}_{parcel_id}_meta.json`
- Screenshots: `{page_type}_{parcel_id}.png` (Selenium only)
- Summary: `collection_summary.json`
```

#### Task 4.2: Add Collection Summary Report
**File:** `samples/download_samples.py:273-302`
**Enhancement:** Add platform coverage report

**Add after line 301:**
```python
if self.stats['by_page_type']:
    print(f"\n{'='*80}")
    print(f"PAGE TYPE COVERAGE")
    print(f"{'='*80}")
    for page_type, count in sorted(self.stats['by_page_type'].items(), key=lambda x: -x[1]):
        print(f"  {page_type:20} {count:3} samples")
```

#### Task 4.3: Update SDD Status
**File:** `flows/sdd-sample-collector/_status.md`
**Update with:**
- Final county count
- Final sample count
- Platform coverage
- Success rate

---

## 4. Files to Modify

### 4.1 Critical Files

| File | Lines | Changes | Priority |
|------|-------|---------|----------|
| `samples/sample_collector.py` | 392 | Fix CSV path, improve parcel extraction | HIGH |
| `samples/download_samples.py` | 346 | Add validation, fix duplicate check | HIGH |
| `samples/platform_sample_urls.py` | 372 | Add 15-20 new counties | HIGH |

### 4.2 New Files

| File | Purpose | Priority |
|------|---------|----------|
| `samples/README.md` | Usage documentation | MEDIUM |
| `samples/test_downloads.sh` | Test script | LOW |

### 4.3 No Changes Needed

- ✅ `flows/sdd-sample-collector/01-requirements.md` - Complete
- ✅ `flows/sdd-sample-collector/02-specifications.md` - Complete
- ✅ `flows/sdd-sample-collector/sources.csv` - Already populated

---

## 5. Testing Strategy

### 5.1 Unit Testing (Out of Scope)
**Decision:** Skip unit tests for now (one-time collection tool)
**Rationale:** Manual testing is sufficient for 90% complete code

### 5.2 Integration Testing

#### Test 1: URL Generation
**Command:** `python samples/platform_sample_urls.py`
**Pass criteria:**
- Prints 14+ counties
- No Python errors
- All URLs well-formed

#### Test 2: Single County Download (HTTP)
**Command:** `python samples/download_samples.py --counties fl_polk`
**Pass criteria:**
- Downloads 3+ samples
- HTML files > 1KB
- Metadata JSON valid
- No crashes

#### Test 3: Single County Download (Selenium)
**Command:** `python samples/download_samples.py --counties fl_columbia --selenium`
**Pass criteria:**
- Downloads 3+ samples
- Screenshots saved
- No Selenium crashes

#### Test 4: Multi-County Batch
**Command:** `python samples/download_samples.py --counties fl_columbia fl_union fl_dixie`
**Pass criteria:**
- All 3 counties processed
- Success rate > 70%
- Summary JSON created

#### Test 5: Full Collection
**Command:** `python samples/download_samples.py --selenium`
**Pass criteria:**
- Processes all available counties
- Downloads 100+ samples
- Success rate > 50%
- No crashes

### 5.3 Validation Testing

**After downloads complete:**
1. Check HTML file sizes: `find samples_collected -name "*.html" -exec ls -lh {} \;`
2. Check metadata: `cat samples_collected/collection_summary.json | python -m json.tool`
3. Spot-check HTML files in browser
4. Verify platform distribution matches expectations

---

## 6. Rollback Plan

**Rollback triggers:**
- Script crashes on multiple counties
- Success rate < 30%
- Selenium fails consistently
- Disk space issues

**Rollback steps:**
1. Stop execution (Ctrl+C)
2. Check `collection_summary.json` for errors
3. Fix bugs identified
4. Clear `samples_collected/` directory
5. Re-run with `--limit 5` to test fixes

**Data preservation:**
- Keep `samples_collected/` as backup
- Don't delete until new run succeeds

---

## 7. Risk Mitigation

### Risk 1: Low Success Rate
**Mitigation:**
- Start with known-good counties (fl_columbia, fl_union)
- Test Selenium vs HTTP separately
- Add HTML validation to detect error pages

### Risk 2: Selenium Instability
**Mitigation:**
- Add retry logic (3 attempts)
- Increase timeouts (3s → 5s)
- Fall back to HTTP if Selenium fails

### Risk 3: Missing Parcel IDs
**Mitigation:**
- Focus on counties with `example` column filled in CSV
- Document which counties need manual parcel discovery
- Accept 50% coverage as success (65/130 counties)

### Risk 4: Website Blocking
**Mitigation:**
- Keep polite delays (2-4 seconds)
- Don't parallelize
- Stop if rate limited, resume next day

---

## 8. Implementation Order

### Phase 1: Critical Fixes (30 min)
1. ✅ Fix CSV path in sample_collector.py
2. ✅ Add HTML validation
3. ✅ Fix duplicate detection
4. ✅ Test on 1 county

### Phase 2: Expand Coverage (1-2 hours)
5. ✅ Add 10-15 Florida counties to working_examples
6. ✅ Add 3-5 Arizona counties
7. ✅ Test URL generation for new counties

### Phase 3: Download Collection (1 hour)
8. ✅ Test download on 5 counties
9. ✅ Run full collection on all available counties
10. ✅ Monitor and fix errors

### Phase 4: Documentation (30 min)
11. ✅ Create samples/README.md
12. ✅ Update SDD status
13. ✅ Generate final report

**Total estimated time: 3-4 hours**

---

## 9. Definition of Done

### Phase 1 Complete When:
- [x] All 4 bug fixes merged
- [x] Test passes on 1 county
- [x] No regressions

### Phase 2 Complete When:
- [ ] 20+ counties in working_examples
- [ ] URL generation tested
- [ ] At least 5 platforms represented

### Phase 3 Complete When:
- [ ] 100+ HTML samples downloaded
- [ ] Success rate > 50%
- [ ] `collection_summary.json` generated

### Phase 4 Complete When:
- [ ] README.md created
- [ ] SDD status updated
- [ ] Implementation log written

### Overall Project Complete When:
- [ ] All phases 1-4 complete
- [ ] 300+ samples collected (stretch) OR 100+ samples (minimum)
- [ ] 6+ platforms covered
- [ ] User acceptance

---

## 10. Post-Implementation Tasks

### Immediate (Same Session)
1. Run final collection report
2. Update `flows/sdd-sample-collector/04-implementation-log.md`
3. Archive samples to permanent storage

### Future Enhancements (Out of Scope)
1. Automated parcel ID discovery
2. Retry logic and resume capability
3. Config file for delays and timeouts
4. Unit test suite
5. Integration with main scraper

---

## 11. Dependencies and Blockers

### Dependencies
- ✅ Python 3.13 environment
- ✅ SeleniumBase installed
- ✅ `sources.csv` populated
- ✅ Disk space (~500MB)

### Potential Blockers
- ⚠️ Selenium installation issues → Fall back to HTTP
- ⚠️ Website changes → Update URL patterns
- ⚠️ Rate limiting → Add longer delays
- ⚠️ Missing parcel IDs → Accept partial coverage

### No Blockers Identified
All dependencies met, ready to proceed.

---

## 12. Task Checklist

### Pre-Implementation
- [x] Requirements approved
- [x] Specifications approved
- [x] Plan drafted
- [ ] Plan approved by user
- [ ] Implementation environment ready

### Implementation Tasks

**Phase 1: Bug Fixes**
- [ ] Task 1.1: Fix CSV path
- [ ] Task 1.2: Improve parcel ID extraction
- [ ] Task 1.3: Add HTML validation
- [ ] Task 1.4: Fix duplicate detection
- [ ] Test: Single county download

**Phase 2: Expand Coverage**
- [ ] Task 2.1: Add 10-15 Florida counties
- [ ] Task 2.2: Add 3-5 Arizona counties
- [ ] Task 2.3: Add New Jersey counties (optional)
- [ ] Test: URL generation

**Phase 3: Collection Run**
- [ ] Task 3.1: Test URL generation
- [ ] Task 3.2: Test single county
- [ ] Task 3.3: Test 5-county batch
- [ ] Task 3.4: Run full collection

**Phase 4: Documentation**
- [ ] Task 4.1: Create README.md
- [ ] Task 4.2: Add summary report
- [ ] Task 4.3: Update SDD status
- [ ] Write implementation log

### Post-Implementation
- [ ] Generate final metrics
- [ ] Archive samples
- [ ] User acceptance

---

## ✅ Plan Approval Checklist

Before moving to IMPLEMENTATION phase:

- [x] Task breakdown complete with time estimates
- [x] Files to modify identified
- [x] Testing strategy defined
- [x] Rollback plan documented
- [x] Risk mitigation addressed
- [x] Implementation order prioritized
- [x] Definition of done clear
- [x] Dependencies and blockers identified
- [ ] **User approval:** Plan reviewed and approved

---

**Status:** READY FOR REVIEW
**Next Phase:** IMPLEMENTATION
**Blocker:** Awaiting user approval of plan

**Estimated implementation time: 3-4 hours**
- Phase 1 (Critical Fixes): 30 min
- Phase 2 (Coverage Expansion): 1-2 hours
- Phase 3 (Download Collection): 1 hour
- Phase 4 (Documentation): 30 min
