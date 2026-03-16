import database as db
from werkzeug.security import generate_password_hash

hashed = generate_password_hash("password")
sql = "INSERT INTO user (fullname, email, role, password) VALUES (?, ?, ?, ?)"
values = ('Super Admin', 'admin@komodohub.com', 'system-admin', hashed)

#Check if this Admin already exists
sql_select = 'SELECT user_id FROM user WHERE fullname = ? AND email = ? AND role = ?'
existing = db.fetch_one(sql_select, (values[0],values[1], values[2]))
if not existing:
    db.execute_query(sql, values)
    print('System admin created successfully')
else: 
    print('System admin by this name already exists, skipping')
    
species_data = [
    ('Javan Rhinoceros', 'Rhinoceros sondaicus', 'CR', 'Herbivore', 'Ujung Kulon', 'Less than 80 individuals remain in Ujung Kulon National Park.', 'Can weigh up to 2,300 kg and live 30-45 years.', 'species/rhi.jpg','https://www.worldwildlife.org/species/rhino/javan-rhino'),
    ('Sumatran Tiger', 'Panthera tigris sumatrae', 'CR', 'Carnivore', 'Sumatra', 'Fewer than 400 remain, threatened by habitat loss and poaching.', 'Smallest tiger subspecies and excellent swimmers.', 'species/tiger2.jpg','https://www.fauna-flora.org/species/sumatran-tiger'),
    ('Bali Myna', 'Leucopsar rothschildi', 'CR', 'Omnivore', 'Bali', 'Bali only endemic bird, with fewer than 100 in the wild.', 'Only endemic bird with striking blue eye patches.', 'species/Bali-Myna.jpg','https://www.mandai.com/en/bird-paradise/animals-and-zones/songs-of-the-forest/bali-myna.html'),
    ('Komodo Dragon', 'Varanus komodoensis', 'VU', 'Carnivore', 'Komodo Island', 'World largest living lizard, found only in Indonesian islands.', 'Can grow up to 3 meters long.', 'species/Komodo.jpg','https://www.londonzoo.org/whats-here/animals/komodo-dragon'),
    ('Javan Hawk-Eagle', 'Nisaetus bartelsi', 'EN', 'Carnivore', 'Java', 'Only 250-400 pairs remaining.', 'Featured on Indonesia coat of arms.', 'species/hawk.jpg','https://datazone.birdlife.org/species/factsheet/javan-hawk-eagle-nisaetus-bartelsi'),
    ('Celebes Crested Macaque', 'Macaca nigra', 'CR', 'Omnivore', 'Sulawesi', 'Population declined 90% in 40 years.', 'Famous for taking the world first monkey selfie in 2011.', 'species/Celebes-Crested.jpg','https://animalia.bio/celebes-crested-macaque?endemic=7'),
    ('Sumatran Orangutan', 'Pongo abelii', 'CR', 'Herbivore', 'Sumatra', 'Fewer than 14,000 remain due to deforestation.', 'Share 97% of DNA with humans.', 'species/Orangutan.jpg','https://www.chesterzoo.org/animals/sumatran-orangutan'),
    ('Sumatran Elephant', 'Elephas maximus sumatranus', 'CR', 'Herbivore', 'Sumatra', 'Only 2,000-2,500 individuals left.', 'Can weigh up to 5 tons and live 60-70 years.', 'species/elep.jpg','https://www.worldwildlife.org/species/elephant/asian-elephant/sumatran-elephant/')
]
sql = 'INSERT INTO species (common_name, scientific_name, status, diet, location, description, fun_fact, image, full_details_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)'

for species in species_data:
    existing = db.fetch_one('SELECT species_id FROM species WHERE common_name = ?', (species[0],))
    if not existing:
        db.execute_query(sql, species)
        print(f'{species[0]} inserted successfully')
    else:
        print(f'{species[0]} already exists, skipping')