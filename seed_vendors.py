from app.database.session import SessionLocal
from app.models.commerce import Vendor, MenuItem

db = SessionLocal()

vendors_data = [
    {
        "name": "Mama Titi Kitchen",
        "location": "Lagos Island",
        "description": "Authentic Nigerian home cooking - Egusi, Jollof, Amala",
        "contact_phone": "2348011111111",
        "rating": 4.8,
        "menu": [
            {"name": "Jollof Rice + Chicken", "price": 2500, "description": "Party jollof with grilled chicken"},
            {"name": "Egusi Soup + Pounded Yam", "price": 3000, "description": "Fresh egusi with assorted meat"},
            {"name": "Amala + Ewedu", "price": 2000, "description": "Smooth amala with ewedu and gbegiri"},
            {"name": "Fried Rice + Turkey", "price": 2800, "description": "Nigerian style fried rice"},
        ]
    },
    {
        "name": "Sunset Grill & Bar",
        "location": "Victoria Island",
        "description": "Premium grills, burgers and cold drinks",
        "contact_phone": "2348022222222",
        "rating": 4.5,
        "menu": [
            {"name": "Suya Platter", "price": 3500, "description": "Spiced beef suya with onions and tomatoes"},
            {"name": "Chicken Burger", "price": 2200, "description": "Crispy chicken fillet burger with fries"},
            {"name": "Beef Kebab", "price": 2800, "description": "6 skewers of marinated beef"},
            {"name": "Grilled Fish", "price": 4000, "description": "Whole grilled tilapia with pepper sauce"},
        ]
    },
    {
        "name": "Abuja Bites",
        "location": "Abuja",
        "description": "Fast food and local dishes in the heart of Abuja",
        "contact_phone": "2348033333333",
        "rating": 4.2,
        "menu": [
            {"name": "Shawarma", "price": 1800, "description": "Chicken or beef shawarma wrap"},
            {"name": "Pepper Soup", "price": 2500, "description": "Spicy assorted meat pepper soup"},
            {"name": "Puff Puff x6", "price": 500, "description": "Fresh hot puff puff"},
            {"name": "Meat Pie", "price": 600, "description": "Nigerian style meat pie"},
        ]
    },
    {
        "name": "Spice Garden",
        "location": "Lekki",
        "description": "Indian and continental cuisine with a Nigerian twist",
        "contact_phone": "2348044444444",
        "rating": 4.6,
        "menu": [
            {"name": "Chicken Biryani", "price": 3200, "description": "Fragrant basmati rice with spiced chicken"},
            {"name": "Butter Chicken", "price": 3500, "description": "Creamy tomato curry with naan"},
            {"name": "Vegetable Fried Rice", "price": 2000, "description": "Wok fried rice with fresh vegetables"},
            {"name": "Samosa x4", "price": 1200, "description": "Crispy pastry with spiced filling"},
        ]
    },
    {
        "name": "Eko Pizza House",
        "location": "Lagos Island",
        "description": "Best pizza and pasta in Lagos at pocket-friendly prices",
        "contact_phone": "2348055555555",
        "rating": 4.3,
        "menu": [
            {"name": "Pepperoni Pizza Large", "price": 4500, "description": "12 inch pepperoni pizza"},
            {"name": "Margherita Pizza Medium", "price": 3000, "description": "Classic tomato and mozzarella"},
            {"name": "Chicken Pasta", "price": 2800, "description": "Creamy penne pasta with grilled chicken"},
            {"name": "Garlic Bread", "price": 800, "description": "Toasted garlic bread with herbs"},
        ]
    },
    {
        "name": "Naija Street Food",
        "location": "Surulere",
        "description": "Affordable street food classics done right",
        "contact_phone": "2348066666666",
        "rating": 4.7,
        "menu": [
            {"name": "Boli + Fish", "price": 1200, "description": "Roasted plantain with grilled fish"},
            {"name": "Akara + Pap", "price": 800, "description": "Crispy bean cakes with smooth pap"},
            {"name": "Noodles + Egg", "price": 900, "description": "Indomie with fried egg and vegetables"},
            {"name": "Beans + Plantain", "price": 1000, "description": "Steamed beans with fried plantain"},
        ]
    },
    {
        "name": "Kano Royal Kitchen",
        "location": "Kano",
        "description": "Northern Nigerian delicacies - Tuwo, Kilishi and more",
        "contact_phone": "2348077777777",
        "rating": 4.9,
        "menu": [
            {"name": "Tuwo Shinkafa + Miyan Kuka", "price": 1800, "description": "Rice pudding with baobab leaf soup"},
            {"name": "Kilishi 100g", "price": 2000, "description": "Dry spiced beef jerky"},
            {"name": "Fura da Nono", "price": 700, "description": "Millet balls with fresh yogurt"},
            {"name": "Dan Wake", "price": 1000, "description": "Bean dumplings with groundnut oil"},
        ]
    },
]

for vd in vendors_data:
    vendor = Vendor(
        name=vd["name"],
        location=vd["location"],
        description=vd["description"],
        contact_phone=vd["contact_phone"],
        rating=vd["rating"],
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    for md in vd["menu"]:
        item = MenuItem(
            vendor_id=str(vendor.id),
            name=md["name"],
            price=md["price"],
            description=md["description"],
        )
        db.add(item)
    db.commit()
    print(f"Added: {vendor.name} ({len(vd['menu'])} menu items)")

db.close()
print("\nDone! 7 vendors seeded successfully.")
