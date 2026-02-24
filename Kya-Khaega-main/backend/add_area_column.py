# import pandas as pd
# import re

# # Hashmap of major Pune areas (add/remove as needed)
# AREA_MAP = {
#     "hinjawadi": "Hinjawadi",
#     "baner": "Baner",
#     "kothrud": "Kothrud",
#     "wakad": "Wakad",
#     "viman-nagar": "Viman Nagar",
#     "koregaon-park": "Koregaon Park",
#     "hadapsar": "Hadapsar",
#     "aundh": "Aundh",
#     "magarpatta": "Magarpatta",
#     "pimple-saudagar": "Pimple Saudagar",
#     "fc-road": "FC Road",
#     "camp": "Camp",
#     "swargate": "Swargate",
#     "deccan": "Deccan",
#     "pimpri": "Pimpri",
#     "chinchwad": "Chinchwad",
#     "bavdhan": "Bavdhan",
#     "dhankawadi": "Dhankawadi",
#     "karve-nagar": "Karve Nagar",
#     "shivaji-nagar": "Shivaji Nagar",
#     "bhugaon": "Bhugaon",
#     "senapati-bapat-road": "Senapati Bapat Road",
#     "yerwada": "Yerawada",
#     "kalyani-nagar": "Kalyani Nagar",
#     "pashan": "Pashan",
#     "bund-garden":"Bund Garden",
#     "sus":"Susgaon",
#     "erandwane":"Erandwane",
#     "mg-road":"MG Road",
#     "mundhwa":"Mundhwa",
#     "pune-university":"Pune University",
#     "jm-road":"JM Road",
#     "sadashiv-peth": "Sadashiv Peth",
#     "kharadi": "Kharadi",
#     "ravet": "Ravet",
#     "yerawada": "Yerawada",
#     "nigdi": "Nigdi",
#     "katraj": "Katraj",
#     "bibvewadi": "Bibvewadi",
#     "bibewadi":"Bibewadi",
#     "bavdhan":"Bavdhan",
#     "wadgaon-sheri":"Wadgaon Sheri",
#     "wadgaon": "Wadgaon",
#     "kondhwa":"Kondhwa",
#     "lohegaon":"Lohegaon",
#     "dhanori":"Dhanori",
#     "pimple-saudagar":"Pimple Saudagar",
#     "pimple-nilakh":"Pimple Nilakh",
#     "shukrawar-peth":"Shukrawar Peth",
#     "narhe":"Narhe",
#     "dehu-road":"Dehu Road",
#     "nibm-road":"NIBM Road",
#     "balewadi":"Balewadi",
#     "sinhgad-road":"Sinhgad Road",
#     "model-colony":"Model Colony",
#     "saluknhe-vihar-road":"Salunkhe Vihar",
#     "lonavala":"Lonavala",
#     "fatima-nagar":"Fatima Nagar",
#     "vishrantwadi":"Vishrantwadi",
#     "satara-road":"Satara Road",
#     "dhole-patil-road":"Dhole Patil Road",
#     "akurdi":"Akurdi",
#     "tilak-road":"Tilak Road",
#     "shivapur":"Shivapur",
#     "east-street":"East Street",
#     "law-college-road": "Law College Road",
#     "chandan-nagar":"Chandan Nagar",
#     "wanowrie":"Wanowrie",
#     "dange-chowk":"Dange Chowk",
#     "warje":"Warje",
#     "khadki":"Khadki",
#     "rasta-peth":"Rasta Peth",
#     "salunkhe-vihar-road": "Salunkhe Vihar Road",
#     "old-mumbai-pune-highway":"Old Mumbai Pune Highway",
#     "parvati":"Parvati",
#     "bhosari":"Bhosari",
#     "wagholi":"Wagholi",
#     "ghorpadi":"Ghorpadi",
#     "talawade":"Talawade",
#     "pimple-gurav":"Pimple Gurav",
#     "budhwar-peth":"Budhwar Peth",
#     "kanji-mahalunge":"Kanji Mahalunge"
# }

# def get_area(url):
#     for key in AREA_MAP:
#         if key in url:
#             return AREA_MAP[key]
#     return "Other"

# df = pd.read_csv("d:/KyaKhaega/backend/Zomato_Menu_Classified.csv")
# df['Area'] = df['URL'].apply(get_area)
# df.to_csv("d:/KyaKhaega/backend/Zomato_Menu_Classified_with_Area.csv", index=False)


import pandas as pd
import re

df = pd.read_csv("d:/KyaKhaega/backend/Zomato_Menu_Classified_with_Area.csv")

# Create a hashmap for new areas found in URLs where Area is 'Other'
new_area_map = {}

for url in df.loc[df['Area'] == 'Other', 'URL']:
    # Extract possible area from the URL (between / and /)
    match = re.findall(r'zomato\.com/pune/([^/]+)/', url)
    if match:
        area_key = match[0]
        # Add to hashmap if not already present
        if area_key not in new_area_map:
            new_area_map[area_key] = area_key.title().replace("-", " ")

print("New areas found in URLs with Area as 'Other':")
print(new_area_map)

