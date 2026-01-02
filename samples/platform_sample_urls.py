#!/usr/bin/env python3
"""
Platform-Specific Sample URL Generator

Generates working sample URLs for each platform based on actual examples from sources.csv
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SampleURL:
    """Sample URL with metadata"""
    url: str
    parcel_id: str
    page_type: str  # 'assessor', 'tax', 'gis', 'recorder'
    platform: str
    county: str
    state: str
    notes: str = ""


class PlatformURLGenerator:
    """Generate sample URLs for different county platforms"""

    def __init__(self):
        # Real working examples from CSV
        self.working_examples = self._load_working_examples()

    def _load_working_examples(self) -> Dict:
        """Load real working examples from sources.csv"""
        return {
            # FLORIDA - QPublic/Beacon
            'fl_alachua': {
                'platform': 'qpublic',
                'assessor': 'https://qpublic.schneidercorp.com/Application.aspx?AppID=1081&LayerID=26490&PageTypeID=2&PageID=10768',
                'tax': 'https://alachua.county-taxes.com/public/search/property_tax',
                'sample_parcels': ['01234-000-000', '02345-000-000', '03456-000-000']
            },

            'fl_columbia': {
                'platform': 'custom_gis',
                'assessor': 'http://columbia.floridapa.com/gis/',
                'tax': 'http://fl-columbia-taxcollector.governmax.com/collectmax/collect30.asp',
                'gis': 'http://columbia.floridapa.com/gis/',
                'recorder': 'https://www.myfloridacounty.com/ori/index.do',
                'sample_parcels': ['R00010-001', '142S1500061000', 'R12074-000'],
                'working_urls': {
                    'assessor_example': 'https://columbia.floridapa.com/gis/?pin=142S1500061000',
                    'gis_example': 'https://columbia.floridapa.com/gis/',
                    'tax_example': 'https://fl-columbia-taxcollector.governmax.com/collectmax/collect30.asp',
                    'tax_link_example': 'https://columbia.floridapa.com/GIS/TaxLink_wait.asp?R12074-000'
                }
            },

            'fl_union': {
                'platform': 'custom_gis',
                'assessor': 'http://union.floridapa.com/gis/',
                'tax': 'https://www.unioncountytc.com/Property/SearchSelect?ClearData=True',
                'recorder': 'https://unionclerk.com/search-official-records/',
                'sample_parcels': ['1805210000005700'],
                'working_urls': {
                    'assessor_example': 'https://union.floridapa.com/gis/?pin=1805210000005700'
                }
            },

            'fl_dixie': {
                'platform': 'qpublic',
                'assessor': 'https://qpublic.schneidercorp.com/Application.aspx?AppID=867&LayerID=16385&PageTypeID=2&PageID=7230',
                'tax': 'http://fl-dixie-taxcollector.governmax.com/collectmax/collect30.asp',
                'recorder': 'https://www.myfloridacounty.com/ori/index.do',
                'sample_parcels': ['010813-00003634-1100', '35-08-13-0000-3900-0200'],
                'working_urls': {
                    'assessor_example': 'https://qpublic.schneidercorp.com/Application.aspx?AppID=867&LayerID=16385&PageTypeID=4&PageID=7232&Q=1806901892&KeyValue=35-08-13-0000-3900-0200'
                }
            },

            'fl_gadsden': {
                'platform': 'qpublic',
                'assessor': 'https://qpublic.schneidercorp.com/Application.aspx?App=GadsdenCountyFL&PageType=Search',
                'tax': 'http://fl-gadsden-taxcollector.governmax.com/collectmax/collect30.asp',
                'recorder': 'http://www.gadsdenclerk.com/PublicInquiry',
                'sample_parcels': ['1324N4W0000003220300', '1-32-4N-4W-0000-00322-0300'],
                'working_urls': {
                    'assessor_example': 'https://beacon.schneidercorp.com/Application.aspx?AppID=814&LayerID=14537&PageTypeID=4&PageID=6817&Q=2067269998&KeyValue=1%2D32%2D4N%2D4W%2D0000%2D00322%2D0300',
                    'recorder_example': 'https://www.gadsdenclerk.com/PublicInquiry/Instrument.aspx?InstrumentID=2678416'
                }
            },

            'fl_polk': {
                'platform': 'custom',
                'assessor': 'https://www.polkpa.org/CamaDisplay.aspx?OutputMode=Input&searchType=RealEstate&page=FindByAddress&cookie_test=true',
                'tax': 'https://www4.polktaxes.com/services/search-and-pay-property-taxes/',
                'gis': 'https://www.polkpa.org/MapSearch.aspx',
                'recorder': 'https://apps.polkcountyclerk.net/browserviewor/',
                'sample_parcels': ['222602000000013090', '222602-000000-013180'],
                'working_urls': {
                    'assessor_example': 'https://www.polkpa.org/CamaDisplay.aspx?OutputMode=Display&SearchType=RealEstate&ParcelID=222602000000013090',
                    'gis_example': 'https://map.polkpa.org/?parcelid=222602000000013090',
                    'tax_example': 'https://polk.payfltaxes.com/property-tax/bill/222602-000000-013180'
                }
            },

            'fl_sarasota': {
                'platform': 'custom',
                'assessor': 'https://www.sc-pa.com//propertysearch',
                'tax': 'https://www.sarasotataxcollector.com/',
                'gis': 'https://ags3.scgov.net/scpa/',
                'recorder': 'https://secure.sarasotaclerk.com/OfficialRecords.aspx',
                'sample_parcels': ['0002141099'],
                'working_urls': {
                    'assessor_example': 'https://qpublic.schneidercorp.com/Application.aspx?App=GadsdenCountyFL&PageType=Search',
                    'gis_example': 'https://ags3.scgov.net/scpa/',
                    'tax_example': 'https://sarasotataxcollector.governmax.com/collectmax/collect30.asp'
                }
            },

            'fl_suwannee': {
                'platform': 'custom_gis',
                'assessor': 'http://www.suwanneepa.com/gis/',
                'tax': 'https://suwannee.floridatax.us/AccountSearch?s=pt',
                'recorder': 'http://records.suwgov.org/LandmarkWeb/Home/index',
                'sample_parcels': ['00035000000', '0403S11E11334000000'],
                'working_urls': {
                    'assessor_example': 'https://www.suwanneepa.com/gis/?pin=0403S11E11334000000',
                    'tax_example': 'https://suwannee.floridatax.us/PropertyDetail?p=00035000000&y=2023&b=19.0000',
                    'tax_link_example': 'https://www.suwanneepa.com/gis/linkTax/?PIN=00035000000&random=21158.88'
                }
            },

            'fl_taylor': {
                'platform': 'qpublic',
                'assessor': 'https://qpublic.net/fl/taylor/',
                'tax': 'https://www.taylorcountytaxcollector.com/',
                'recorder': 'http://67.158.150.97/PublicInquiry/Search.aspx?Type=Name',
                'sample_parcels': ['R06259-050', '06259-050'],
                'working_urls': {
                    'assessor_example': 'https://qpublic.schneidercorp.com/Application.aspx?AppID=792&LayerID=11749&PageTypeID=4&PageID=5270&Q=182380348&KeyValue=06259-050',
                    'tax_example': 'https://taylor.floridatax.us/PropertyDetail?p=R06259-050&y=2023&b=9176.0000'
                }
            },

            'fl_orange': {
                'platform': 'custom',
                'assessor': 'https://ocpaweb.ocpafl.org/parcelsearch',
                'tax': 'https://www.octaxcol.com/taxes/about-property-tax/pay-my-taxes/',
                'gis': 'http://www.orangecountyfl.net/PlanningDevelopment/InteractiveMapping.aspx',
                'recorder': 'https://selfservice.or.occompt.com/ssweb/search/DOCSEARCH2950S1',
                'sample_parcels': ['REG017988'],
                'working_urls': {
                    'assessor_example': 'https://ocpaweb.ocpafl.org/parcelsearch',
                    'tangible_example': 'https://ocpaweb.ocpafl.org/tangiblecard/REG017988',
                    'recorder_example': 'https://selfservice.or.occompt.com/ssweb/search/DOCSEARCH2950S1'
                }
            },

            'fl_lafayette': {
                'platform': 'custom_gis',
                'assessor': 'http://www.lafayettepa.com/GIS/Search_F.asp',
                'tax': 'http://www.lafayettetc.com/',
                'recorder': 'https://www3.myfloridacounty.com/ori/index.do',
                'sample_parcels': ['0507140000000000200', '01-03-10-0000-0000-00104'],
                'working_urls': {
                    'assessor_example': 'https://www.lafayettepa.com/gis/?pin=0507140000000000200',
                    'tax_example': 'https://lafayette.payfltaxes.com/property-tax/bill/01-03-10-0000-0000-00104',
                    'recorder_example': 'https://www3.myfloridacounty.com/ori/index.do'
                }
            },

            'fl_okeechobee': {
                'platform': 'custom_gis',
                'assessor': 'http://www.okeechobeepa.com/gis/',
                'tax': 'https://okeechobeecountytaxcollector.com/Property/SearchSelect',
                'recorder': 'https://pioneer.okeechobeelandmark.com/LandmarkWebLive',
                'sample_parcels': ['11536350040000400200'],
                'working_urls': {
                    'assessor_example': 'https://www.okeechobeepa.com/gis/?pin=11536350040000400200'
                }
            },

            # ARIZONA
            'az_coconino': {
                'platform': 'tyler',
                'assessor': 'https://www.coconino.az.gov/121/Maps-Property-Information',
                'tax': 'https://www.coconino.az.gov/372/Treasurer',
                'gis': 'https://coconinocounty.maps.arcgis.com/apps/webappviewer/index.html?id=868170827e4443d2be37eb60562446ae',
                'recorder': 'https://eagleassessor.coconino.az.gov:8443/recorder/web/',
                'sample_parcels': ['R0050197', '10035015'],
                'working_urls': {
                    'assessor_example': 'https://eagleassessor.coconino.az.gov:444/assessor/taxweb/results.jsp',
                    'tax_example': 'https://eagleassessor.coconino.az.gov/treasurer/treasurerweb/account.jsp?account=R0050197'
                }
            },

            'az_pima': {
                'platform': 'custom',
                'assessor': 'https://www.asr.pima.gov/',
                'tax': 'https://www.to.pima.gov/',
                'gis': 'https://gis.pima.gov/maps/landbase/parsrch.htm',
                'recorder': 'https://www.recorder.pima.gov/PublicDocServices/Search',
                'sample_parcels': ['993420000'],
                'working_urls': {
                    'assessor_example': 'https://www.asr.pima.gov/Parcel/Index'
                }
            },
        }

    def get_sample_urls(self, state: str, county: str, num_samples: int = 3) -> List[SampleURL]:
        """Get sample URLs for a specific county"""
        county_key = f"{state}_{county}"

        if county_key not in self.working_examples:
            return []

        county_data = self.working_examples[county_key]
        platform = county_data['platform']
        sample_urls = []

        # Get working example URLs if available
        if 'working_urls' in county_data:
            for url_type, url in county_data['working_urls'].items():
                # Extract parcel ID if possible
                parcel_id = 'unknown'
                if 'sample_parcels' in county_data and county_data['sample_parcels']:
                    parcel_id = county_data['sample_parcels'][0]

                page_type = url_type.replace('_example', '')

                sample_urls.append(SampleURL(
                    url=url,
                    parcel_id=parcel_id,
                    page_type=page_type,
                    platform=platform,
                    county=county,
                    state=state,
                    notes=f"Working example from sources.csv - {url_type}"
                ))

        # Generate additional URLs using sample parcels
        if 'sample_parcels' in county_data:
            parcels = county_data['sample_parcels'][:num_samples]

            for parcel in parcels:
                # Assessor URL
                if 'assessor' in county_data:
                    url = self._generate_url(county_data['assessor'], parcel, platform, 'assessor')
                    if url:
                        sample_urls.append(SampleURL(
                            url=url,
                            parcel_id=parcel,
                            page_type='assessor',
                            platform=platform,
                            county=county,
                            state=state
                        ))

                # Tax URL
                if 'tax' in county_data:
                    url = self._generate_url(county_data['tax'], parcel, platform, 'tax')
                    if url:
                        sample_urls.append(SampleURL(
                            url=url,
                            parcel_id=parcel,
                            page_type='tax',
                            platform=platform,
                            county=county,
                            state=state
                        ))

        return sample_urls[:num_samples * 3]  # Return up to 3 URLs per sample

    def _generate_url(self, base_url: str, parcel_id: str, platform: str, page_type: str) -> Optional[str]:
        """Generate URL based on platform and page type"""

        if not base_url:
            return None

        # Custom GIS (floridapa.com)
        if 'floridapa.com/gis' in base_url:
            return f"{base_url}?pin={parcel_id}"

        # QPublic - needs search first (return search page)
        if 'qpublic.schneidercorp.com' in base_url or 'beacon.schneidercorp.com' in base_url:
            # Return base search URL - actual parcel URLs need interactive search
            return base_url

        # PropertyTax (county-taxes.com)
        if 'county-taxes.com' in base_url:
            return f"{base_url}?parcel={parcel_id}"

        # GovernMax
        if 'governmax.com' in base_url:
            return base_url  # Needs search form

        # Tyler Technologies
        if 'tylerhost.net' in base_url:
            return base_url  # Needs search form

        # Generic - try parcel parameter
        if '?' not in base_url:
            return f"{base_url}?parcel={parcel_id}"

        return base_url

    def get_all_counties_with_examples(self) -> List[str]:
        """Get list of all counties that have working examples"""
        return list(self.working_examples.keys())

    def print_county_info(self, state: str, county: str):
        """Print detailed info about a county's URLs"""
        county_key = f"{state}_{county}"

        if county_key not in self.working_examples:
            print(f"No examples found for {county_key}")
            return

        data = self.working_examples[county_key]
        print(f"\n{'='*80}")
        print(f"County: {state.upper()} - {county.title()}")
        print(f"Platform: {data['platform']}")
        print(f"{'='*80}")

        print(f"\nBase URLs:")
        if 'assessor' in data:
            print(f"  Assessor:  {data['assessor']}")
        if 'tax' in data:
            print(f"  Tax:       {data['tax']}")
        if 'gis' in data:
            print(f"  GIS:       {data['gis']}")
        if 'recorder' in data:
            print(f"  Recorder:  {data['recorder']}")

        if 'sample_parcels' in data:
            print(f"\nSample Parcel IDs:")
            for parcel in data['sample_parcels']:
                print(f"  - {parcel}")

        if 'working_urls' in data:
            print(f"\nWorking Example URLs:")
            for url_type, url in data['working_urls'].items():
                print(f"  {url_type}:")
                print(f"    {url}")


def main():
    """Demo usage"""
    generator = PlatformURLGenerator()

    print("Counties with working examples:")
    for county_key in generator.get_all_counties_with_examples():
        state, county = county_key.split('_', 1)
        print(f"  - {state.upper()} {county.title()}")

    print(f"\n{'='*80}\n")

    # Show examples for a few counties
    for county_key in ['fl_columbia', 'fl_union', 'fl_polk', 'az_coconino']:
        state, county = county_key.split('_', 1)
        generator.print_county_info(state, county)

        print(f"\nGenerated Sample URLs:")
        urls = generator.get_sample_urls(state, county, num_samples=2)
        for url in urls:
            print(f"  [{url.page_type}] {url.url}")
            if url.notes:
                print(f"    Notes: {url.notes}")


if __name__ == '__main__':
    main()
