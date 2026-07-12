import logging
import xml.etree.ElementTree as ET
from datetime import timedelta
import requests

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval

DOMAIN = "ipaws_monitor"
_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)
FEED_URL = "https://apps.fema.gov/IPAWSOPEN_EAS_SERVICE/rest/feed"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
CAP_NS = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}

WATCHED_EVENTS = {
    "Tornado Warning",
    "Severe Thunderstorm Warning",
    "Flash Flood Warning",
    "Civil Emergency Message",
    "Extreme Wind Warning",
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform from a config entry."""
    fips_codes = hass.data[DOMAIN][entry.entry_id]
    
    sensor = IpawsMonitorSensor(fips_codes)
    async_add_entities([sensor], True)

    async def update_sensor(now):
        # Safely run the blocking network update inside HA's thread executor pool
        await hass.async_add_executor_job(sensor.update_data)
        # Write the state safely back inside the main event loop
        sensor.async_write_ha_state()

    async_track_time_interval(hass, update_sensor, SCAN_INTERVAL)


class IpawsMonitorSensor(SensorEntity):
    """Representation of an IPAWS Monitor Sensor."""

    def __init__(self, fips_codes):
        """Initialize the sensor."""
        self._state = "No alerts at this time"
        self._attrs = {}
        self.watched_fips = set(fips_codes)

    @property
    def name(self):
        return "IPAWS Emergency Alert"

    @property
    def unique_id(self):
        return f"ipaws_monitor_{''.join(sorted(self.watched_fips))}"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs

    def get_feed(self):
        r = requests.get(FEED_URL, timeout=15, headers={"User-Agent": "IPAWS-Monitor"})
        r.raise_for_status()
        return ET.fromstring(r.content)

    def download_cap(self, url):
        try:
            r = requests.get(url, timeout=15, headers={"User-Agent": "IPAWS-Monitor"})
            if r.status_code == 403:
                return None
            r.raise_for_status()
            return ET.fromstring(r.content)
        except Exception as e:
            _LOGGER.error("Error retrieving CAP XML data: %s", e)
            return None

    def get_alert_info(self, root):
        info = root.find("cap:info", CAP_NS)
        if info is None:
            return None
        return {
            "identifier": root.findtext("cap:identifier", namespaces=CAP_NS),
            "event": info.findtext("cap:event", namespaces=CAP_NS),
            "headline": info.findtext("cap:headline", namespaces=CAP_NS),
            "description": info.findtext("cap:description", namespaces=CAP_NS),
        }

    def get_same_codes(self, root):
        codes = []
        for geo in root.findall(".//cap:area/cap:geocode", CAP_NS):
            name = geo.findtext("cap:valueName", namespaces=CAP_NS)
            value = geo.findtext("cap:value", namespaces=CAP_NS)
            if name == "SAME":
                codes.append(value)
        return codes

    def alert_matches(self, alert, codes):
        if alert["event"] not in WATCHED_EVENTS:
            return False
        for code in codes:
            if code in self.watched_fips:
                return True
        return False

    def update_data(self):
        """Fetch data from the FEMA feed and process states (called inside executor thread)."""
        try:
            feed = self.get_feed()
            entries = feed.findall("atom:entry", ATOM_NS)
            active_alert = None

            for entry in entries:
                alert_id = entry.findtext("atom:id", namespaces=ATOM_NS)
                if not alert_id:
                    continue

                link = entry.find("atom:link", ATOM_NS)
                if link is None:
                    continue

                cap_url = link.attrib.get("href")
                if not cap_url:
                    continue

                cap = self.download_cap(cap_url)
                if cap is None:
                    continue

                alert = self.get_alert_info(cap)
                if alert is None:
                    continue

                codes = self.get_same_codes(cap)

                if self.alert_matches(alert, codes):
                    active_alert = alert
                    break

            if active_alert:
                event_type = active_alert["event"].upper()
                raw_desc = active_alert["description"] or ""
                clean_desc = raw_desc.replace("\n", " ").strip()
                
                self._state = f"THE NATIONAL WEATHER SERVICE HAS ISSUED A {event_type}. {clean_desc}"
                self._attrs = {
                    "headline": active_alert["headline"],
                    "event": active_alert["event"],
                    "identifier": active_alert["identifier"],
                    "monitored_zones": list(self.watched_fips),
                    "alert_active": True
                }
            else:
                self._state = "No alerts at this time"
                self._attrs = {
                    "monitored_zones": list(self.watched_fips),
                    "alert_active": False
                }

        except Exception as e:
            _LOGGER.error("Error updating FEMA IPAWS feed: %s", e)