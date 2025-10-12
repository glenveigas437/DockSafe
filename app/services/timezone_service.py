from datetime import datetime, timezone, timedelta
import pytz


class TimezoneService:
    """Service to handle timezone operations based on country selection"""

    # Country to timezone mapping
    COUNTRY_TIMEZONES = {
        "India": "Asia/Kolkata",
        "United States": "America/New_York",
        "United Kingdom": "Europe/London",
        "Canada": "America/Toronto",
        "Australia": "Australia/Sydney",
        "Germany": "Europe/Berlin",
        "France": "Europe/Paris",
        "Japan": "Asia/Tokyo",
        "China": "Asia/Shanghai",
        "Brazil": "America/Sao_Paulo",
        "Russia": "Europe/Moscow",
        "South Africa": "Africa/Johannesburg",
        "Singapore": "Asia/Singapore",
        "UAE": "Asia/Dubai",
        "Saudi Arabia": "Asia/Riyadh",
        "South Korea": "Asia/Seoul",
        "Thailand": "Asia/Bangkok",
        "Malaysia": "Asia/Kuala_Lumpur",
        "Indonesia": "Asia/Jakarta",
        "Philippines": "Asia/Manila",
        "Vietnam": "Asia/Ho_Chi_Minh",
        "Turkey": "Europe/Istanbul",
        "Italy": "Europe/Rome",
        "Spain": "Europe/Madrid",
        "Netherlands": "Europe/Amsterdam",
        "Sweden": "Europe/Stockholm",
        "Norway": "Europe/Oslo",
        "Denmark": "Europe/Copenhagen",
        "Finland": "Europe/Helsinki",
        "Poland": "Europe/Warsaw",
        "Czech Republic": "Europe/Prague",
        "Hungary": "Europe/Budapest",
        "Romania": "Europe/Bucharest",
        "Greece": "Europe/Athens",
        "Portugal": "Europe/Lisbon",
        "Ireland": "Europe/Dublin",
        "Belgium": "Europe/Brussels",
        "Austria": "Europe/Vienna",
        "Switzerland": "Europe/Zurich",
        "New Zealand": "Pacific/Auckland",
        "Mexico": "America/Mexico_City",
        "Argentina": "America/Argentina/Buenos_Aires",
        "Chile": "America/Santiago",
        "Colombia": "America/Bogota",
        "Peru": "America/Lima",
        "Venezuela": "America/Caracas",
        "Ecuador": "America/Guayaquil",
        "Bolivia": "America/La_Paz",
        "Paraguay": "America/Asuncion",
        "Uruguay": "America/Montevideo",
        "Egypt": "Africa/Cairo",
        "Nigeria": "Africa/Lagos",
        "Kenya": "Africa/Nairobi",
        "Morocco": "Africa/Casablanca",
        "Tunisia": "Africa/Tunis",
        "Algeria": "Africa/Algiers",
        "Libya": "Africa/Tripoli",
        "Ethiopia": "Africa/Addis_Ababa",
        "Ghana": "Africa/Accra",
        "Senegal": "Africa/Dakar",
        "Ivory Coast": "Africa/Abidjan",
        "Cameroon": "Africa/Douala",
        "Angola": "Africa/Luanda",
        "Mozambique": "Africa/Maputo",
        "Tanzania": "Africa/Dar_es_Salaam",
        "Uganda": "Africa/Kampala",
        "Rwanda": "Africa/Kigali",
        "Burundi": "Africa/Bujumbura",
        "Madagascar": "Indian/Antananarivo",
        "Mauritius": "Indian/Mauritius",
        "Seychelles": "Indian/Mahe",
        "Israel": "Asia/Jerusalem",
        "Jordan": "Asia/Amman",
        "Lebanon": "Asia/Beirut",
        "Syria": "Asia/Damascus",
        "Iraq": "Asia/Baghdad",
        "Iran": "Asia/Tehran",
        "Afghanistan": "Asia/Kabul",
        "Pakistan": "Asia/Karachi",
        "Bangladesh": "Asia/Dhaka",
        "Sri Lanka": "Asia/Colombo",
        "Nepal": "Asia/Kathmandu",
        "Bhutan": "Asia/Thimphu",
        "Myanmar": "Asia/Yangon",
        "Cambodia": "Asia/Phnom_Penh",
        "Laos": "Asia/Vientiane",
        "Mongolia": "Asia/Ulaanbaatar",
        "Kazakhstan": "Asia/Almaty",
        "Uzbekistan": "Asia/Tashkent",
        "Kyrgyzstan": "Asia/Bishkek",
        "Tajikistan": "Asia/Dushanbe",
        "Turkmenistan": "Asia/Ashgabat",
        "Azerbaijan": "Asia/Baku",
        "Armenia": "Asia/Yerevan",
        "Georgia": "Asia/Tbilisi",
        "Ukraine": "Europe/Kiev",
        "Belarus": "Europe/Minsk",
        "Lithuania": "Europe/Vilnius",
        "Latvia": "Europe/Riga",
        "Estonia": "Europe/Tallinn",
        "Moldova": "Europe/Chisinau",
        "Bulgaria": "Europe/Sofia",
        "Croatia": "Europe/Zagreb",
        "Serbia": "Europe/Belgrade",
        "Bosnia and Herzegovina": "Europe/Sarajevo",
        "Montenegro": "Europe/Podgorica",
        "North Macedonia": "Europe/Skopje",
        "Albania": "Europe/Tirana",
        "Slovenia": "Europe/Ljubljana",
        "Slovakia": "Europe/Bratislava",
        "Iceland": "Atlantic/Reykjavik",
        "Greenland": "America/Godthab",
        "Fiji": "Pacific/Fiji",
        "Papua New Guinea": "Pacific/Port_Moresby",
        "Solomon Islands": "Pacific/Guadalcanal",
        "Vanuatu": "Pacific/Efate",
        "New Caledonia": "Pacific/Noumea",
        "French Polynesia": "Pacific/Tahiti",
        "Samoa": "Pacific/Apia",
        "Tonga": "Pacific/Tongatapu",
        "Cook Islands": "Pacific/Rarotonga",
        "Niue": "Pacific/Niue",
        "Tuvalu": "Pacific/Funafuti",
        "Kiribati": "Pacific/Tarawa",
        "Nauru": "Pacific/Nauru",
        "Palau": "Pacific/Palau",
        "Marshall Islands": "Pacific/Majuro",
        "Micronesia": "Pacific/Pohnpei",
        "Guam": "Pacific/Guam",
        "Northern Mariana Islands": "Pacific/Saipan",
        "American Samoa": "Pacific/Pago_Pago",
        "Hawaii": "Pacific/Honolulu",
        "Alaska": "America/Anchorage",
        "California": "America/Los_Angeles",
        "Texas": "America/Chicago",
        "Florida": "America/New_York",
        "Arizona": "America/Phoenix",
        "Colorado": "America/Denver",
        "Washington": "America/Los_Angeles",
        "Oregon": "America/Los_Angeles",
        "Nevada": "America/Los_Angeles",
        "Utah": "America/Denver",
        "Montana": "America/Denver",
        "Wyoming": "America/Denver",
        "Idaho": "America/Denver",
        "North Dakota": "America/Chicago",
        "South Dakota": "America/Chicago",
        "Nebraska": "America/Chicago",
        "Kansas": "America/Chicago",
        "Oklahoma": "America/Chicago",
        "Arkansas": "America/Chicago",
        "Louisiana": "America/Chicago",
        "Mississippi": "America/Chicago",
        "Alabama": "America/Chicago",
        "Tennessee": "America/Chicago",
        "Kentucky": "America/New_York",
        "West Virginia": "America/New_York",
        "Virginia": "America/New_York",
        "North Carolina": "America/New_York",
        "South Carolina": "America/New_York",
        "Georgia": "America/New_York",
        "Maryland": "America/New_York",
        "Delaware": "America/New_York",
        "New Jersey": "America/New_York",
        "Pennsylvania": "America/New_York",
        "New York": "America/New_York",
        "Connecticut": "America/New_York",
        "Rhode Island": "America/New_York",
        "Massachusetts": "America/New_York",
        "Vermont": "America/New_York",
        "New Hampshire": "America/New_York",
        "Maine": "America/New_York",
        "Minnesota": "America/Chicago",
        "Wisconsin": "America/Chicago",
        "Michigan": "America/New_York",
        "Illinois": "America/Chicago",
        "Indiana": "America/New_York",
        "Ohio": "America/New_York",
        "Iowa": "America/Chicago",
        "Missouri": "America/Chicago",
    }

    @staticmethod
    def get_timezone_for_country(country):
        """Get timezone for a given country"""
        return TimezoneService.COUNTRY_TIMEZONES.get(country, "UTC")

    @staticmethod
    def get_current_time_for_country(country):
        """Get current time for a given country"""
        timezone_name = TimezoneService.get_timezone_for_country(country)
        try:
            tz = pytz.timezone(timezone_name)
            return datetime.now(tz)
        except:
            # Fallback to UTC if timezone not found
            return datetime.now(timezone.utc)

    @staticmethod
    def get_countries_list():
        """Get list of all supported countries"""
        return sorted(TimezoneService.COUNTRY_TIMEZONES.keys())

    @staticmethod
    def format_time_for_display(dt, country=None):
        """Format datetime for display with country-specific formatting"""
        if country:
            timezone_name = TimezoneService.get_timezone_for_country(country)
            try:
                tz = pytz.timezone(timezone_name)
                local_dt = dt.astimezone(tz)
                return local_dt.strftime("%B %d, %Y at %I:%M %p %Z")
            except:
                pass

        # Fallback formatting
        return dt.strftime("%B %d, %Y at %I:%M %p UTC")
