import requests
import utils
from bs4 import BeautifulSoup
import itertools

# Living Wage start page URL.
base_url = "https://livingwage.mit.edu"


def get_wages(state, city, county):
    def _find_state_locations():
        page = requests.get(base_url)
        soup = BeautifulSoup(page.text, "lxml")

        with open("lw_start.html") as file_in:
            page = file_in.read()
        soup = BeautifulSoup(page, "lxml")
        state_name = utils.state_province_to_long(state)
        locations_path = ""
        for item in soup.find_all("li"):
            if state_name == item.text.strip():
                locations_path = item.a["href"]
                break

        if not locations_path:
            raise ValueError(
                f"Couldn't find a page for state '{state}' ({state_name})."
            )

        state_locations = requests.get(base_url + locations_path)
        return BeautifulSoup(state_locations.text, "lxml")

    def _find_metro_page(state_locations):
        metro_class = "metros list-unstyled"
        div = state_locations.find_all("div", {"class": metro_class})[0]
        metro_path = ""
        for metro in div.find_all("li"):
            metro_name = metro.text.strip()
            if city in metro_name:
                metro_path = metro.a["href"]
                break

        if not metro_path:
            return None

        metro_page = requests.get(base_url + metro_path)
        return BeautifulSoup(metro_page.text, "lxml")

    def _find_county_page(state_locations):
        county_class = "counties list-unstyled"
        div = state_locations.find_all("div", {"class": county_class})[0]
        county_path = ""
        for _county in div.find_all("li"):
            county_name = _county.text.strip()[: -len(" County")]
            if county == county_name:
                county_path = _county.a["href"]
                break

        if not county_path:
            return None

        county_page = requests.get(base_url + county_path)
        return BeautifulSoup(county_page.text, "lxml")

    def _find_state_page(state_locations):
        lookup_text_start = "Show results for "
        lookup_text_end = " as a whole"
        state_path = ""
        for a in state_locations.find_all("a"):
            atext = a.text.strip()
            if atext.startswith(lookup_text_start) and atext.endswith(lookup_text_end):
                state_path = a["href"]
                break

        if not state_path:
            return None

        state_page = requests.get(base_url + state_path)
        return BeautifulSoup(state_page.text, "lxml")

    def _parse_wages(page):
        if not page:
            return None

        result = {}

        # Find the place's name.
        first_div = page.find("div", {"class": "container"})
        header_text = first_div.find("h1").text
        name = header_text[len("Living Wage Calculation for ") :]
        if "," in name:
            name = name[: name.rfind(",")]
        result["name"] = name

        # Find the wages.
        table = page.find_all("table", {"class": "expense_table"})[0]
        result_row = table.find_all("tr", {"class": "results"})[0]
        wages = [r.text.strip() for r in result_row if r.text.strip().startswith("$")]

        adults = ["1A1W", "2A1W", "2W2W"]
        children = ["0C", "1C", "2C", "3C"]
        result["wages"] = {}
        for (a, c), wage in zip(itertools.product(adults, children), wages):
            key = f"{a}{c}"
            result["wages"][key] = wage

        return result

    state_locations = _find_state_locations()
    metro_page = _find_metro_page(state_locations)
    county_page = _find_county_page(state_locations)
    state_page = _find_state_page(state_locations)
    return {
        "metro": _parse_wages(metro_page),
        "county": _parse_wages(county_page),
        "state": _parse_wages(state_page),
    }


if __name__ == "__main__":
    tests = [
        ("FL", "Miami", "Miami-Dade"),
        ("CA", "Irvine", "Orange"),
        ("NC", "Chapel Hill", "Orange"),
        ("NC", "Raleigh", "Wake"),
        ("NJ", "Princeton", "Mercer"),
    ]

    for t_state, t_city, t_county in tests:
        print(f"Results for {t_city=}")
        res = get_wages(t_state, t_city, t_county)
        for k, v in res.items():
            if not v:
                print(f"\t{k} - N/A")
                continue

            print(f"\t{k} - {v['name']}")

            for fam_size, wage in v["wages"].items():
                print(f"\t\t{fam_size} - {wage}")
        break
