import requests

url = "https://irctc1.p.rapidapi.com/api/v1/searchTrain"

querystring = {"query":"190"}

headers = {
	"x-rapidapi-key": "999a4e361fmshed1d5d600aa108fp128b75jsn63b07c808776",
	"x-rapidapi-host": "irctc1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())


url = "https://irctc1.p.rapidapi.com/api/v1/searchStation"

querystring = {"query":"BJU"}

headers = {
	"x-rapidapi-key": "999a4e361fmshed1d5d600aa108fp128b75jsn63b07c808776",
	"x-rapidapi-host": "irctc1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())


url = "https://irctc1.p.rapidapi.com/api/v3/trainBetweenStations"

querystring = {"fromStationCode":"BVI","toStationCode":"NDLS","dateOfJourney":"2025-02-24"}

headers = {
	"x-rapidapi-key": "999a4e361fmshed1d5d600aa108fp128b75jsn63b07c808776",
	"x-rapidapi-host": "irctc1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())


url = "https://irctc1.p.rapidapi.com/api/v1/liveTrainStatus"

querystring = {"trainNo":"19038","startDay":"1"}

headers = {
	"x-rapidapi-key": "999a4e361fmshed1d5d600aa108fp128b75jsn63b07c808776",
	"x-rapidapi-host": "irctc1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())


url = "https://irctc1.p.rapidapi.com/api/v1/getTrainSchedule"

querystring = {"trainNo":"12936"}

headers = {
	"x-rapidapi-key": "999a4e361fmshed1d5d600aa108fp128b75jsn63b07c808776",
	"x-rapidapi-host": "irctc1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())


url = "https://irctc1.p.rapidapi.com/api/v3/getPNRStatus"

querystring = {"pnrNumber":"45879365123"}

headers = {
	"x-rapidapi-key": "999a4e361fmshed1d5d600aa108fp128b75jsn63b07c808776",
	"x-rapidapi-host": "irctc1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())


url = "https://irctc1.p.rapidapi.com/api/v1/checkSeatAvailability"

querystring = {"classType":"2A","fromStationCode":"ST","quota":"GN","toStationCode":"BVI","trainNo":"19038","date":"2025-02-21"}

headers = {
	"x-rapidapi-key": "999a4e361fmshed1d5d600aa108fp128b75jsn63b07c808776",
	"x-rapidapi-host": "irctc1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())


url = "https://irctc1.p.rapidapi.com/api/v1/getTrainClasses"

querystring = {"trainNo":"19038"}

headers = {
	"x-rapidapi-key": "999a4e361fmshed1d5d600aa108fp128b75jsn63b07c808776",
	"x-rapidapi-host": "irctc1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())


url = "https://irctc1.p.rapidapi.com/api/v2/getFare"

querystring = {"trainNo":"19038","fromStationCode":"ST","toStationCode":"BVI"}

headers = {
	"x-rapidapi-key": "999a4e361fmshed1d5d600aa108fp128b75jsn63b07c808776",
	"x-rapidapi-host": "irctc1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
