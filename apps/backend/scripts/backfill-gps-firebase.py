#!/usr/bin/env python3
"""
Backfill GPS coordinates from photo_catalog.db to Firebase Firestore.

This script:
1. Reads all photos with GPS from photo_catalog.db (argentina-2025 trip)
2. Matches them to existing Firebase photos by originalFilename or caption
3. Updates Firebase documents with lat/lng coordinates

Usage:
  python scripts/backfill-gps-firebase.py [--dry-run] [--trip argentina-2025]

Requirements:
  pip install firebase-admin
"""

import sqlite3
import argparse
import json
import sys
import os
from pathlib import Path

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False
    print("Warning: firebase-admin not installed. Run: pip install firebase-admin")

# Path to photo_catalog.db
DB_PATH = Path(__file__).parent.parent / "legacy" / "photo_catalog.db"


def load_photos_from_db(trip_name: str = "argentina-2025") -> dict:
    """Load photos with GPS from SQLite database, keyed by filename."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT filename, latitude, longitude, location_name, location_address,
               file_path, date_taken, city
        FROM photos
        WHERE trip_name = ?
          AND latitude IS NOT NULL
          AND longitude IS NOT NULL
    """, (trip_name,))

    photos = {}
    for row in cur.fetchall():
        # Key by filename (strip path)
        filename = row['filename']
        photos[filename] = {
            'lat': row['latitude'],
            'lng': row['longitude'],
            'location_name': row['location_name'],
            'location_address': row['location_address'],
            'file_path': row['file_path'],
            'date_taken': row['date_taken'],
            'city': row['city']
        }

    conn.close()
    return photos


def backfill_firestore(db_photos: dict, dry_run: bool = True, limit: int = 100):
    """Update Firebase Firestore photos with GPS coordinates."""
    if not HAS_FIREBASE:
        print("ERROR: firebase-admin SDK not available")
        return

    # Initialize Firebase Admin
    cred_path = Path(__file__).parent.parent / "src" / "imports" / "viajefamiliar30dias" / "serviceAccountKey.json"
    if not cred_path.exists():
        print(f"ERROR: Firebase service account key not found at {cred_path}")
        print("Download from: https://console.firebase.google.com → Project Settings → Service Accounts")
        return

    cred = credentials.Certificate(str(cred_path))
    firebase_admin.initialize_app(cred)
    firestore_db = firestore.client()

    # Get all photos from Firestore
    photos_ref = firestore_db.collection('photos')
    docs = list(photos_ref.limit(limit).stream())

    updated = 0
    matched = 0
    not_found = 0

    for doc in docs:
        data = doc.to_dict()
        original_filename = data.get('originalFilename') or data.get('caption') or ''

        # Try to match by filename
        db_photo = None
        for db_filename, db_data in db_photos.items():
            if db_filename in original_filename or original_filename in db_filename:
                db_photo = db_data
                break

        if db_photo:
            matched += 1
            # Check if GPS already exists
            existing_lat = data.get('lat')
            existing_lng = data.get('lng')

            if existing_lat and existing_lng:
                print(f"  SKIP {original_filename}: already has GPS ({existing_lat}, {existing_lng})")
                continue

            # Update the document
            update_data = {
                'lat': db_photo['lat'],
                'lng': db_photo['lng']
            }

            if dry_run:
                print(f"  [DRY RUN] Would update {original_filename}: lat={db_photo['lat']}, lng={db_photo['lng']}")
            else:
                doc.reference.update(update_data)
                print(f"  UPDATED {original_filename}: lat={db_photo['lat']}, lng={db_photo['lng']}")

            updated += 1
        else:
            not_found += 1

    print(f"\nSummary:")
    print(f"  Matched: {matched}")
    print(f"  Updated: {updated}")
    print(f"  Not found in DB: {not_found}")
    print(f"  Total DB photos with GPS: {len(db_photos)}")


def main():
    parser = argparse.ArgumentParser(description="Backfill GPS from photo_catalog.db to Firebase")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    parser.add_argument("--trip", default="argentina-2025", help="Trip name to process (default: argentina-2025)")
    parser.add_argument("--limit", type=int, default=100, help="Max Firestore docs to process (default: 100)")
    args = parser.parse_args()

    print(f"Loading photos from {DB_PATH} for trip '{args.trip}'...")
    db_photos = load_photos_from_db(args.trip)
    print(f"Found {len(db_photos)} photos with GPS in database")

    if not db_photos:
        print("No photos with GPS found. Exiting.")
        return

    # Show sample
    sample = list(db_photos.items())[:3]
    print("\nSample photos:")
    for filename, data in sample:
        print(f"  {filename}: ({data['lat']}, {data['lng']}) - {data['location_name'] or 'no name'}")

    print(f"\nProcessing Firebase photos (limit: {args.limit})...")
    backfill_firestore(db_photos, dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
