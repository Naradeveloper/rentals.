import json
from app import app, db, Property, User
from datetime import datetime

def create_sample_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@homerent.co.ke',
            password='hashed_password_here',  # Hash this in production
            phone='+254700000000',
            is_admin=True
        )
        db.session.add(admin)
        
        # Sample properties data
        sample_properties = [
            {
                "title": "Modern Bedsitter in Kilimani",
                "description": "Spacious bedsitter with modern finishes, fitted kitchen, and ensuite bathroom. Located in secure compound with 24/7 security.",
                "property_type": "bedsitter",
                "price": 15000,
                "deposit": 30000,
                "size": "300 sq ft",
                "location": "Kilimani, Nairobi",
                "latitude": -1.286389,
                "longitude": 36.817223,
                "address": "Mukoma Road, Kilimani",
                "bedrooms": 0,
                "bathrooms": 1,
                "amenities": json.dumps(["24/7 Security", "Water Backup", "Parking", "WiFi", "Gym Access"]),
                "video_url": "https://example.com/video1.mp4",
                "images": json.dumps([
                    "/static/images/property1-1.jpg",
                    "/static/images/property1-2.jpg",
                    "/static/images/property1-3.jpg"
                ]),
                "owner_id": 1
            },
            {
                "title": "Luxury One Bedroom Apartment",
                "description": "Beautiful one bedroom apartment with balcony, fitted wardrobes, and modern kitchen. Comes with access to swimming pool and gym.",
                "property_type": "one_bedroom",
                "price": 35000,
                "deposit": 70000,
                "size": "600 sq ft",
                "location": "Westlands, Nairobi",
                "latitude": -1.2689,
                "longitude": 36.8028,
                "address": "Woodvale Grove, Westlands",
                "bedrooms": 1,
                "bathrooms": 1,
                "amenities": json.dumps(["Swimming Pool", "Gym", "24/7 Security", "Parking", "Backup Generator", "Water Backup"]),
                "video_url": "https://example.com/video2.mp4",
                "images": json.dumps([
                    "/static/images/property2-1.jpg",
                    "/static/images/property2-2.jpg",
                    "/static/images/property2-3.jpg"
                ]),
                "owner_id": 1
            },
            {
                "title": "Affordable Single Room",
                "description": "Clean single room with shared kitchen and bathroom. Perfect for students or young professionals.",
                "property_type": "single_room",
                "price": 8000,
                "deposit": 16000,
                "size": "150 sq ft",
                "location": "Buruburu, Nairobi",
                "latitude": -1.2822,
                "longitude": 36.8758,
                "address": "Phase 5, Buruburu",
                "bedrooms": 0,
                "bathrooms": 0,
                "amenities": json.dumps(["Shared Kitchen", "Shared Bathroom", "24/7 Security", "Water Available"]),
                "video_url": None,
                "images": json.dumps(["/static/images/property3-1.jpg"]),
                "owner_id": 1
            },
            {
                "title": "Spacious Two Bedroom Apartment",
                "description": "Modern two bedroom apartment with master ensuite, fitted kitchen, and spacious living area. Located in gated community.",
                "property_type": "two_bedroom",
                "price": 55000,
                "deposit": 110000,
                "size": "900 sq ft",
                "location": "Kileleshwa, Nairobi",
                "latitude": -1.2800,
                "longitude": 36.7800,
                "address": "James Gichuru Road, Kileleshwa",
                "bedrooms": 2,
                "bathrooms": 2,
                "amenities": json.dumps(["Gated Community", "Parking", "24/7 Security", "Backup Generator", "Water Backup", "Children's Playground"]),
                "video_url": "https://example.com/video4.mp4",
                "images": json.dumps([
                    "/static/images/property4-1.jpg",
                    "/static/images/property4-2.jpg",
                    "/static/images/property4-3.jpg"
                ]),
                "owner_id": 1
            },
            {
                "title": "Cozy Bedsitter Near CBD",
                "description": "Well-maintained bedsitter with own kitchenette and bathroom. Close to public transport and shopping centers.",
                "property_type": "bedsitter",
                "price": 12000,
                "deposit": 24000,
                "size": "250 sq ft",
                "location": "Ngara, Nairobi",
                "latitude": -1.2700,
                "longitude": 36.8200,
                "address": "Murang'a Road, Ngara",
                "bedrooms": 0,
                "bathrooms": 1,
                "amenities": json.dumps(["Near CBD", "Public Transport", "Security", "Water Available"]),
                "video_url": None,
                "images": json.dumps(["/static/images/property5-1.jpg"]),
                "owner_id": 1
            },
            {
                "title": "Executive One Bedroom",
                "description": "Executive one bedroom with premium finishes, walk-in closet, and modern appliances. Comes with dedicated parking.",
                "property_type": "one_bedroom",
                "price": 45000,
                "deposit": 90000,
                "size": "700 sq ft",
                "location": "Lavington, Nairobi",
                "latitude": -1.2600,
                "longitude": 36.7900,
                "address": "Lavington Green, Lavington",
                "bedrooms": 1,
                "bathrooms": 1,
                "amenities": json.dumps(["Dedicated Parking", "24/7 Security", "Backup Generator", "Water Backup", "Gym Access", "Swimming Pool"]),
                "video_url": "https://example.com/video6.mp4",
                "images": json.dumps([
                    "/static/images/property6-1.jpg",
                    "/static/images/property6-2.jpg"
                ]),
                "owner_id": 1
            }
        ]
        
        # Add sample properties
        for prop_data in sample_properties:
            property = Property(**prop_data)
            db.session.add(property)
        
        db.session.commit()
        print("Sample data created successfully!")

if __name__ == '__main__':
    create_sample_data()